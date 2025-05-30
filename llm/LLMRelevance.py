import os
from typing import Dict, Any
from langchain.llms import Ollama
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

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

def check_relevance(incident: Dict[str, Any]) -> bool:
    """Check if the incident is relevant for automatic resolution."""
    llm = get_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that determines if an incident can be automatically resolved."),
        ("user", """Please determine if the following incident can be automatically resolved:

{incident}

Consider the following criteria:
1. The incident has enough information to make a decision
2. The incident is not too complex or requires human judgment
3. The incident is not a critical system issue
4. The incident is not a security-related issue

Please respond with 'true' if the incident can be automatically resolved, or 'false' if it requires human intervention.""")
    ])
    
    chain = prompt | llm
    
    response = chain.invoke({"incident": str(incident)})
    
    return response.lower().strip() == "true" 