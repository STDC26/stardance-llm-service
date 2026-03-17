from anthropic import AsyncAnthropic
from app.core.config import Settings
from app.services.prompt_registry_service import get_prompt_registry
from typing import Optional


class AnthropicService:
    def __init__(self, settings: Settings) -> None:
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key, timeout=settings.anthropic_default_timeout)

    async def call(self, model, prompt_id, prompt_version, payload, max_tokens=1024):
        registry = get_prompt_registry()
        prompt_record = registry.resolve_for_call(prompt_id, prompt_version)
        try:
            user_content = prompt_record.content.format(**payload)
        except KeyError:
            user_content = f"{prompt_record.content}\n\nContext:\n{payload}"
        response = await self._client.messages.create(model=model, max_tokens=max_tokens, messages=[{"role": "user", "content": user_content}])
        content = response.content[0].text if response.content else ""
        return {"content": content, "model_version": response.model, "prompt_version": prompt_record.prompt_version, "tokens_in": response.usage.input_tokens, "tokens_out": response.usage.output_tokens}
