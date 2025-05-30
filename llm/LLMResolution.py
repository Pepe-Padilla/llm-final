import os
from typing import Dict, Any, List
from langchain.llms import Ollama
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from .LLMQuery import query_vector_db

def get_llm():
    """Get the appropriate LLM based on environment."""
    if os.getenv("ENTORNO") == "DESA":
        return Ollama(base_url=os.getenv("OLLAMA_BASE_URL"), model="llama2")
    else:
        return ChatOpenAI(
            model="gpt-4",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )

def generate_resolution(incident: Dict[str, Any], similar_incidents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a resolution for the incident based on similar incidents."""
    llm = get_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that generates incident resolutions based on similar past incidents."),
        ("user", """Please generate a resolution for the following incident based on similar past incidents:

Current Incident:
{incident}

Similar Past Incidents:
{similar_incidents}

Please provide a resolution in the following format:
{
    "type": "manual|close|wait|reassign|api",
    "buzon_destino": "destination mailbox if reassigning",
    "notas_resolucion": "resolution notes",
    "detalle": "detailed explanation"
}""")
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