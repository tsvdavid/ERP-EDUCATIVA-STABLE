# apps/data_engine/templates/builder.py
"""TemplatePipelineBuilder interpreting declarative templates into executable MAC pipelines."""

from typing import Any, Dict, Optional

from apps.data_engine.connectors import BaseConnector, ConnectorRegistry
from apps.data_engine.connectors import readers as _conn_readers  # noqa: F401
from apps.data_engine.connectors.exceptions import ConnectorException
from apps.data_engine.transformations import (
    BaseTransformation,
    TransformationException,
    TransformationPipeline,
    TransformationRegistry,
)
from .base import BaseImportTemplate
from .exceptions import TemplateBuildException


class TemplatePipelineBuilder:
    """Instantiates and links real MAC components from declarative import templates."""

    @staticmethod
    def build_connector(
        template: BaseImportTemplate,
        source_params: Optional[Dict[str, Any]] = None,
    ) -> BaseConnector:
        """Instantiate a BaseConnector matching the template's connector definition."""
        if not isinstance(template, BaseImportTemplate):
            raise TypeError("template must be an instance of BaseImportTemplate.")

        pipeline_def = template.get_pipeline_definition()
        conn_def = pipeline_def.connector
        conn_type = conn_def.connector_type

        # Merge template default parameters with runtime source parameters
        merged_params = dict(conn_def.parameters)
        if source_params:
            merged_params.update(source_params)

        try:
            reg = ConnectorRegistry.global_registry()
            cls_item = reg.get_connector_class(conn_type)
            if isinstance(cls_item, type) and issubclass(cls_item, BaseConnector):
                from apps.data_engine.connectors.contracts import ConnectorConfig
                cfg = ConnectorConfig(connector_type=conn_type, parameters=merged_params)
                return cls_item(config=cfg)
            raise TemplateBuildException(
                f"Registered item for connector '{conn_type}' is not a BaseConnector class."
            )
        except (ConnectorException, KeyError) as exc:
            raise TemplateBuildException(
                f"Failed to build connector '{conn_type}' for template '{template.code}': {exc}"
            ) from exc

    @staticmethod
    def build_transformation_pipeline(template: BaseImportTemplate) -> TransformationPipeline:
        """Instantiate a sequential TransformationPipeline with all defined validators and processors."""
        if not isinstance(template, BaseImportTemplate):
            raise TypeError("template must be an instance of BaseImportTemplate.")

        pipeline_def = template.get_pipeline_definition()
        pipeline = TransformationPipeline(name=f"pipeline_{template.code}_v{template.version}")
        reg = TransformationRegistry.global_registry()

        # 1. Add standalone validators first (validate raw incoming fields before mutation/rename)
        for val_def in pipeline_def.validators:
            val_type = val_def.validator_type
            params = val_def.parameters
            try:
                item = reg.get(val_type)
                if isinstance(item, type) and issubclass(item, BaseTransformation):
                    instance = item(**params)
                elif isinstance(item, BaseTransformation):
                    instance = item
                else:
                    raise TemplateBuildException(f"Item registered under validator '{val_type}' is not a BaseTransformation.")
                pipeline.add(instance)
            except (TransformationException, KeyError, TypeError) as exc:
                raise TemplateBuildException(
                    f"Failed instantiating validator '{val_type}' in template '{template.code}': {exc}"
                ) from exc

        # 2. Add transformations/processors after validation
        for tx_def in pipeline_def.transformations:
            tx_type = tx_def.transformation_type
            params = tx_def.parameters
            try:
                item = reg.get(tx_type)
                if isinstance(item, type) and issubclass(item, BaseTransformation):
                    instance = item(**params)
                elif isinstance(item, BaseTransformation):
                    # For pre-instantiated components or singletons
                    instance = item
                else:
                    raise TemplateBuildException(f"Item registered under '{tx_type}' is not a BaseTransformation.")
                pipeline.add(instance)
            except (TransformationException, KeyError, TypeError) as exc:
                raise TemplateBuildException(
                    f"Failed instantiating transformation '{tx_type}' in template '{template.code}': {exc}"
                ) from exc

        return pipeline

    @staticmethod
    def validate_execution_readiness(template: BaseImportTemplate) -> bool:
        """Verify that all components specified by the template are registered and structurally valid."""
        errors = template.validate_template()
        if errors:
            return False

        if not template.get_template_definition().columns:
            return False

        pipeline_def = template.get_pipeline_definition()
        conn_type = pipeline_def.connector.connector_type
        if conn_type.lower() not in ConnectorRegistry.global_registry().list_supported_connectors():
            return False

        reg_tx = TransformationRegistry.global_registry()
        supported_txs = [n.lower() for n in reg_tx.list_names()]
        for tx in pipeline_def.transformations:
            if tx.transformation_type.lower() not in supported_txs:
                return False
        for val in pipeline_def.validators:
            if val.validator_type.lower() not in supported_txs:
                return False

        return True
