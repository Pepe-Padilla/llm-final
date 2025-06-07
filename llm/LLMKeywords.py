import os
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import json

# Load environment variables
load_dotenv()

def get_llm():
    """Get the appropriate LLM based on environment."""
    if os.getenv("ENTORNO") == "DESA":
        return OllamaLLM(base_url=os.getenv("OLLAMA_BASE_URL"), model="llama3", temperature=0)
    else:
        return ChatOpenAI(
            model="gpt-4-mini",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )

def extract_keywords(incident: Dict[str, Any]) -> Dict[str, Any]:
    """Extract keywords from incident description, title and history."""
    llm = get_llm()
    
    # Read prompt from file
    with open("prompts/extract_keywords.txt", "r", encoding="utf-8") as f:
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
    
    response = chain.invoke({"incident": str(incident)})
    
    # Parse the JSON response
    json_response = {}
    try:
        json_response = json.loads(response)
    except:
        print("Error al interpretar json de extract_keywords")
        print(response)

    return json.loads(json_response) 