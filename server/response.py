import os
import pandas as pd
import numpy as np
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI

# ------------------------
# Azure OpenAI Setup
# ------------------------
api_key = "f923fd20f0b34a888e9c9edaaf31fb39"
api_endpoint = "https://openai-us-east.openai.azure.com/"

embedding_model = AzureOpenAIEmbeddings(
    azure_endpoint=api_endpoint,
    azure_deployment="embedding-ada",
    openai_api_key=api_key,
    openai_api_version="2024-10-01-preview",
    model_kwargs={}
)

chat_model = AzureChatOpenAI(
    openai_api_key=api_key,
    azure_endpoint=api_endpoint,
    deployment_name="gpt-4o",
    openai_api_version="2024-10-01-preview",
    openai_api_type="azure",
    temperature=0.3,
)

# ------------------------
# Detect Infoblox-Related Query
# ------------------------
def is_infoblox_query(query: str) -> bool:
    infoblox_keywords = [
        "infoblox", "nios", "ipam", "dddi", "tdi", "netmri", "bloxone",
        "network insight", "cloud dhcp", "cloud dns", "cloud ipam",
        "bloxone threat defense", "grid manager", "dns firewall",
        "infoblox api", "ib-nios", "bloxapp", "threat intelligence",
        "data connector", "reporting server", "ib appliance", "infoblox central"
    ]
    return any(keyword in query.lower() for keyword in infoblox_keywords)

# ------------------------
# GPT-4o Direct Answer for Infoblox Topics
# ------------------------
def answer_direct_gpt(query: str):
    print(f"\n🤖 Using GPT-4o for Infoblox-related question:\n🔍 {query}")
    response = chat_model.invoke([
        {
            "role": "system",
            "content": "You are an expert on Infoblox products and services. Answer clearly, concisely, and accurately."
        },
        {"role": "user", "content": query}
    ])
    print("\n💬 GPT-4o Answer:\n")
    print(response.content)

# ------------------------
# Load Cached FAISS or Build from Parquet
# ------------------------
def load_cached_vectorstore(parquet_path: str, faiss_path: str) -> FAISS:
    if os.path.exists(faiss_path):
        print(f"🔁 Using cached FAISS index from: {faiss_path}")
        return FAISS.load_local(faiss_path, embedding_model, allow_dangerous_deserialization=True)

    print(f"📄 Loading embeddings from Parquet: {parquet_path}")
    df = pd.read_parquet(parquet_path)

    texts = df["content"].tolist()
    embeddings = [
        embedding.tolist() if isinstance(embedding, (list, np.ndarray)) else embedding
        for embedding in df["embedding"]
    ]
    metadatas = df[["source_url", "title", "deep_link", "deep_link_description"]].to_dict(orient="records")

    print("⚙️ Creating FAISS vectorstore from cached embeddings...")
    embedding_text_tuples = list(zip(texts, embeddings))  # (text, embedding)
    vectorstore = FAISS.from_embeddings(
        embedding_text_tuples,
        metadatas=metadatas,
        embedding=embedding_model
    )

    vectorstore.save_local(faiss_path)
    print(f"✅ FAISS index saved to: {faiss_path}")
    return vectorstore

# ------------------------
# RAG-Based Answer with Vectorstore
# ------------------------
def run_rag_query(query: str, vectorstore: FAISS, k=8):
    print(f"\n🔍 Query: {query}")
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": k})
    docs = retriever.get_relevant_documents(query)

    context = "\n\n".join(doc.page_content for doc in docs)

    system_msg = "You are a helpful assistant answering questions based on internal documents. Respond using the provided context only."
    user_msg = f"""
Use the context below to answer the question. Be concise and accurate. Do not include any formatting.

Context:
{context}

Question: {query}
"""

    response = chat_model.invoke([
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ])

    print("\n💬 RAG Answer:\n")
    print(response.content)

# ------------------------
# Main Program Loop
# ------------------------
if __name__ == "__main__":
    parquet_path = "./output/embeddings.parquet"
    faiss_path = "./output/faiss_index"

    vectorstore = load_cached_vectorstore(parquet_path, faiss_path)

    while True:
        query = input("\n💬 Ask a question (or type 'exit'): ")
        if query.lower() in {"exit", "quit"}:
            break

        if is_infoblox_query(query):
            answer_direct_gpt(query)
        else:
            run_rag_query(query, vectorstore)
