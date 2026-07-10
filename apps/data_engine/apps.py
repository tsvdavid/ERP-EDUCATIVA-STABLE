from django.apps import AppConfig

class DataEngineConfig(AppConfig):
    """AppConfig for the Motor Análisis y Carga (MAC) module.

    No runtime logic is executed here; the class only registers the
    application when the feature flag ``MAC_ENABLED`` is set to ``True``.
    """

    name = "apps.data_engine"
    verbose_name = "Motor Análisis y Carga"

    def ready(self):
        # Intentionally left blank – the MAC module does not perform any
        # start‑up actions until a later development phase.
        pass
