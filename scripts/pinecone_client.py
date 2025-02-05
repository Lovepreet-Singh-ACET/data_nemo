import os
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

def get_pinecone_client():

    pc = Pinecone(api_key=os.getenv["PINECONE_API_KEY"])

    return pc