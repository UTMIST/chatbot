# This embeds the data into a vector database
import os

os.environ["OPENAI_API_KEY"] = "Your_Key"

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

documents = SimpleDirectoryReader(input_files=["instagram.txt"]).load_data()
index = VectorStoreIndex.from_documents(documents)
index.storage_context.persist()