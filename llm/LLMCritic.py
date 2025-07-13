import os
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from .LLMLogger import log_llm_interaction

# Load environment variables
load_dotenv()

def get_llm():
    """Get the appropriate LLM based on environment."""
    if os.getenv("ENTORNO") == "DESA":
        return OllamaLLM(base_url=os.getenv("OLLAMA_BASE_URL"), model="gemma3", temperature=0)
    else:
        return ChatOpenAI(
            model="gpt-4-mini",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )

def evaluate_resolution(incident: Dict[str, Any], resolution: Dict[str, Any]) -> str:
    """
    Evaluate if a proposed resolution is appropriate for the given incident.
    
    Args:
        incident: The incident dictionary with all details and history
        resolution: The proposed resolution dictionary
    
    Returns:
        str: JSON string with evaluation result
    """
    llm = get_llm()
    
    # Read prompt from file
    with open("prompts/critic_resolution.txt", "r", encoding="utf-8") as f:
        prompt_content = f.read()
    
    # Split the content into system and user messages
    system_msg, user_msg = prompt_content.split("---", 1)
    system_msg = system_msg.replace("system: ", "").strip()
    user_msg = user_msg.replace("user: ", "").strip()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("user", user_msg)
    ])
    
    chain = prompt | llm
    
    # Format the input for logging
    input_data = {
        "incident_id": incident.get("codIncidencia", "unknown"),
        "incident_title": incident.get("titulo", ""),
        "resolution_type": resolution.get("metadata", {}).get("RESOLUCION AUTOMÁTICA", ""),
        "resolution_summary": resolution.get("metadata", {}).get("SOLUCIÓN", "")
    }
    
    # Get evaluation
    evaluation = chain.invoke({
        "incident": str(incident),
        "resolution": str(resolution)
    })

    # Log the interaction
    log_llm_interaction("LLMCritic", input_data, evaluation)

    # Return the raw response string for the calling service to handle
    return evaluation 