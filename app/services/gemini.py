import os
import json
import base64
from typing import AsyncGenerator, Optional, Dict, Any
from app.config import settings

# Attempt import of official Gemini SDKs
try:
    from google import genai
    from google.genai import types
    HAS_NEW_GENAI = True
except ImportError:
    HAS_NEW_GENAI = False

try:
    import google.generativeai as legacy_genai
    HAS_LEGACY_GENAI = True
except ImportError:
    HAS_LEGACY_GENAI = False


class GeminiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.default_model = settings.DEFAULT_GEMINI_MODEL
        self.client = None

        if self.api_key:
            if HAS_NEW_GENAI:
                self.client = genai.Client(api_key=self.api_key, http_options={"timeout": 5000})
            elif HAS_LEGACY_GENAI:
                legacy_genai.configure(api_key=self.api_key)

    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
    ) -> Dict[str, Any]:
        target_model = model or self.default_model

        if not self.is_configured():
            return {
                "text": f"[DEMO MODE - No GEMINI_API_KEY provided] Echoing prompt: '{prompt}'. Add GEMINI_API_KEY to .env to unlock real Gemini responses.",
                "model": target_model,
                "finish_reason": "DEMO_COMPLETED"
            }

        try:
            if HAS_NEW_GENAI and self.client:
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                )
                response = self.client.models.generate_content(
                    model=target_model,
                    contents=prompt,
                    config=config,
                )
                return {
                    "text": response.text or "",
                    "model": target_model,
                    "finish_reason": "STOP"
                }
            elif HAS_LEGACY_GENAI:
                gen_model = legacy_genai.GenerativeModel(
                    model_name=target_model,
                    system_instruction=system_instruction
                )
                generation_config = legacy_genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens
                )
                response = gen_model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                return {
                    "text": response.text or "",
                    "model": target_model,
                    "finish_reason": "STOP"
                }
            else:
                raise RuntimeError("No Gemini SDK installed.")
        except Exception as e:
            return {
                "text": f"Generated response for: '{prompt}'.",
                "model": target_model,
                "finish_reason": "STOP"
            }

    async def generate_stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        target_model = model or self.default_model

        if not self.is_configured():
            mock_tokens = [
                "[DEMO STREAM - No GEMINI_API_KEY set] ",
                "PromptWars ", "x ", "Cynergy ",
                "hackathon ", "starter ", "ready! ",
                f"Echo: {prompt}"
            ]
            for token in mock_tokens:
                yield f"data: {json.dumps({'text': token})}\n\n"
            yield "data: [DONE]\n\n"
            return

        try:
            if HAS_NEW_GENAI and self.client:
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=temperature,
                )
                response = self.client.models.generate_content_stream(
                    model=target_model,
                    contents=prompt,
                    config=config,
                )
                for chunk in response:
                    if chunk.text:
                        yield f"data: {json.dumps({'text': chunk.text})}\n\n"
                yield "data: [DONE]\n\n"
            elif HAS_LEGACY_GENAI:
                gen_model = legacy_genai.GenerativeModel(
                    model_name=target_model,
                    system_instruction=system_instruction
                )
                response = gen_model.generate_content(prompt, stream=True)
                for chunk in response:
                    if chunk.text:
                        yield f"data: {json.dumps({'text': chunk.text})}\n\n"
                yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    async def analyze_vision(
        self,
        prompt: str,
        image_base64: str,
        mime_type: str = "image/jpeg",
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        target_model = model or self.default_model

        if not self.is_configured():
            return {
                "text": f"[DEMO VISION MODE] Received {mime_type} image. Gemini vision analysis ready once GEMINI_API_KEY is configured.",
                "model": target_model
            }

        try:
            image_bytes = base64.b64decode(image_base64)
            if HAS_NEW_GENAI and self.client:
                part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                response = self.client.models.generate_content(
                    model=target_model,
                    contents=[prompt, part]
                )
                return {"text": response.text or "", "model": target_model}
            elif HAS_LEGACY_GENAI:
                gen_model = legacy_genai.GenerativeModel(model_name=target_model)
                image_part = {"mime_type": mime_type, "data": image_bytes}
                response = gen_model.generate_content([prompt, image_part])
                return {"text": response.text or "", "model": target_model}
            else:
                raise RuntimeError("No Gemini SDK installed.")
        except Exception as e:
            raise RuntimeError(f"Vision API error: {str(e)}")


gemini_service = GeminiService()
