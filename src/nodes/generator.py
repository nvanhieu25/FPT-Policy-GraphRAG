from langchain_core.messages import AIMessage
from src.core.state import MainAgentState
from src.services.llm import get_generator_model

def answer_generator(state: MainAgentState) -> dict:
    question = state["current_question"]
    info = state["retrieved_info"]
    history = state.get("messages", [])
    
    print("[AnswerGen] Generating final response to user...")
    hist_str = "\n".join(f"{m.type}: {m.content}" for m in history)
    
    prompt = f"""
You are an expert FPT Software compliance AI assistant.
Answer the user's question accurately using ONLY the provided retrieved information and conversation history. 
If the information is insufficient, state that clearly. Do not make up internal policies.

History:
{hist_str}

Retrieved Information:
{info}

Question: {question}
"""
    llm = get_generator_model()
    response = llm.invoke(prompt)
    
    return {
        "final_answer": response.content,
        "messages": [AIMessage(content=response.content)]
    }
