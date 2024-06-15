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
from enum import Enum
# Option 2: return a string (we use a raw LLM call for illustration)

from llama_index.llms.openai import OpenAI
from llama_index.core import PromptTemplate
from pathlib import Path
from openai import OpenAI as openai_client
from openai.types.chat import ChatCompletion



from dotenv import load_dotenv

env_path = Path("..") / ".env"
load_dotenv(dotenv_path=env_path)

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "Your-OpenAI-API-Key"

openai_client_instance = openai_client(api_key = os.environ.get("OPENAI_API_KEY"))

#load documents
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


class Relevance(Enum):
    known = "known"
    unknown = "unknown"
    irrelevant = "irrelevant"

def classifyRelevance(input, retriever = retriever):

    RELEVANCE_DETERMINATION_PROMPT = """You are talking to a user as a representative of a club called the University of Toronto Machine Intelligence Team (UTMIST). 
    
Your job is to determine whether the user's query is relevant to any of the following, and output one of the responses according to the possible scenarios.

1. AI and machine learning related questions
2. UTMIST club information and events

<context>
{context_str}
</context>

<possible scenarios>

1. SCENARIO: If the query seems relevant to UTMIST or AI and the "context" explicitly contains information about the query; OUTPUT: "known"
2. SCENARIO: If the query is about GENERAL knowledge in AI/ML but NOT about UTMIST; OUTPUT: "known"
3. SCENARIO: If the query seems relevant to UTMIST or AI but the information is not in "context" AND it is NOT GENERAL knowledge about AI/ML; OUTPUT: "unknown"
4. SCENARIO: If the query is completely irrelevant to the criteria above; OUTPUT: "irrelevant"

</possible scenarios>

Example A:

<context>
UTMIST is a club to help students learn about AI
</context>

Query: When was UTMIST founded?

Output: unknown

Example B:

<context>
The GenAI conference will be on April 30, 2024
</context>

Query: What do you know about history?

Output: irrelevant

Example C:

<context>
The GenAI conference will help students learn about AI.
</context>

Query: What is the GenAI conference?

Output: relevant

### END OF EXAMPLES ###

Query: {query_str}"""

    nodes = retriever.retrieve(input)

    context_str = "\n\n".join([n.node.get_content() for n in nodes])

    formatted_relevance_prompt = RELEVANCE_DETERMINATION_PROMPT.format(context_str = context_str, query_str = input)    

    response : ChatCompletion = openai_client_instance.chat.completions.create(model = "gpt-3.5-turbo", messages=[{"role" : "system", "content" : formatted_relevance_prompt}])

    return response.choices[0].message.content.strip("Output:").strip()

