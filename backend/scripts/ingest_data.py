import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import os
import re
from pathlib import Path
import logging
from backend.app.config import settings
from typing import List, Optional, Dict
from datetime import datetime

# Configure logging for ingest_data.py
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def clean_text(text):
    """Enhanced text cleaning for document content."""
    if pd.isna(text):
        return None
    text = str(text).strip()
    if len(text) < 10:  # Increased minimum length to ensure meaningful snippets
        logger.debug(f"Skipping short text (length {len(text)}): '{text[:50]}...'")
        return None
    # **CRITICAL FIX HERE:** Allow letters, numbers, common punctuation, and spaces.
    # The previous regex was too restrictive.
    text = re.sub(r'[^a-zA-Z0-9\\s.,!?@#$%&*()\\-_+/=\\[\\]{}\\\'"]', '', text)
    # Normalize whitespace to single spaces
    text = re.sub(r'\\s+', ' ', text)
    return text

def load_data(data_path: Path):
    """Loads specified CSV data for ingestion."""
    datasets = {}
    expected_files = {
        "faqs": "redclouds_erp_faqs.csv"
    }
    
    for name, filename in expected_files.items():
        file_path = data_path / filename
        if not file_path.exists():
            logger.error(f"Required file not found: {file_path}. Please ensure it exists.")
            return {}
        
        try:
            df = pd.read_csv(file_path)
            if not df.empty:
                datasets[name] = df
                logger.info(f"Loaded {len(df)} records from {filename}.")
            else:
                logger.warning(f"File {filename} loaded but is empty. No data will be ingested for this source.")

        except Exception as e:
            logger.error(f"Error loading {filename}: {e}")
            return {}
    
    return datasets

def get_text_column(df_columns: List[str]) -> Optional[str]:
    """Dynamically find the most appropriate text column for FAQs."""
    if "Answer" in df_columns:
        return "Answer"
    elif "answer" in df_columns:
        return "answer"
    elif "Question" in df_columns:
        logger.warning("Using 'Question' column as primary text for FAQs. 'Answer' column is preferred for detailed content.")
        return "Question"
    
    logger.error(f"No suitable text column ('Answer' or 'Question') found in FAQ dataset. Available columns: {df_columns}.")
    return None

def create_metadata(row: pd.Series, source_name: str, text_col: str) -> Dict:
    """Create metadata dictionary for a document, excluding the main text column."""
    metadata = {
        "source": source_name,
        "ingested_at": datetime.now().isoformat()
    }
    for col in row.index:
        if col != text_col and pd.notna(row[col]):
            metadata[col] = str(row[col])
    return metadata

def main():
    logger.info("Starting RedClouds ERP FAQ data ingestion process...")
    try:
        chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_path)
        
        try:
            chroma_client.delete_collection(name=settings.chroma_collection)
            logger.info(f"Existing ChromaDB collection '{settings.chroma_collection}' deleted.")
        except Exception:
            logger.info(f"ChromaDB collection '{settings.chroma_collection}' did not exist or could not be deleted. Proceeding to create new one.")

        collection = chroma_client.get_or_create_collection(
            name=settings.chroma_collection,
            metadata={"description": "RedClouds ERP Customer Service FAQs"}
        )
        logger.info(f"ChromaDB collection '{settings.chroma_collection}' initialized for FAQs.")

        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        logger.info("SentenceTransformer embedding model loaded.")

        data_path = Path(__file__).parent.parent.parent / "data" 
        logger.info(f"Attempting to load data from: {data_path}")
        if not data_path.is_dir():
            logger.critical(f"Data directory not found at {data_path}. Please create it and place 'redclouds_erp_faqs.csv' inside.")
            return

        datasets = load_data(data_path)

        if not datasets:
            logger.error("No FAQ datasets were loaded. Data ingestion aborted.")
            return

        total_ingested_docs = 0
        for name, df in datasets.items():
            logger.info(f"Processing dataset: '{name}' (Expected: faqs)")
            
            text_column = get_text_column(df.columns.tolist())
            if not text_column:
                logger.error(f"Skipping dataset '{name}' due to missing essential text column.")
                continue
                
            df['clean_text'] = df[text_column].apply(clean_text)
            df = df[df['clean_text'].notna()]
            
            if len(df) == 0:
                logger.warning(f"No valid, cleaned text found in '{name}' dataset. Skipping ingestion for this source.")
                continue
            
            batch_size = 100
            for i in tqdm(range(0, len(df), batch_size), desc=f"Ingesting {name} data"):
                batch = df.iloc[i:i + batch_size]
                
                embeddings = model.encode(
                    batch['clean_text'].tolist(),
                    show_progress_bar=False,
                    batch_size=32,
                    convert_to_tensor=False
                ).tolist()

                metadatas = batch.apply(
                    lambda row: create_metadata(row, name, text_column),
                    axis=1
                ).tolist()
                
                ids = [f"{name}_{i+j}" for j in range(len(batch))]
                
                try:
                    collection.add(
                        ids=ids,
                        embeddings=embeddings,
                        documents=batch['clean_text'].tolist(),
                        metadatas=metadatas
                    )
                    total_ingested_docs += len(batch)
                    logger.debug(f"Added {len(batch)} documents from '{name}' in batch {i // batch_size + 1}.")
                except Exception as add_e:
                    logger.error(f"Error adding batch from '{name}' to ChromaDB: {add_e}")

        logger.info("\\n✅ Data ingestion complete!")
        final_count = collection.count()
        logger.info(f"ChromaDB collection '{settings.chroma_collection}' now contains {final_count} documents.")
        if final_count == 0:
            logger.error("WARNING: 0 documents ingested. Please verify your data file and cleaning logic.")
        
    except Exception as e:
        logger.critical(f"❌ Critical data ingestion failure: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
