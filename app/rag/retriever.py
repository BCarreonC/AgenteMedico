from app.rag.vectordb import db

retriever=db.as_retriever(

    search_kwargs={

        "k":4

    }

)