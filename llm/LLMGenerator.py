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

def generate_summary(metadata: Dict[str, Any]) -> str:
    """Generate a summary of the incident from its metadata."""
    llm = get_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that summarizes incident metadata into a clear problem description."),
        ("user", "Please summarize the following incident metadata into a clear problem description:\n{metadata}")
    ])
    
    chain = prompt | llm
    
    return chain.invoke({"metadata": str(metadata)}) 