from langchain_openai import OpenAIEmbeddings

def get_embeddings_model(model="text-embedding-3-small"):
    return OpenAIEmbeddings(model=model)
