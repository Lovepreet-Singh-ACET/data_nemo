# from llama_index.embeddings import OpenAIEmbedding
# from llama_index.node_parser import SentenceSplitter
# from llama_index import ServiceContext
# from llama_index.llms import OpenAI
# from llama_index.vector_stores import MetadataFilters, ExactMatchFilter
# from llama_index.vector_stores.types import FilterCondition
# from llama_index.llms.base import ChatMessage
# import os 
# from dotenv import load_dotenv, dotenv_values

# load_dotenv()

# OPENAI_KEY = os.getenv("OPENAI_KEY")
# LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")

# CHUNK_SIZE=1024
# CHUNK_OVERLAP=204
# EMBED_MODEL="text-embedding-ada-002"
# MODEL="gpt-3.5-turbo"

# def get_service_context(with_llm:bool = True):
#     llm=None
#     if with_llm == True:
#         llm = OpenAI(model=MODEL,
#         #api_key = os.environ.get("OPENAI_API_KEY")
#         api_key = OPENAI_KEY)
#     embed_model = OpenAIEmbedding(model=EMBED_MODEL,
#                                         #api_key=os.environ.get("OPENAI_API_KEY")
#                                         api_key=OPENAI_KEY
#                                         )
    
#     node_parser = SentenceSplitter.from_defaults(
#             chunk_size=CHUNK_SIZE,
#             chunk_overlap=CHUNK_OVERLAP
#         )
#     return ServiceContext.from_defaults(llm= llm,embed_model=embed_model,node_parser=node_parser)

# def get_query_engine(index,metadata):    
#     filters = MetadataFilters(
#         filters=[ExactMatchFilter(key=key, value=value) for key,value in metadata.items()],
#         condition=FilterCondition.AND
#     )
#     query_engine = index.as_query_engine(filters = filters)
#     return query_engine

# def get_chat_history(history:dict,k:int):
#     if k==0:
#         return []
#     history = history[:-1]
#     if len(history)//2 >= k:
#         return [ChatMessage(role= messages["role"],content=messages["content"]) for messages in history[-k*2:]]
#     else:
#         return [ChatMessage(role= messages["role"],content=messages["content"]) for messages in history]