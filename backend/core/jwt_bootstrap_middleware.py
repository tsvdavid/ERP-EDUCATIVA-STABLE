from django.utils.deprecation import MiddlewareMixin
from rest_framework_simplejwt.tokens import AccessToken


class JwtBootstrapMiddleware(MiddlewareMixin):
    """Decode SimpleJWT token early and expose tenant information.

    This middleware runs **before** ``TenantMiddleware`` and does **not** hit the
    database. It extracts ``user_id`` and optional ``institution`` claim from the
    JWT (if present) and stores them on the request for later use.
    """

    # Prefixes for auth‑only endpoints – they are bypassed by TenantMiddleware
    AUTH_PREFIXES = ("/api/token/", "/api/auth/")

    def process_request(self, request):
        # Bypass for login/refresh endpoints – no tenant needed yet
        if request.path.startswith(self.AUTH_PREFIXES):
            return None

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token_str = auth_header.split(" ", 1)[1]
        try:
            token = AccessToken(token_str)  # validates signature & expiration
        except Exception as e:
            # capture decoding error for debugging / monitoring
            request.jwt_bootstrap_error = str(e)
            return None

        # Expose raw payload for debugging if needed
        request.jwt_payload = token.payload
        request.user_id = token.get("user_id")
        # ``institution`` / ``institution_id`` claims are optional, but should be present for multi-tenant requests.
        request.institution_id = token.get("institution_id") or token.get("institution")
        return None
