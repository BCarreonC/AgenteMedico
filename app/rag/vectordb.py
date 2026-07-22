from langchain_chroma import Chroma

from app.rag.embeddings import embeddings

db=Chroma(

    collection_name="medical",

    embedding_function=embeddings,

    persist_directory="./chroma"
)