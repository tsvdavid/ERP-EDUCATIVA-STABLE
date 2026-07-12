# apps/data_engine/transformations/expressions.py
"""Pure Python ExpressionEngine supporting declarative transformation functions.

Evaluates functions like UPPER, LOWER, TRIM, CONCAT, COALESCE, SUBSTRING,
IF, CASE, NOW, UUID, HASH, and REGEX_REPLACE safely without using `eval()`.
"""

import datetime
import hashlib
import re
import uuid
from typing import Any, Dict, List, Optional, Union

from .contracts import TransformationContext
from .exceptions import ExpressionException


class ExpressionEngine:
    """Evaluates declarative transformation functions on record fields and context."""

    @staticmethod
    def _resolve_val(token: Any, record: Dict[str, Any], context: Optional[TransformationContext] = None) -> Any:
        """Resolve a token to its literal value, record field, or context variable."""
        if not isinstance(token, str):
            return token

        token_stripped = token.strip()
        # String literal enclosed in single or double quotes
        if (token_stripped.startswith('"') and token_stripped.endswith('"')) or (
            token_stripped.startswith("'") and token_stripped.endswith("'")
        ):
            return token_stripped[1:-1]

        # Numeric literal check
        try:
            if "." in token_stripped:
                return float(token_stripped)
            return int(token_stripped)
        except ValueError:
            pass

        # Boolean and Null checks
        lower_token = token_stripped.lower()
        if lower_token == "true":
            return True
        if lower_token == "false":
            return False
        if lower_token in ("null", "none"):
            return None

        # Check in record or context variables
        if token_stripped in record:
            return record[token_stripped]
        if context and token_stripped in context.variables:
            return context.variables[token_stripped]

        # Return None if unquoted field identifier is not in record or context
        return None

    @staticmethod
    def evaluate(
        expression: Any,
        record: Dict[str, Any],
        context: Optional[TransformationContext] = None,
    ) -> Any:
        """Evaluate a declarative expression or function against a record dictionary.

        Supported functions:
        - UPPER(arg)
        - LOWER(arg)
        - TRIM(arg)
        - CONCAT(arg1, arg2, ...)
        - COALESCE(arg1, arg2, ...)
        - SUBSTRING(arg, start, length)
        - IF(cond, true_val, false_val)
        - CASE(conditions_dict, default)
        - NOW()
        - UUID()
        - HASH(arg)
        - REGEX_REPLACE(arg, pattern, repl)
        """
        if isinstance(expression, dict):
            # Dict expression representation, e.g., {"func": "CONCAT", "args": ["first", "last"]}
            func = str(expression.get("func", "")).upper()
            args = expression.get("args", [])
            return ExpressionEngine._execute_func(func, args, record, context)

        if not isinstance(expression, str):
            return expression

        expr = expression.strip()
        if not (expr.endswith(")") and "(" in expr):
            return ExpressionEngine._resolve_val(expr, record, context)

        idx = expr.index("(")
        func_name = expr[:idx].strip().upper()
        args_raw = expr[idx + 1 : -1].strip()

        # Split arguments cleanly handling quoted commas and nested structures
        args = ExpressionEngine._split_args(args_raw) if args_raw else []
        return ExpressionEngine._execute_func(func_name, args, record, context)

    @staticmethod
    def _split_args(args_str: str) -> List[str]:
        """Split argument string by commas while respecting quoted substrings and parentheses."""
        args: List[str] = []
        current = []
        in_quote = False
        quote_char = ""
        paren_depth = 0

        for char in args_str:
            if char in ("'", '"'):
                if not in_quote:
                    in_quote = True
                    quote_char = char
                elif quote_char == char:
                    in_quote = False
                current.append(char)
            elif char == "(" and not in_quote:
                paren_depth += 1
                current.append(char)
            elif char == ")" and not in_quote:
                paren_depth -= 1
                current.append(char)
            elif char == "," and not in_quote and paren_depth == 0:
                args.append("".join(current).strip())
                current = []
            else:
                current.append(char)

        if current:
            args.append("".join(current).strip())
        return args

    @staticmethod
    def _execute_func(
        func_name: str,
        args: List[Any],
        record: Dict[str, Any],
        context: Optional[TransformationContext] = None,
    ) -> Any:
        """Execute the identified function with resolved argument parameters."""
        resolved = [ExpressionEngine._resolve_val(arg, record, context) for arg in args]

        try:
            if func_name == "UPPER":
                if not resolved or resolved[0] is None:
                    return ""
                return str(resolved[0]).upper()

            if func_name == "LOWER":
                if not resolved or resolved[0] is None:
                    return ""
                return str(resolved[0]).lower()

            if func_name == "TRIM":
                if not resolved or resolved[0] is None:
                    return ""
                return str(resolved[0]).strip()

            if func_name == "CONCAT":
                return "".join(str(r) for r in resolved if r is not None)

            if func_name == "COALESCE":
                for item in resolved:
                    if item is not None and item != "":
                        return item
                return None

            if func_name == "SUBSTRING":
                if not resolved or resolved[0] is None:
                    return ""
                s = str(resolved[0])
                start = int(resolved[1]) if len(resolved) > 1 and resolved[1] is not None else 0
                length = int(resolved[2]) if len(resolved) > 2 and resolved[2] is not None else len(s)
                return s[start : start + length]

            if func_name == "IF":
                cond = bool(resolved[0]) if resolved else False
                true_val = resolved[1] if len(resolved) > 1 else None
                false_val = resolved[2] if len(resolved) > 2 else None
                return true_val if cond else false_val

            if func_name == "CASE":
                conds = resolved[0] if resolved and isinstance(resolved[0], dict) else {}
                default = resolved[1] if len(resolved) > 1 else None
                # Check each condition key against record
                for k, v in conds.items():
                    if ExpressionEngine._resolve_val(k, record, context):
                        return v
                return default

            if func_name == "NOW":
                return datetime.datetime.now().isoformat()

            if func_name == "UUID":
                return str(uuid.uuid4())

            if func_name == "HASH":
                target = str(resolved[0]).encode("utf-8") if resolved and resolved[0] is not None else b""
                return hashlib.sha256(target).hexdigest()

            if func_name == "REGEX_REPLACE":
                if len(resolved) < 3 or resolved[0] is None:
                    return ""
                s = str(resolved[0])
                pattern = str(resolved[1])
                repl = str(resolved[2])
                return re.sub(pattern, repl, s)

            raise ExpressionException(f"Unsupported expression function: '{func_name}'.")
        except Exception as exc:
            if isinstance(exc, ExpressionException):
                raise
            raise ExpressionException(f"Error evaluating function '{func_name}' with args {args}: {exc}") from exc
