from dotenv import load_dotenv
load_dotenv()

import os
from pinecone_client import get_pinecone_client
from langchain.text_splitter import RecursiveCharacterTextSplitter # To split the text into smaller chunks
from langchain_openai import OpenAIEmbeddings # To create embeddings
from langchain_pinecone import PineconeVectorStore # To connect with the Vectorstore
from langchain_community.document_loaders import DirectoryLoader # To load files in a directory

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["PINECONE_API_KEY"] = os.getenv("PINECONE_API_KEY")

class Ingestor:
    def __init__(self) -> None:
        self.client = get_pinecone_client()

    def extract_data_from_dir(self,directory:str,metadata:dict)-> dict:
        reader = DirectoryLoader(directory)
        docs = {}
        for file in reader.iter_data():

            file_name = file[0].metadata['file_name']
            if file_name not in docs:
                docs[file_name] = []

            for page in file:
                doc = Document(text = page.text,extra_info={'Page_No':page.metadata['page_label'],
                                                            'File_Name':file_name,
                                                            'Year':metadata['Year'],
                                                            'Quarter':metadata['Quarter']})
                docs[file_name].append(doc)
            
        return docs
    
    def _get_index(self,index_name:str):

        if index_name not in self.client.list_indexes():
            self.client.create_index(
                index_name,
                dimension=1536,
                metric='cosine'
            )

        return self.client.Index(index_name)
    
    def ingest(self,index_name:str,docs:dict):

        pinecone_index = self._get_index(index_name)
        vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
        service_context = get_service_context(with_llm=False)

        index = VectorStoreIndex.from_vector_store(vector_store=vector_store,service_context=service_context)
        for file in list(docs.keys()):
            print(file)
            for page in docs[file]:
                index.insert(page)

    
if __name__ == "__main__":

    ingestor = Ingestor()
    print("Extracting Data ...")
    docs = ingestor.extract_data_from_dir(directory='Q4FY23',metadata={"Year":"FY23","Quarter":"Q4"})
    print("Ingesting Data ...")
    ingestor.ingest(index_name = 'earning-calls',docs=docs)

