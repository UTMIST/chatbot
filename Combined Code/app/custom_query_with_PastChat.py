from llama_index.core.query_engine import CustomQueryEngine
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore
from llama_index.core import get_response_synthesizer
from llama_index.core.response_synthesizers import BaseSynthesizer
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Document,
)
import os.path
import os
from enum import Enum
# Option 2: return a string (we use a raw LLM call for illustration)

from llama_index.llms.openai import OpenAI
from llama_index.core import PromptTemplate
from pathlib import Path
import openai
from openai import OpenAI as openai_client
from openai.types.chat import ChatCompletion
from llama_index.core.extractors import SummaryExtractor

from dotenv import load_dotenv

def strip_whole_str(input_str: str, substr: str) -> str:
    """
    Removes all occurrences of a specified substring from the input string.

    :param input_str: The original string.
    :param substr: The substring to remove.
    :return: The modified string with the specified substring removed.
    """
    return input_str.replace(substr, '')

env_path = Path("..") / ".env"
load_dotenv(dotenv_path=env_path)

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "Your Key"
openai_client_instance = openai
embedding_model = openai_client(api_key=os.environ.get("OPENAI_API_KEY"))

# load existing index from storage
PERSIST_DIR = "./storage"
storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
index = load_index_from_storage(storage_context)

#Combine existing index with new index
retriever = index.as_retriever()

#Chat History management
chat_history = []

SUMMARY_EXTRACTOR = SummaryExtractor(summaries=["prev", "self", "next"], llm=embedding_model)

def update_chat_history(role, message):
    '''
    :param role: The role of the message sender ("user" or "bot").
    :param message: The content of the message.
    '''
    chat_history.append({"role":role, "content": message})

def embed_chat_history(chat_history : list[dict]) -> VectorStoreIndex:
    conversations = [Document(text=message['content']) for message in chat_history]
    index = VectorStoreIndex.from_documents(conversations, embedding_model = embedding_model)
    return index

def _retrieve_context_for_query(query_str : str, past_chat_history : list[dict], chat_depth_for_retrieval = 2) -> list[NodeWithScore]:
    
    retrieved_knowledge = set()
    returned_nodes = []

    def append_to_returned_nodes(nodes : list[NodeWithScore]):
        for node in nodes:
            if node.get_content() in retrieved_knowledge:
                continue
            returned_nodes.append(node)
            retrieved_knowledge.add(node.get_content)

    for i in range(chat_depth_for_retrieval):
        if len(past_chat_history) < i:
            break

        chat = past_chat_history[-i]        
        nodes = retriever.retrieve(chat['content'])
        append_to_returned_nodes(nodes)

    nodes = retriever.retrieve(query_str)
    append_to_returned_nodes(nodes)

    return returned_nodes







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

    # Custom query that incorporates chat history
    def custom_query(self, query_str: str, past_chat_history: list[dict]):
        # NOTE: Embedding past chat history 
        # embed_chat_history(past_chat_history)

        # Retrieve past conversations from the vector database

        # summarize the past chat
        # past_nodes = self.retriever.retrieve(query_str)
        # past_context_str = "\n\n".join([n.node.get_content() for n in past_nodes])
        # Address current context
        nodes = _retrieve_context_for_query(query_str, past_chat_history)
        if not nodes:  # If no nodes are found, log the query as unanswered
            with open("unanswered_queries.txt", "a") as f:
                f.write(f"{query_str}\n")

        context_str = "\n\n".join([n.node.get_content() for n in nodes])

        # Combine past and current contexts
        combined_context = f'{context_str}'


        response = self.llm.complete(
            qa_prompt.format(context_str=combined_context, query_str=query_str)
        )

        return str(response)



llm = OpenAI(model="gpt-3.5-turbo")
synthesizer = get_response_synthesizer(response_mode="compact")

#aiResponse combiend with past_chat_history
def aiResponse(input, past_chat_history=[]):
    query_engine = RAGStringQueryEngine(
        retriever=retriever,
        response_synthesizer=synthesizer,
        llm=llm,
        qa_prompt=qa_prompt,
    )
    
    response = query_engine.custom_query(str(input), past_chat_history)
    return response

class Relevance(Enum):
    KNOWN = "known"
    UNKNOWN = "unknown"
    IRRELEVANT = "irrelevant"


def classifyRelevance(input, retriever=retriever) -> Relevance:
    """
    Classifies how relevant a particular user input is to UTMIST.

    :param input: The user input to classify.
    :return: ``Relevance.known`` if the input is known, ``Relevance.unknown`` if the input is unknown, and ``Relevance.irrelevant`` if the input is irrelevant.
    """

    RELEVANCE_DETERMINATION_PROMPT = """You are talking to a user as a representative of a club called the University of Toronto Machine Intelligence Team (UTMIST). 

Your job is to determine whether the user's query is relevant to any of the following, and output one of the responses according to the possible scenarios.

1. AI and machine learning related questions
2. UTMIST club information and events

Note that when the user refers to "you" or "your", they are referring to UTMIST.    

<possible scenarios>

1. SCENARIO: If the query seems relevant to UTMIST (i.e. events or general info) or AI and the "context" explicitly contains information about the query; OUTPUT: "known"
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

### END OF EXAMPLES ###"""

    nodes = _retrieve_context_for_query(input, chat_history)

    context_str = "\n\n".join([n.node.get_content() for n in nodes])

    user_query = f"""<context>
{context_str}
</context>

Query: {input}

Output: """

    # Retry up to 3 times in case GPT returns wrong value.
    for i in range(3):

        response: str = get_openai_response_content(system_prompt=RELEVANCE_DETERMINATION_PROMPT, model="gpt-3.5-turbo",
                                                    messages=[{"role": "user", "content": user_query}])
        
        response = strip_whole_str(response, "Output:").strip()
        try:
            return Relevance(response)
        except ValueError:
            print("value error: " + response)
            pass

    return Relevance.UNKNOWN


def get_response_with_relevance(input: str, past_chat_history=[], retriever=retriever) -> str:
    relevance = classifyRelevance(input, retriever=retriever)

    print("relevance: " + str(relevance))
    if relevance == Relevance.KNOWN:
        return aiResponse(input)
    elif relevance == Relevance.UNKNOWN:
        return get_unknown_response(input, past_chat_history, retriever)
    else:
        return "I'm sorry, I cannot answer that question as I am only here to provide information about UTMIST and AI/ML. If you think this is a mistake, please contact the UTMIST team."


def get_unknown_response(latest_user_input: str, past_chat_history=[], retriever=retriever) -> str:
    """
    Returns a response when the input is classified as irrelevant.

    :param input: The user input to respond to.
    :param past_chat_history: The chat history to consider when responding.
    :return: A response to the user input.
    """

    UNKNOWN_RESPONSE_PROMPT = """You are talking to a student as a representative of the University of Toronto Machine Intelligence Team (UTMIST), a student group dedicated to educating students about AI/ML through various events (conferences, workshops), academic programs, and other initiatives. 

Given the chat history, you must try to answer the user's latest inquiry using your knowledge of AI and nothing else. This means you must not use knowledge on any other topic other than UTMIST, AI, and/or machine learning.

If you cannot answer the user's query using your knowledge of AI/ML, you must tell the student that you don't know the answer.

<RULES>
1. DO NOT provide any information that is not related to AI/ML and/or computer science.
2. DO NOT make up information that you do not 100% know to be true.
</RULES>"""

    messages = list(past_chat_history)
    messages.append({"role": "user", "content": latest_user_input})

    return get_openai_response_content(system_prompt=UNKNOWN_RESPONSE_PROMPT, model="gpt-3.5-turbo", messages=messages)


def get_openai_response_content(system_prompt="", messages=[], model="gpt-3.5-turbo", **kwargs) -> str:
    assert messages or system_prompt, "prompt or messages must be provided"

    if system_prompt:
        messages.insert(0, {"role": "system", "content": system_prompt})

    response = _get_openai_response(messages=messages, model=model, **kwargs)
    return _extract_openai_response_content(response)


def _extract_openai_response_content(response: ChatCompletion) -> str:
    assert isinstance(response, ChatCompletion), "response must be a ChatCompletion object"
    return response.choices[0].message.content


def _get_openai_response(messages=[], model="gpt-3.5-turbo", **kwargs) -> ChatCompletion:
    response: ChatCompletion = openai_client_instance.chat.completions.create(model=model, messages=messages, **kwargs)
    return response
