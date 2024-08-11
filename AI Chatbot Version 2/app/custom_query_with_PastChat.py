from llama_index.core.query_engine import CustomQueryEngine
from llama_index.core.retrievers import BaseRetriever
from llama_index.core import get_response_synthesizer
from llama_index.core.response_synthesizers import BaseSynthesizer
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Document
)
import os.path
import os
from enum import Enum
from llama_index.llms.openai import OpenAI
from llama_index.core import PromptTemplate
from pathlib import Path
import openai
from openai import OpenAI as openai_client
from openai.types.chat import ChatCompletion
from dotenv import load_dotenv

# Helper function to strip a substring from a string
def strip_whole_str(input_str: str, substr: str) -> str:
    return input_str.replace(substr, '')

# Load environment variables
env_path = Path("..") / ".env"
load_dotenv(dotenv_path=env_path)

# Ensure API key is set
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "Your KEY"  # Replace with your actual key
openai_client_instance = openai
embedding_model = openai_client(api_key=os.environ.get("OPENAI_API_KEY"))

# Load existing index from storage
PERSIST_DIR = "./storage"
storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
index = load_index_from_storage(storage_context)

# Combine existing index with new data
retriever = index.as_retriever()

# Chat History management
chat_history = []

def update_chat_history(role, message):
    '''
    :param role: The role of the message sender ("user" or "bot").
    :param message: The content of the message.
    '''
    chat_history.append({"role": role, "content": message})

def embed_chat_history(chat_history):
    global index, retriever  # Declare global variables at the start

    if isinstance(chat_history, list) and all(isinstance(message, dict) for message in chat_history):
        conversations = [Document(text=message['content']) for message in chat_history]

        # Insert new documents to the storage context
        for doc in conversations:
            index.storage_context.insert_document(doc)

        # Rebuild retriever if needed
        retriever = index.as_retriever()
    else:
        raise ValueError("chat_history must be a list of dictionaries with 'content' keys.")

# Define the QA prompt template
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

    def custom_query(self, query_str: str, past_chat_history: list):
        # Embed past chat history
        embed_chat_history(past_chat_history)

        # Retrieve relevant nodes based on the query
        nodes = self.retriever.retrieve(query_str)
        context_str = "\n\n".join([n.node.get_content() for n in nodes])

        # Generate response using the combined context
        response = self.llm.complete(
            qa_prompt.format(context_str=context_str, query_str=query_str)
        )

        return str(response)


# Initialize the LLM and synthesizer
llm = OpenAI(model="gpt-3.5-turbo")
synthesizer = get_response_synthesizer(response_mode="compact")

# aiResponse function with embedded chat history
def aiResponse(input, past_chat_history=[]):
    # Initialize query engine
    query_engine = RAGStringQueryEngine(
        retriever=retriever,
        response_synthesizer=synthesizer,
        llm=llm,
        qa_prompt=qa_prompt,
    )

    # Update chat history with user input
    update_chat_history("user", input)

    # Generate response
    response = query_engine.custom_query(str(input), past_chat_history)

    # Update chat history with the bot's response
    update_chat_history("bot", response)

    return response

# Relevance classification logic
class Relevance(Enum):
    KNOWN = "known"
    UNKNOWN = "unknown"
    IRRELEVANT = "irrelevant"

def classifyRelevance(input, retriever=retriever) -> Relevance:
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

    nodes = retriever.retrieve(input)
    context_str = "\n\n".join([n.node.get_content() for n in nodes])

    user_query = f"""<context>
{context_str}
</context>

Query: {input}

Output: """

    for i in range(3):
        response = get_openai_response_content(system_prompt=RELEVANCE_DETERMINATION_PROMPT, messages=[{"role": "user", "content": user_query}])
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
        return aiResponse(input, past_chat_history)
    elif relevance == Relevance.UNKNOWN:
        return get_unknown_response(input, past_chat_history, retriever)
    else:
        return "I'm sorry, I cannot answer that question as I am only here to provide information about UTMIST and AI/ML. If you think this is a mistake, please contact the UTMIST team."

def get_unknown_response(latest_user_input: str, past_chat_history=[], retriever=retriever) -> str:
    UNKNOWN_RESPONSE_PROMPT = """You are talking to a student as a representative of the University of Toronto Machine Intelligence Team (UTMIST), a student group dedicated to educating students about AI/ML through various events (conferences, workshops), academic programs, and other initiatives. 

Given the chat history, you must try to answer the user's latest inquiry using your knowledge of AI and nothing else. This means you must not use knowledge on any other topic other than UTMIST, AI, and/or machine learning.

If you cannot answer the user's query using your knowledge of AI/ML, you must tell the student that you don't know the answer.

<RULES>
1. DO NOT provide any information that is not related to AI/ML and/or computer science.
2. DO NOT make up information that you do not 100% know to be true.
</RULES>"""

    messages = list(past_chat_history)
    messages.append({"role": "user", "content": latest_user_input})

    return get_openai_response_content(system_prompt=UNKNOWN_RESPONSE_PROMPT, messages=messages)

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
