from langchain_openai import ChatOpenAI

def get_llm_model(temperature=0, model="gpt-4o-mini"):
    """Get the standard LLM model (default is mini)."""
    return ChatOpenAI(temperature=temperature, model=model)

def get_generator_model(temperature=0, model="gpt-4o"):
    """Get the generator LLM model (can be a stronger model)."""
    return ChatOpenAI(temperature=temperature, model=model)
