from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader


def load_documents():

    docs=[]

    folder = Path(__file__).parent.parent / "documents"

    for pdf in folder.rglob("*.pdf"):

        loader=PyPDFLoader(str(pdf))

        docs.extend(loader.load())

    return docs