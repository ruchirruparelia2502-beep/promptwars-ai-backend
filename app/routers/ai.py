from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas.models import (
    GenerateRequest,
    GenerateResponse,
    VisionRequest,
    StructuredDataRequest
)
from app.services.gemini import gemini_service
import json

router = APIRouter(prefix="/api/v1", tags=["AI Engine"])

@router.post("/generate", response_model=GenerateResponse, summary="Generate AI Content / Prompt")
async def generate(req: GenerateRequest):
    try:
        result = await gemini_service.generate_text(
            prompt=req.prompt,
            system_instruction=req.system_instruction,
            model=req.model,
            temperature=req.temperature,
            max_output_tokens=req.max_output_tokens
        )
        return GenerateResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream", summary="Real-time Server-Sent Events (SSE) Stream")
async def stream(req: GenerateRequest):
    try:
        return StreamingResponse(
            gemini_service.generate_stream(
                prompt=req.prompt,
                system_instruction=req.system_instruction,
                model=req.model,
                temperature=req.temperature
            ),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vision", summary="Multimodal Vision Prompting")
async def vision(req: VisionRequest):
    try:
        result = await gemini_service.analyze_vision(
            prompt=req.prompt,
            image_base64=req.image_base64,
            mime_type=req.mime_type or "image/jpeg",
            model=req.model
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/structured", summary="Structured JSON Generation")
async def structured(req: StructuredDataRequest):
    try:
        system_prompt = (
            f"{req.instruction}\n\n"
            "CRITICAL: You must reply ONLY with valid JSON. Do not wrap in markdown or backticks."
        )
        if req.json_schema:
            system_prompt += f"\nSchema to adhere to: {json.dumps(req.json_schema)}"

        result = await gemini_service.generate_text(
            prompt=req.prompt,
            system_instruction=system_prompt,
            model=req.model,
            temperature=0.2
        )
        # Attempt parsing to ensure pure json
        raw_text = result["text"].strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()

        try:
            parsed = json.loads(raw_text)
            return {"data": parsed, "raw": raw_text}
        except json.JSONDecodeError:
            return {"data": None, "raw": raw_text, "note": "Failed to parse strictly as JSON"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
