# apps/data_engine/pipeline/builder.py
"""PipelineBuilder implementing declarative pipeline construction."""

from typing import Any, Dict, List, Optional

from apps.data_engine.connectors.contracts import ConnectorConfig
from apps.data_engine.connectors.factory import ConnectorFactory
from apps.data_engine.connectors.registry import ConnectorRegistry
from apps.data_engine.templates.builder import TemplatePipelineBuilder
from apps.data_engine.templates.registry import TemplateRegistry
from apps.data_engine.transformations.base import BaseTransformation
from apps.data_engine.transformations.pipeline import TransformationPipeline
from apps.data_engine.transformations.registry import TransformationRegistry
from apps.data_engine.quality.engine import QualityEngine
from apps.data_engine.quality.registry import QualityRuleRegistry
from apps.data_engine.rules.engine import BusinessRulesEngine
from apps.data_engine.rules.registry import BusinessRuleRegistry
from apps.data_engine.sessions.orchestrator import ImportWorkflowOrchestrator

from apps.data_engine.pipeline.exceptions import PipelineBuildError
from apps.data_engine.pipeline.models import PipelineDefinition
from apps.data_engine.pipeline.runtime import PipelineRuntime


class PipelineBuilder:
    """Orchestrates automatic construction of a PipelineRuntime from a PipelineDefinition."""

    def build(self, definition: PipelineDefinition) -> PipelineRuntime:
        """Build and link all MAC components specified in the PipelineDefinition.

        Parameters
        ----------
        definition : PipelineDefinition
            The declarative pipeline definition containing component configurations.

        Returns
        -------
        PipelineRuntime
            An executable runtime container containing all built components.

        Raises
        ------
        PipelineBuildError
            If any specified component cannot be resolved or instantiated.
        """
        if not isinstance(definition, PipelineDefinition):
            raise TypeError("definition must be an instance of PipelineDefinition.")

        # 1. Build Connector
        try:
            conn_dict = definition.connector
            conn_type = conn_dict["connector_type"]
            conn_params = conn_dict.get("parameters") or {}
            # Keep host/port/username/password at config root, rest in parameters
            config = ConnectorConfig(
                connector_type=conn_type,
                host=conn_params.get("host"),
                port=conn_params.get("port"),
                username=conn_params.get("username"),
                password=conn_params.get("password"),
                parameters=conn_params,
            )
            connector = ConnectorFactory.create_connector(config)
        except Exception as exc:
            raise PipelineBuildError(f"Failed to build connector: {exc}") from exc

        # 2. Resolve Template (Optional)
        template = None
        if definition.template:
            try:
                template = TemplateRegistry.global_registry().get(definition.template)
            except Exception as exc:
                raise PipelineBuildError(f"Failed to resolve template '{definition.template}': {exc}") from exc

        # 3. Build Transformation Pipeline
        try:
            if template:
                # Build baseline pipeline from template configuration
                tx_pipeline = TemplatePipelineBuilder.build_transformation_pipeline(template)
            else:
                tx_pipeline = TransformationPipeline(name=f"pipeline_{definition.pipeline_id}")

            # Append any custom transformation steps defined in pipeline definition
            tx_registry = TransformationRegistry.global_registry()
            for tx_def in definition.transformations:
                tx_type = tx_def["transformation_type"]
                tx_params = tx_def.get("parameters") or {}
                tx_class = tx_registry.get(tx_type)

                if isinstance(tx_class, type) and issubclass(tx_class, BaseTransformation):
                    instance = tx_class(**tx_params)
                elif isinstance(tx_class, BaseTransformation):
                    instance = tx_class
                else:
                    raise PipelineBuildError(f"Resolved transformation '{tx_type}' is not a BaseTransformation class.")
                tx_pipeline.add(instance)
        except Exception as exc:
            raise PipelineBuildError(f"Failed to build transformation pipeline: {exc}") from exc

        # 4. Build Quality Engine & Resolve Quality Rules
        try:
            quality_engine = QualityEngine()
            q_rules = []
            q_registry = QualityRuleRegistry.global_registry()
            for q_def in definition.quality_rules:
                if isinstance(q_def, dict):
                    rule_code = q_def["rule_code"]
                    rule_instance = q_registry.get(rule_code)
                else:
                    rule_instance = q_def
                q_rules.append(rule_instance)
        except Exception as exc:
            raise PipelineBuildError(f"Failed to build quality engine/rules: {exc}") from exc

        # 5. Build Business Rules Engine & Resolve Business Rules
        try:
            business_engine = BusinessRulesEngine()
            b_rules = []
            b_registry = BusinessRuleRegistry.global_registry()
            for b_def in definition.business_rules:
                if isinstance(b_def, dict):
                    rule_code = b_def["rule_code"]
                    rule_instance = b_registry.get(rule_code)
                else:
                    rule_instance = b_def
                b_rules.append(rule_instance)
        except Exception as exc:
            raise PipelineBuildError(f"Failed to build business engine/rules: {exc}") from exc

        # 6. Build Workflow Orchestrator
        try:
            workflow = ImportWorkflowOrchestrator()
        except Exception as exc:
            raise PipelineBuildError(f"Failed to build workflow orchestrator: {exc}") from exc

        # Store resolved rules and configurations in the configuration dict
        configuration = dict(definition.options)
        configuration["quality_rules"] = q_rules
        configuration["business_rules"] = b_rules

        return PipelineRuntime(
            connector=connector,
            template=template,
            transformations=tx_pipeline,
            quality_engine=quality_engine,
            business_engine=business_engine,
            workflow=workflow,
            configuration=configuration,
        )
