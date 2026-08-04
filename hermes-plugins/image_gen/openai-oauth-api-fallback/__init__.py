"""Hermes image backend: Codex OAuth, then Krea, then OpenAI API key."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent.image_gen_provider import DEFAULT_ASPECT_RATIO, ImageGenProvider, error_response


_PRIMARY = "openai-codex"
_SECONDARY = "krea"
_TERTIARY = "openai"
_FALLBACK_ERROR_TYPES = {
    "api_error",
    "auth_required",
    "connection_error",
    "empty_response",
    "invalid_response",
    "missing_dependency",
    "timeout",
}
_MODELS = [
    {
        "id": "gpt-image-2-low",
        "display": "GPT Image 2 - Low",
        "speed": "~15s",
        "strengths": "Fast iteration",
        "price": "OAuth first; Krea second; OpenAI API last",
    },
    {
        "id": "gpt-image-2-medium",
        "display": "GPT Image 2 - Medium",
        "speed": "~40s",
        "strengths": "Balanced default",
        "price": "OAuth first; Krea second; OpenAI API last",
    },
    {
        "id": "gpt-image-2-high",
        "display": "GPT Image 2 - High",
        "speed": "~2min",
        "strengths": "Highest fidelity",
        "price": "OAuth first; Krea second; OpenAI API last",
    },
]


class OpenAIOAuthApiFallbackProvider(ImageGenProvider):
    @property
    def name(self) -> str:
        return "openai-oauth-api-fallback"

    @property
    def display_name(self) -> str:
        return "Images - OAuth, Krea, OpenAI API"

    def _providers(self):
        from agent.image_gen_registry import get_provider

        return (
            get_provider(_PRIMARY),
            get_provider(_SECONDARY),
            get_provider(_TERTIARY),
        )

    def is_available(self) -> bool:
        return any(
            provider and provider.is_available()
            for provider in self._providers()
        )

    def list_models(self) -> List[Dict[str, Any]]:
        return list(_MODELS)

    def default_model(self) -> Optional[str]:
        return "gpt-image-2-medium"

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": self.display_name,
            "badge": "fallback",
            "tag": "Codex OAuth first; Krea second; OpenAI API key last",
            "env_vars": [
                {
                    "key": "OPENAI_API_KEY",
                    "prompt": "OpenAI API key (final fallback)",
                    "url": "https://platform.openai.com/api-keys",
                }
            ],
        }

    def capabilities(self) -> Dict[str, Any]:
        return {"modalities": ["text", "image"], "max_reference_images": 16}

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        *,
        image_url: Optional[str] = None,
        reference_image_urls: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        primary, secondary, tertiary = self._providers()
        call_kwargs = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "image_url": image_url,
            "reference_image_urls": reference_image_urls,
            **kwargs,
        }

        if primary is None:
            primary_result = error_response(
                error="Codex OAuth image backend is not registered",
                error_type="auth_required",
                provider=_PRIMARY,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )
        else:
            primary_result = primary.generate(**call_kwargs)

        if primary_result.get("success"):
            primary_result["route"] = "oauth-primary"
            return primary_result

        primary_error_type = str(primary_result.get("error_type") or "")
        if primary_error_type not in _FALLBACK_ERROR_TYPES:
            primary_result["route"] = "oauth-primary-no-fallback"
            return primary_result

        secondary_result: Optional[Dict[str, Any]] = None
        if secondary is not None and secondary.is_available():
            secondary_result = secondary.generate(**call_kwargs)
            if secondary_result.get("success"):
                secondary_result["route"] = "krea-secondary"
                secondary_result["primary_error_type"] = primary_error_type
                secondary_result["primary_error"] = str(primary_result.get("error") or "")
                return secondary_result
            secondary_error_type = str(secondary_result.get("error_type") or "")
            if secondary_error_type not in _FALLBACK_ERROR_TYPES:
                secondary_result["route"] = "krea-secondary-no-api-fallback"
                secondary_result["primary_error_type"] = primary_error_type
                secondary_result["primary_error"] = str(primary_result.get("error") or "")
                return secondary_result

        if tertiary is None or not tertiary.is_available():
            secondary_error = (
                str(secondary_result.get("error") or "")
                if secondary_result is not None
                else "Krea unavailable"
            )
            return error_response(
                error=(
                    f"OAuth failed: {primary_result.get('error', 'unknown error')}. "
                    f"Krea failed: {secondary_error}. "
                    "OpenAI API-key fallback is unavailable."
                ),
                error_type="fallback_unavailable",
                provider=self.name,
                model=str(primary_result.get("model") or ""),
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )

        tertiary_result = tertiary.generate(**call_kwargs)
        tertiary_result["route"] = "openai-api-tertiary"
        tertiary_result["primary_error_type"] = primary_error_type
        tertiary_result["primary_error"] = str(primary_result.get("error") or "")
        if secondary_result is not None:
            tertiary_result["secondary_error_type"] = str(
                secondary_result.get("error_type") or ""
            )
            tertiary_result["secondary_error"] = str(secondary_result.get("error") or "")
        else:
            tertiary_result["secondary_error_type"] = "unavailable"
            tertiary_result["secondary_error"] = "Krea unavailable"
        return tertiary_result


def register(ctx) -> None:
    ctx.register_image_gen_provider(OpenAIOAuthApiFallbackProvider())
