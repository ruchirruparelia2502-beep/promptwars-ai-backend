from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    environment: str
    gemini_configured: bool

class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="Prompt or user query")
    system_instruction: Optional[str] = Field(None, description="System instructions / persona")
    model: Optional[str] = Field(None, description="Gemini model name (defaults to env configuration)")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_output_tokens: Optional[int] = Field(2048, description="Maximum tokens to generate")

class GenerateResponse(BaseModel):
    text: str
    model: str
    finish_reason: Optional[str] = None

class VisionRequest(BaseModel):
    prompt: str = Field(..., description="Instruction or query regarding the image")
    image_base64: str = Field(..., description="Base64-encoded image string")
    mime_type: Optional[str] = Field("image/jpeg", description="MIME type e.g. image/jpeg, image/png")
    model: Optional[str] = Field(None, description="Gemini model name")

class StructuredDataRequest(BaseModel):
    prompt: str = Field(..., description="Data to extract or format")
    instruction: Optional[str] = Field("Extract key information strictly adhering to the requested JSON format.")
    json_schema: Optional[Dict[str, Any]] = Field(None, description="Optional target JSON schema definition")
    model: Optional[str] = Field(None)
