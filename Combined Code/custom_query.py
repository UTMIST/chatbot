from llama_index.core.query_engine import CustomQueryEngine
from llama_index.core.retrievers import BaseRetriever
from llama_index.core import get_response_synthesizer
from llama_index.core.response_synthesizers import BaseSynthesizer
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)
import os.path
import os
# Option 2: return a string (we use a raw LLM call for illustration)

from llama_index.llms.openai import OpenAI
from llama_index.core import PromptTemplate

# load documents
os.environ["OPENAI_API_KEY"] = "Your_Key"

PERSIST_DIR = "./storage"
storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
index = load_index_from_storage(storage_context)
retriever = index.as_retriever()

qa_prompt = PromptTemplate(
    "Context information is below.\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "Given the context information and not prior knowledge, "
    "answer the query. When it comes to writing content, "
    "two factors are crucial, \"perplexity\" and \"burstiness\"." 
    "Perplexity measures the complexity of text. Separately, burstiness compares the variations of sentences. "
    "Humans tend to write with greater burstiness, for example, with some longer or complex sentences alongside shorter ones. "
    "AI sentences tend to be more uniform. Therefore, when writing the following contents I am going to ask you to create, "
    "I need it to have a good amount of perplexity and burstiness. You answer should never exceed 40 words.\n"
    "Query: {query_str}\n"
    "Answer: "
)


class RAGStringQueryEngine(CustomQueryEngine):
    """RAG String Query Engine."""

    retriever: BaseRetriever
    response_synthesizer: BaseSynthesizer
    llm: OpenAI
    qa_prompt: PromptTemplate

    def custom_query(self, query_str: str):
        nodes = self.retriever.retrieve(query_str)

        context_str = "\n\n".join([n.node.get_content() for n in nodes])
        response = self.llm.complete(
            qa_prompt.format(context_str=context_str, query_str=query_str)
        )

        return str(response)


llm = OpenAI(model="gpt-3.5-turbo")
synthesizer = get_response_synthesizer(response_mode="compact")



def aiResponse(input):  
    query_engine = RAGStringQueryEngine(
    retriever=retriever,
    response_synthesizer=synthesizer,
    llm=llm,
    qa_prompt=qa_prompt,
    )
    #query_engine = index.as_query_engine(streaming=True)
    #streaming_response = query_engine.query(input)
    #streaming_response.print_response_stream()

    response = query_engine.query(str(input))
    return response


