from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models import TenantModel

class AIProviderConfig(TenantModel):
    PROVIDER_CHOICES = [
        ('anthropic', 'Anthropic (Claude)'),
        ('openai', 'OpenAI (GPT)'),
        ('local', 'Local / Custom (Ollama/vLLM)'),
    ]

    institution = models.ForeignKey('users.Institution', on_delete=models.CASCADE, related_name='ai_configs', verbose_name=_("Institución"))
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='anthropic')
    api_key = models.CharField(max_length=255, help_text=_("Clave API para el proveedor seleccionado"))
    model_name = models.CharField(max_length=100, default='claude-3-haiku-20240307', help_text=_("Nombre exacto del modelo (ej: gpt-4o, claude-3-opus)"))
    api_base_url = models.URLField(max_length=255, blank=True, null=True, help_text=_("URL base opcional (usado para Ollama o proxies)"))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Configuración de Proveedor IA")
        verbose_name_plural = _("Configuraciones de Proveedores IA")
        unique_together = ('institution', 'provider')

    def __str__(self):
        return f"{self.institution.name} - {self.get_provider_display()} ({self.model_name})"

    def save(self, *args, **kwargs):
        if self.is_active:
            # Desactivar otras configuraciones activas para esta institución
            AIProviderConfig.objects.filter(institution=self.institution, is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
