import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()

def get_llm():
    """Get the appropriate LLM based on environment."""
    if os.getenv("ENTORNO") == "DESA":
        return OllamaLLM(base_url=os.getenv("OLLAMA_BASE_URL"), model="llama3")
    else:
        return ChatOpenAI(
            model="gpt-4-mini",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )

def get_resolution(incident: Dict[str, Any], relevant_solutions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get the best resolution from a list of relevant solutions."""
    llm = get_llm()
    
    # Read prompt from file
    with open("prompts/generate_resolution.txt", "r", encoding="utf-8") as f:
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
    
    resolution = chain.invoke({
        "incident": str(incident),
        "solutions": str(relevant_solutions)
    })

    # print(resolution)
    
    return eval(resolution)  # Convert string to dict 