"""
Lab Copilot API Router for LabLink
Empowers students with AI hardware advisory while keeping all keys strictly in process memory.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from app.schemas.copilot import CopilotChatRequest, CopilotChatResponse
from app.services.copilot_service import process_copilot_chat

router = APIRouter(prefix="/api/v1/copilot", tags=["Lab Copilot AI"])


@router.post("/chat", response_model=CopilotChatResponse)
def copilot_chat_endpoint(request: CopilotChatRequest):
    """
    Interactive Lab Copilot:
    Recommends specialized hardware, dev kits, and workstations based on student project needs.
    Uses Google Gemini Flash if API key is present; otherwise leverages domain fallback.
    Never exposes API keys or internal traces.
    """
    return process_copilot_chat(request)


@router.get("/suggestions", response_model=List[Dict[str, str]])
def get_copilot_starter_prompts():
    """
    Returns popular campus project starter prompts to help students ask Copilot.
    """
    return [
        {
            "title": "Edge AI & Drone SLAM",
            "prompt": "I want to deploy a real-time stereo depth SLAM model on a drone. What hardware and sensors should I reserve?"
        },
        {
            "title": "Spiking Neural Network on FPGA",
            "prompt": "I am working on custom RTL hardware acceleration for spiking neurons. Which FPGA board and logic analyzer do I need?"
        },
        {
            "title": "LLM Fine-Tuning & Quantization",
            "prompt": "My capstone requires fine-tuning a 7B parameter vision-language model. Which GPU workstation has enough VRAM?"
        },
        {
            "title": "Custom SLA Mechanical Gripper",
            "prompt": "I need to 3D print a high-precision compliant gripper with 50-micron tolerance. What 3D printer and resin do you suggest?"
        },
        {
            "title": "Real-Time qPCR DNA Amplification",
            "prompt": "We are quantifying gene expression from bacterial samples. Which thermal cycler and wet bench should we book?"
        }
    ]
