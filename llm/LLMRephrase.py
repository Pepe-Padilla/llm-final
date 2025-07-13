"""LLM para reformular incidencias."""

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

def rephrase_incidence(incident: Dict[str, Any]) -> str:
    """Rephrase the incident description to be more clear and structured."""
    llm = get_llm()
    
    # Read prompt from file
    with open("prompts/rephrase_incidence.txt", "r", encoding="utf-8") as f:
        prompt_content = f.read()
    
    # Split the content into system and user messages
    system_msg, user_msg = prompt_content.split("---", 1)
    system_msg = system_msg.replace("system: ", "")
    user_msg = user_msg.replace("user: ", "")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("user", user_msg)
    ])
    
    chain = prompt | llm

    # Get rephrased versions and return raw response
    rephrased = chain.invoke({"incident": str(incident)})
    
    # Log the interaction
    log_llm_interaction("LLMRephrase", incident, rephrased)
    
    # Return the raw response string for the calling service to handle
    return rephrased 