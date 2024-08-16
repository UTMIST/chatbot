import os
import openai
from llama_index.llms.openai import OpenAI
from llama_index.core import Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.extractors import TitleExtractor
from llama_index.core.ingestion import IngestionPipeline
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import VectorStoreIndex
from qdrant_client import QdrantClient
from llama_index.core.extractors import (
    SummaryExtractor,
    QuestionsAnsweredExtractor,
    TitleExtractor,
    KeywordExtractor,
)
from llama_index.core.schema import MetadataMode, Document

os.environ["OPENAI_API_KEY"] = "Your Key"
# Set up OpenAI API key
llm = OpenAI(temperature=0.1, model="gpt-3.5-turbo")

# Define the directory containing the text files
directory = "/Users/dingshengliu/Desktop/ChatbotAI/chatbot/app/data"


# Function to read text files and create Document objects
def read_files(directory):
    documents = []
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            file_path = os.path.join(directory, filename)
            with open(file_path, "r") as file:
                content = file.read()
                documents.append(Document(text=content))
    return documents


qdrant_key = "N7jUwnesBqzfkh8_v5tkAnzc09ka35LekyLQcY7LL36R9u_4mMTkbA"

qdrant_client = QdrantClient(
    url="https://e66659b9-20a8-4ef9-bcdc-9f978f890043.us-east4-0.gcp.cloud.qdrant.io:6333",
    api_key=qdrant_key,
)
vector_store = QdrantVectorStore(client=qdrant_client, collection_name="test")

pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=128, chunk_overlap=32),
        SummaryExtractor(summaries=["prev", "self", "next"], llm=llm),
        # TitleExtractor(llm=llm, max_tokens=10, temperature=0.3, top_p=0.9),
        # KeywordExtractor(llm=llm, max_keywords=10, threshold=0.2, include_scores=True),
        OpenAIEmbedding(),
    ],
    vector_store=vector_store,
)

# Read files and ingest documents
documents = read_files(directory)
nodes = pipeline.run(documents=documents)

index = VectorStoreIndex(nodes=nodes)
index.storage_context.persist()
