"""
app/services/nodes/generator.py

Provides the answer_generator node for the main LangGraph agent.
Moved from src/nodes/generator.py — import paths updated for the new structure.
Logic is unchanged.
"""
from langchain_core.messages import AIMessage
from app.core.config import settings  # noqa: F401 (ensures env vars are loaded)
from langchain_openai import ChatOpenAI


def get_generator_model(temperature: float = 0, model: str = "gpt-4o") -> ChatOpenAI:
    """Get the generator LLM model (strong model for final answer synthesis)."""
    return ChatOpenAI(temperature=temperature, model=model)


def answer_generator(state: dict) -> dict:
    """LangGraph node: Generate the final answer for the user.

    Reads from MainAgentState:
        current_question (str): The user's question.
        retrieved_info    (str): Synthesized context from retrieval subgraph.
        messages          (list): Conversation history (BaseMessage list).

    Returns:
        final_answer (str): The generated answer.
        messages     (list): Updated with the new AIMessage.
    """
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
        "messages": [AIMessage(content=response.content)],
    }
