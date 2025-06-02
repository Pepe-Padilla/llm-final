import os
from typing import Dict, Any, List
from langchain.llms import Ollama
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from .LLMQuery import query_vector_db

def get_llm():
    """Get the appropriate LLM based on environment."""
    if os.getenv("ENTORNO") == "DESA":
        return Ollama(base_url=os.getenv("OLLAMA_BASE_URL"), model="llama3")
    else:
        return ChatOpenAI(
            model="gpt-4-mini",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )

def generate_resolution(incident: Dict[str, Any], similar_incidents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a resolution for the incident based on similar incidents."""
    llm = get_llm()
    
    # Read prompt from file
    with open("prompts/generate_resolution.txt", "r", encoding="utf-8") as f:
        prompt_content = f.read()
    
    # Split the content into system and user messages
    system_msg, user_msg = prompt_content.split("\n\n", 1)
    system_msg = system_msg.replace("system: ", "")
    user_msg = user_msg.replace("user: ", "")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        ("user", user_msg)
    ])
    
    chain = prompt | llm
    
    resolution = chain.invoke({
        "incident": str(incident),
        "similar_incidents": str(similar_incidents)
    })
    
    return eval(resolution)  # Convert string to dict

def get_resolution(incident: Dict[str, Any]) -> Dict[str, Any]:
    """Get a resolution for the incident by querying similar incidents and generating a resolution."""
    # Query similar incidents
    similar_incidents = query_vector_db(str(incident))
    
    # Generate resolution
    return generate_resolution(incident, similar_incidents) 