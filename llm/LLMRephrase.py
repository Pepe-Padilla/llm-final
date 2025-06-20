import os
from typing import Dict, Any, List
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

def rephrase_incidence(incident: Dict[str, Any]) -> List[str]:
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

    # Get rephrased versions
    rephrased = chain.invoke({"incident": str(incident)})
    
    # print(rephrased)

    # A veces mete agrupadores tipo {} en vez de un Array simple de Strings
    rephrased.replace("{","")
    rephrased.replace("}","")

    # Parse the JSON array from the response
    rephrased_list = []
    try :
        rephrased_list = json.loads(rephrased)
    except:
        print("Error en json loads rephrase_incidence")
        print(rephrased)
    
    # Add the original incident at the beginning
    return [str(incident["descripcion"])] + rephrased_list 