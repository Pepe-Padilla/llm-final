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

def rephrase_incidence(incident: Dict[str, Any]) -> str:
    """Rephrase the incident description to be more clear and structured."""
    llm = get_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that rephrases incident descriptions to be more clear and structured."),
        ("user", """Please rephrase the following incident description to be more clear and structured:

{incident}

Focus on:
1. Making the problem statement clear and concise
2. Organizing the information logically
3. Highlighting key details and context
4. Removing any unnecessary information""")
    ])
    
    chain = prompt | llm
    
    return chain.invoke({"incident": str(incident)}) 