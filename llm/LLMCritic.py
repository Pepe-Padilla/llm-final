"""LLM para crítica de resoluciones."""

from typing import Dict, Any
from langchain_ollama import OllamaLLM
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from .LLMLogger import log_llm_interaction
from config import ENTORNO, OLLAMA_BASE_URL, OPENAI_API_KEY, LLM_MODEL_DESA, LLM_MODEL_PROD, LLM_TEMPERATURE

def get_llm():
    """Obtiene el LLM apropiado según el entorno."""
    if ENTORNO == "DESA":
        return OllamaLLM(base_url=OLLAMA_BASE_URL, model=LLM_MODEL_DESA, temperature=LLM_TEMPERATURE)
    else:
        return ChatOpenAI(
            model=LLM_MODEL_PROD,
            temperature=LLM_TEMPERATURE,
            api_key=OPENAI_API_KEY
        )

def evaluate_resolution(incident: Dict[str, Any], resolution: Dict[str, Any]) -> str:
    """Evalúa si una resolución propuesta es apropiada para la incidencia dada."""
    llm = get_llm()
    
    with open("prompts/critic_resolution.txt", "r", encoding="utf-8") as f:
        prompt_content = f.read()
    
    system_msg, user_msg = prompt_content.split("---", 1)
    system_msg = system_msg.replace("system: ", "").strip()
    user_msg = user_msg.replace("user: ", "").strip()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("user", user_msg)
    ])
    
    chain = prompt | llm
    
    input_data = {
        "incident_id": incident.get("codIncidencia", "unknown"),
        "incident_title": incident.get("titulo", ""),
        "resolution_type": resolution.get("metadata", {}).get("RESOLUCION AUTOMÁTICA", ""),
        "resolution_summary": resolution.get("metadata", {}).get("SOLUCIÓN", "")
    }
    
    evaluation = chain.invoke({
        "incident": str(incident),
        "resolution": str(resolution)
    })

    log_llm_interaction("LLMCritic", input_data, evaluation)
    return evaluation 