"""
app/services/nodes/generator.py

Provides the answer_generator node for the main LangGraph agent.
Moved from src/nodes/generator.py — import paths updated for the new structure.
Logic is unchanged.
"""
from pathlib import Path
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from app.core.config import settings  # noqa: F401 (ensures env vars are loaded)
from langchain_openai import ChatOpenAI


def load_system_prompt() -> str:
    """Load system prompt from SYSTEM-PROMPT.md file."""
    prompt_path = Path(__file__).parent.parent / "config" / "SYSTEM-PROMPT.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"System prompt file not found at {prompt_path}")
    return prompt_path.read_text()


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

    print("[AnswerGen] ========== START DEBUG ==========")
    print(f"[AnswerGen] Question: {question}")
    print(f"[AnswerGen] Retrieved info length: {len(info)} chars")
    print(f"[AnswerGen] Info preview: {info[:200] if info else '(EMPTY)'}...")

    hist_str = "\n".join(f"{m.type}: {m.content}" for m in history)

    # Load system prompt from external file
    print("[AnswerGen] Loading system prompt from file...")
    try:
        system_prompt_template = load_system_prompt()
        print(f"[AnswerGen] ✅ System prompt loaded ({len(system_prompt_template)} chars)")
    except Exception as e:
        print(f"[AnswerGen] ❌ Error loading system prompt: {e}")
        raise

    # Format the context into the system prompt
    print("[AnswerGen] Formatting system prompt with context...")
    try:
        formatted_system_prompt = system_prompt_template.format(
            info=info,
            hist_str=hist_str,
            question=question
        )
        print(f"[AnswerGen] ✅ System prompt formatted ({len(formatted_system_prompt)} chars)")
        print(f"[AnswerGen] Formatted prompt preview:\n{formatted_system_prompt[:400]}...")
    except Exception as e:
        print(f"[AnswerGen] ❌ Error formatting prompt: {e}")
        raise

    # Use proper message structure: SystemMessage + HumanMessage
    print("[AnswerGen] Creating messages for LLM...")
    messages = [
        SystemMessage(content=formatted_system_prompt),
        HumanMessage(content=question)
    ]
    print(f"[AnswerGen] ✅ Messages created: {len(messages)} messages")
    print(f"[AnswerGen] Message types: {[type(m).__name__ for m in messages]}")

    print("[AnswerGen] Invoking LLM (gpt-4o)...")
    llm = get_generator_model()
    response = llm.invoke(messages)

    print(f"[AnswerGen] ✅ LLM response received ({len(response.content)} chars)")
    print(f"[AnswerGen] Response:\n{response.content}")
    print("[AnswerGen] ========== END DEBUG ==========")

    return {
        "final_answer": response.content,
        "messages": [AIMessage(content=response.content)],
    }
