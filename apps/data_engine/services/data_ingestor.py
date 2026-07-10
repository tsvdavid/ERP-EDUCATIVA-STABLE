# apps/data_engine/services/data_ingestor.py
"""Data ingestion service for MAC.

The service validates the feature flag, tenant information and retrieves a
connector from the global ``MacRegistry`` to fetch raw data. It returns a
``MacContext`` that can be passed directly to the MAC orchestrator.
"""

from typing import Any

from backend.config.mac_settings import MAC_ENABLED
from apps.data_engine.core.registry import MacRegistry
from apps.data_engine.core.exceptions import ComponentNotFoundError, MacError
from apps.data_engine.components.base import MacContext


class DataIngestor:
    """Service responsible for ingesting raw data via a registered connector.

    The service is deliberately lightweight and has **no** knowledge of any
    concrete connector implementation – it only works with the ``BaseConnector``
    contract provided by the MAC core.
    """

    def ingest(
        self,
        connector: str,
        source: Any,
        tenant_id: str,
        run_id: str,
        user_id: str,
    ) -> MacContext:
        """Execute the ingestion pipeline.

        Steps:
        1. Verify that ``MAC_ENABLED`` is ``True``; otherwise raise ``MacError``.
        2. Validate that ``tenant_id`` is a non‑empty string.
        3. Retrieve the connector instance from the global ``MacRegistry``.
        4. Build the initial ``MacContext`` and invoke ``connector.execute``.
        5. Merge the connector result back into the context and return it.
        """
        if not MAC_ENABLED:
            raise MacError("MAC está desactivado")

        if not tenant_id:
            raise MacError("tenant_id es obligatorio")

        registry = MacRegistry.global_registry()
        try:
            connector_instance = registry.get(connector)
        except ComponentNotFoundError as exc:
            raise ComponentNotFoundError(
                f"Connector '{connector}' no registrado"
            ) from exc

        # Context starts with mandatory multi‑tenant fields and empty payload.
        context: MacContext = {
            "tenant_id": tenant_id,
            "run_id": run_id,
            "user_id": user_id,
            "payload": {},
            "metadata": {},
        }

        # The connector may use ``source`` via the context if needed.
        # We expose it through ``metadata`` so that connectors can read it.
        context["metadata"]["source"] = source

        result = connector_instance.execute(context)
        if isinstance(result, dict):
            # Merge result dict into the existing context (same behaviour as
            # ``MacOrchestrator``).
            context.update(result)
        else:
            # If the connector returns a non‑dict we replace the whole context.
            context = result  # type: ignore[assignment]
        return context
