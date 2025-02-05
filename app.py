import os

from scripts.database import MongoDB
from scripts.rag_implementation import rag_pipeline
from uuid import uuid4
from streamlit_feedback import streamlit_feedback
import pandas as pd
import streamlit as st
import logging
import sys
import json
import pymongo
from datetime import datetime, timezone
from langchain_openai import ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings

# Index Name
index_name = "earning-calls-euclidean"
os.environ['OPENAI_API_KEY'] = st.secrets["OPENAI"]['OPENAI_KEY']
os.environ['PINECONE_API_KEY'] = st.secrets["PINECONE"]['PINECONE_API_KEY']
# Initialize connection.
# Uses st.cache_resource to only run once.
@st.cache_resource
def init_connection():
    return pymongo.MongoClient(st.secrets["mongo"]['uri'])

client = init_connection()

embeddings = OpenAIEmbeddings()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger()

if not logger.handlers:
    logger.addHandler(logging.StreamHandler(stream=sys.stdout))

with open("mappings.json", 'r') as json_file:
    mappings = json.load(json_file)

# Initialize MongoDB instance
mongo = MongoDB(client, st.secrets["mongo"]['database'], st.secrets["mongo"]["collection_name"])

st.title("Information Extraction Example from Earnigns Calls of NIFTY 50 Universe")
        
@st.cache_resource(show_spinner=False)
def load_data():
    index = None
    try:
        # Index Name
        index_name = "earning-calls-euclidean"
        index = PineconeVectorStore(index_name=index_name, embedding=embeddings, pinecone_api_key=st.secrets["PINECONE"]['PINECONE_API_KEY'])
        logging.info(f"Loaded index: {index_name}")
    except Exception as e:
        logging.info(f"Could not load index: {e}")
        
    return index

# setting question state to false
if 'question_state' not in st.session_state:
    st.session_state.question_state = False

# Initializing index
if "index" not in st.session_state.keys():
	st.session_state.index = load_data()

# Metadata from user
with st.sidebar:
    year = st.selectbox("Select Year",list(mappings.keys()))
    quarter = st.selectbox("Select Quarter",list(mappings[year].keys()))
    file_name = st.selectbox("Select file", mappings[year][quarter])
	
metadata={"File_Name":file_name+".pdf","Year":year,"Quarter":quarter}
# Initializing session metadata
if "metadata" not in st.session_state.keys():
    st.session_state.metadata = metadata

# Initializing Query Engine
if "query_engine" not in st.session_state.keys():
    new_keys = {'File_Name': 'filename', 'Year': 'year', 'Quarter': 'quarter'}
    new_dict = {new_keys.get(k, k): v for k, v in st.session_state.metadata.items()}
    # st.session_state.query_engine = get_query_engine(index=st.session_state.index,metadata=st.session_state.metadata)
    st.session_state.retriever = st.session_state.index.as_retriever(search_kwargs={"filter": new_dict, "k": 4})
    st.session_state.rag_pipeline, st.session_state.chat_template = rag_pipeline(llm=llm, retriver=st.session_state.retriever)

# Updating filters and chat engine if metadata is updated and updating session metadata also
if st.session_state.metadata != metadata:

    st.session_state.metadata = metadata
    new_keys = {'File_Name': 'filename', 'Year': 'year', 'Quarter': 'quarter'}
    new_dict = {new_keys.get(k, k): v for k, v in st.session_state.metadata.items()}

    # st.session_state.query_engine = get_query_engine(index=st.session_state.index,metadata=st.session_state.metadata)
    st.session_state.retriever = st.session_state.index.as_retriever(search_kwargs={"filter": new_dict, "k": 4})
    st.session_state.rag_pipeline, st.session_state.chat_template = rag_pipeline(llm=llm, retriver=st.session_state.retriever)

# Initialize session state
if "messages" not in st.session_state.keys():
    st.session_state.messages = []

# initializing a unique key for feedback
if 'fbk' not in st.session_state:
    st.session_state.fbk = str(uuid4())

# setting question state to false
if 'current_prompt' not in st.session_state:
    st.session_state.current_prompt = None

def display_answer():
    # Display chat
    for message in st.session_state.messages:
        with st.chat_message("user"):
            st.write(message["question"])
        with st.chat_message("assistant"):
            st.write(message["answer"].replace("$", "\$"))

def create_answer(question, answer=None):
    """Add question/answer to history."""
    # Do not save to history if question is None.
    # We reach this because streamlit reruns to get the feedback.
    if question is None:
        return
    
    message_id = str(uuid4())
    st.session_state.messages.append({
        "question": question,
        "answer": answer,
        "message_id": message_id,
    })


def fbcb(response):
    """Update the history with feedback and add feedback to database.
    
    The question and answer are already saved in history.
    Now we will add the feedback in that history entry and to the feedback database.
    """
    last_entry = st.session_state.messages[-1]  # get the last entry
    last_entry.update({'feedback': response})  # update the last entry
    st.session_state.messages[-1] = last_entry  # replace the last entry
    last_entry.update({"timestamp": datetime.now(timezone.utc)}) # added timestamp to the document inserted
    last_entry.update({"prompt": st.session_state.current_prompt}) # added the prompt
    st.session_state.current_prompt = None # reset the prompt to None once used
    last_entry.update({"metadata": st.session_state.metadata}) # adding metadata of the file in consideration
    mongo.insert_document(document=last_entry)
    st.session_state.fbk = str(uuid4())
    st.rerun()

def return_answer(prompt):
    response = st.session_state.rag_pipeline.invoke(prompt)
    return response

prompt = st.chat_input("Your question")
if prompt:
    # We need this because of feedback. That question above
    # is a stopper. If user hits the feedback button, streamlit
    # reruns the code from top and we cannot enter back because
    # of that chat_input.
    st.session_state.question_state = True

# We are now free because st.session_state.question_state is True.
# But there are consequences. We will have to handle
# the double runs of create_answer() and display_answer()
# just to get the user feedback. 
if st.session_state.question_state:

    if prompt is None:
         display_answer()
    else:
        # Displaying user prompt in frontend
        with st.chat_message("user"):
            st.write(prompt)

        with st.spinner(text="Thinking ..."):
            with st.chat_message("assistant"):
                logging.info(prompt)
                
                # Generating Response            
                try:
                    # response_full = rag_chain_with_source.invoke(prompt)
                    response_full = return_answer(prompt)
                    print("RESPONSE:", response_full)
                    response = response_full.get('answer')
                    if "Rail" not in response_full.get('answer'):
                        st.session_state.current_prompt = st.session_state.chat_template.format(
                                                                            context_str="\n\n".join(doc.page_content for doc in response_full.get('context_str')),
                                                                            query_str = prompt)
                    else:
                        st.session_state.current_prompt = st.session_state.chat_template.format(
                                                                            context_str="",
                                                                            query_str = prompt)
                except Exception as e:
                    response = str(e)
                    source_nodes = dict()
                print("RESPONSE:", response)
                if "Rail" in response:
                    pass
                else:
                    meta_data_for_user_context = {}
                    for index, item in enumerate(response_full.get('context_str')):
                        meta_data_for_user_context[f'Retrived_Chunk_{index+1}'] = item.metadata
                        meta_data_for_user_context[f'Retrived_Chunk_{index+1}'].update({"source": item.page_content})
                        
                        # showing metadata for user context
                        st.dataframe(pd.Series(meta_data_for_user_context[f'Retrived_Chunk_{index+1}']), use_container_width=True, column_config={1: "Retrived Chunk"})

                st.write(response.replace("$", "\$"))

                create_answer(question=prompt, answer=response)
    
    if st.session_state.get("messages") and len(st.session_state.get("messages")) > 0:
        if not st.session_state.get('messages')[-1].get("feedback"):
            streamlit_feedback(
                feedback_type="thumbs",
                optional_text_label="[Optional]",
                align="flex-start",
                key=st.session_state.fbk,
                on_submit=fbcb
            )
