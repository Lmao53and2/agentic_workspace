import os
import tempfile
from typing import List, Dict
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb
from agno.document.reader.pdf_reader import PDFReader
from agno.document.reader.csv_reader import CSVReader
from agno.document.chunking.recursive_character import RecursiveCharacterChunker

# Path for persistence
app_data = os.path.join(os.path.expanduser("~"), ".myapp")
os.makedirs(app_data, exist_ok=True)
LANCE_URI = os.path.join(app_data, "lancedb")

class RagService:
    def __init__(self):
        self.knowledge = Knowledge(
            vector_db=LanceDb(
                table_name="user_documents",
                uri=LANCE_URI,
            ),
            # Default chunker
            chunker=RecursiveCharacterChunker(chunk_size=1000, chunk_overlap=100),
        )

    def ingest_files(self, files: List[Dict[str, any]]):
        """
        Ingest files into the vector database.
        files: List of {"name": str, "data": bytes}
        """
        all_docs = []
        for file_info in files:
            name = file_info["name"]
            data = file_info["data"]
            
            # Save to temp file to use Agno readers
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(name)[1]) as tmp:
                tmp.write(data)
                tmp_path = tmp.name

            try:
                if name.lower().endswith(".pdf"):
                    reader = PDFReader()
                    docs = reader.read(tmp_path)
                elif name.lower().endswith(".csv"):
                    reader = CSVReader()
                    docs = reader.read(tmp_path)
                else:
                    continue
                
                for doc in docs:
                    doc.meta_data["filename"] = name
                
                all_docs.extend(docs)
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        if all_docs:
            self.knowledge.load_documents(all_docs, upsert=True)
            return True
        return False

    def clear_context(self):
        """Clear all documents from the knowledge base."""
        # LanceDB specific clear
        import lancedb
        db = lancedb.connect(LANCE_URI)
        if "user_documents" in db.table_names():
            db.drop_table("user_documents")
        # Re-initialize the knowledge base table structure
        self.knowledge.vector_db.create()
        return True

    def get_uploaded_files(self):
        """Return a list of unique filenames currently in the vector DB."""
        # This is a bit complex with LanceDB directly, 
        # but for simplicity we'll just track them in a session list in the bridge.
        pass
