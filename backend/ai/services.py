import abc
import anthropic
from openai import OpenAI
from .models import AIProviderConfig

class BaseAIProvider(abc.ABC):
    @abc.abstractmethod
    def generate_completion(self, prompt: str, system_prompt: str = "") -> str:
        pass

class AnthropicProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def generate_completion(self, prompt: str, system_prompt: str = "") -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text

class OpenAIProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: str, base_url: str = None):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def generate_completion(self, prompt: str, system_prompt: str = "") -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

class AIServiceFactory:
    @staticmethod
    def get_provider(institution) -> BaseAIProvider:
        config = AIProviderConfig.objects.filter(institution=institution, is_active=True).first()
        if not config:
            raise ValueError("No hay configuración de IA activa para esta institución.")

        if config.provider == 'anthropic':
            return AnthropicProvider(api_key=config.api_key, model=config.model_name)
        elif config.provider == 'openai':
            return OpenAIProvider(api_key=config.api_key, model=config.model_name)
        elif config.provider == 'local':
            return OpenAIProvider(api_key=config.api_key, model=config.model_name, base_url=config.api_base_url)
        
        raise ValueError(f"Proveedor '{config.provider}' no soportado.")
