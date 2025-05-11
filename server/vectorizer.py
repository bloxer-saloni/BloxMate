import os
import time
import hashlib
import json
import pandas as pd
import ssl
import nltk

# Fix SSL certificate verification issues for NLTK
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Pre-download NLTK data with SSL verification disabled
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

from langchain_community.document_loaders import (
    UnstructuredPDFLoader,
    UnstructuredWordDocumentLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings
from langchain.schema import Document
from unstructured.partition.pptx import partition_pptx

# -------------------------------
# Azure OpenAI Configuration
# -------------------------------
api_key = "87BvNkDR0nvGs9bRSQNyNOeVWcKQqumCWNwlbPMi6QEwitD8CB0kJQQJ99BEACHYHv6XJ3w3AAABACOGZZmZ"
api_endpoint = "https://hackfest25.openai.azure.com/"

embeddings_model = AzureOpenAIEmbeddings(
    azure_endpoint=api_endpoint,
    azure_deployment="embedding-ada",
    openai_api_key=api_key,
    openai_api_version="2024-10-01-preview",
    model_kwargs={}
)

print("✅ Azure OpenAI client initialized")

# -------------------------------
# Helper Functions
# -------------------------------
def clean_text(text):
    if not text:
        return ""
    return text.replace("**", "").replace("*", "").replace("_", "").strip()

def load_pptx(file_path):
    elements = partition_pptx(filename=file_path)
    return [
        Document(
            page_content=clean_text(el.text),
            metadata={
                "id": os.path.basename(file_path),
                "source_url": file_path,
                "title": os.path.basename(file_path),
                "deep_link": file_path,
                "deep_link_description": "Local file"
            }
        )
        for el in elements if el.text
    ]

def compute_file_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

# -------------------------------
# Vectorizer Class 
# -------------------------------
class LocalVectorizer:
    def __init__(self, chunk_size=500, chunk_overlap=100, batch_size=30, sleep_time=1, cache_file="embedding_cache.json"):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.batch_size = batch_size
        self.sleep_time = sleep_time
        self.embedding_model = embeddings_model
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        with open(self.cache_file, "w") as f:
            json.dump(self.cache, f, indent=2)

    def extract_text_from_excel(self, file_path):
        df_dict = pd.read_excel(file_path, sheet_name=None)
        parts = []
        for sheet_name, df in df_dict.items():
            parts.append(f"### Sheet: {sheet_name}\n")
            parts.append(df.astype(str).to_string(index=False))
        return "\n\n".join(parts)

    def load_local_documents(self, folder_path):
        docs = []

        for root, _, files in os.walk(folder_path):
            for file_name in files:
                full_path = os.path.join(root, file_name)
                ext = file_name.lower().split(".")[-1]

                try:
                    file_hash = compute_file_hash(full_path)
                    cache_key = f"{full_path}|{file_hash}"

                    if cache_key in self.cache:
                        print(f"⏩ Skipping cached file: {file_name}")
                        continue

                    if ext == "pdf":
                        loader = UnstructuredPDFLoader(full_path)
                        file_docs = loader.load()

                    elif ext in {"docx", "doc"}:
                        loader = UnstructuredWordDocumentLoader(full_path)
                        file_docs = loader.load()

                    elif ext in {"ppt", "pptx"}:
                        file_docs = load_pptx(full_path)

                    elif ext in {"xlsx", "xls"}:
                        excel_text = self.extract_text_from_excel(full_path)
                        file_docs = [Document(
                            page_content=clean_text(excel_text),
                            metadata={
                                "id": os.path.basename(full_path),
                                "source_url": full_path,
                                "title": file_name,
                                "deep_link": full_path,
                                "deep_link_description": "Local file"
                            }
                        )]

                    else:
                        print(f"⚠️ Skipping unsupported file: {file_name}")
                        continue

                    for doc in file_docs:
                        doc.page_content = clean_text(doc.page_content)
                        doc.metadata.update({
                            "id": os.path.basename(full_path),
                            "source_url": full_path,
                            "title": file_name,
                            "deep_link": full_path,
                            "deep_link_description": "Local file"
                        })

                    docs.extend(file_docs)
                    self.cache[cache_key] = True  # Mark as processed

                except Exception as e:
                    print(f"❌ Error loading {file_name}: {e}")

        return docs

    def generate_embeddings_batch(self, documents):
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )

        try:
            split_documents = splitter.split_documents(documents)
        except Exception as e:
            print(f"❌ Error splitting documents: {e}")
            return []

        print(f"🔢 Total chunks to embed: {len(split_documents)}")
        data_list = []

        for batch_start in range(0, len(split_documents), self.batch_size):
            batch_end = batch_start + self.batch_size
            batch_docs = split_documents[batch_start:batch_end]
            batch_texts = [clean_text(doc.page_content) for doc in batch_docs]

            try:
                print(f"⚙️ Embedding batch {batch_start}–{batch_end}...")
                batch_embeddings = self.embedding_model.embed_documents(batch_texts)

                for doc, embedding in zip(batch_docs, batch_embeddings):
                    data_list.append({
                        "id": doc.metadata["id"],
                        "content": doc.page_content,
                        "embedding": embedding,
                        "source_url": doc.metadata["source_url"],
                        "title": doc.metadata["title"],
                        "deep_link": doc.metadata["deep_link"],
                        "deep_link_description": doc.metadata["deep_link_description"]
                    })

                time.sleep(self.sleep_time)
            except Exception as e:
                print(f"❌ Error embedding batch {batch_start}–{batch_end}: {e}")

        return data_list

    def save_to_parquet(self, data, output_path):
        df = pd.DataFrame(data)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_parquet(output_path, index=False)
        print(f"✅ Embeddings saved to: {output_path}")

    def run(self, input_folder, output_file):
        print(f"📂 Loading from: {input_folder}")
        documents = self.load_local_documents(input_folder)

        if not documents:
            print("❌ No documents to process.")
            return

        print("🧠 Generating embeddings...")
        embeddings = self.generate_embeddings_batch(documents)

        if not embeddings:
            print("❌ No embeddings generated.")
            return

        print("💾 Saving embeddings...")
        self.save_to_parquet(embeddings, output_file)
        self._save_cache()
        print("🎉 Vectorization complete!")

# -------------------------------
# Entry Point
# -------------------------------
if __name__ == "__main__":
    # add your file path here
    input_folder = "/Users/vvazirani/demo-nam/Data Science Weekly Status Update.pdf"
    output_file = "./output/updates_embeddings.parquet"

    vectorizer = LocalVectorizer(chunk_size=500, chunk_overlap=100)
    vectorizer.run(input_folder, output_file)
    print("✅ Vectorization completed successfully.")