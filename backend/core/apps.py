from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        import core.signals
        
        # Auditoría de Arquitectura: Verificar que todos los modelos hereden de TenantModel
        from django.core.checks import register, Warning as DjangoWarning, Error
        from core.models import TenantModel

        @register()
        def check_tenant_models(app_configs, **kwargs):
            warnings = []
            target_apps = [
                'academic', 'treasury', 'helpdesk', 'procedures', 
                'health', 'learning', 'accounting', 'purchases', 
                'payments', 'communication', 'privacy', 'ai'
            ]
            
            from django.apps import apps
            for app_label in target_apps:
                try:
                    app_config = apps.get_app_config(app_label)
                    for model in app_config.get_models():
                        # Excepciones que no necesitan aislamiento directo o son core
                        if model.__name__ in ['Institution', 'ActionLog']:
                            continue
                            
                        if not issubclass(model, TenantModel):
                            warnings.append(
                                DjangoWarning(
                                    f"El modelo {model.__name__} en {app_label} no hereda de TenantModel.",
                                    hint="Todos los modelos específicos de institución deben heredar de core.models.TenantModel para garantizar aislamiento.",
                                    obj=model,
                                    id=f'core.W00{len(warnings)+1}',
                                )
                            )
                except LookupError:
                    continue
            return warnings
