from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database configuration
    db_driver: str = "{ODBC Driver 17 for SQL Server}" # IMPORTANT: Use the exact driver name you installed (e.g., ODBC Driver 18 for SQL Server)
    db_server: str = "localhost" # Or your SQL Server IP/hostname/instance name (e.g., "YOUR_SERVER\SQLEXPRESS")
    db_name: str = "redclouds_erp_sqlserver" # The database name you created/will create in SQL Server
    db_port: Optional[int] = 1433 # Default SQL Server port, can be omitted if not explicitly specified and default is used
    db_pool_min: int = 2
    db_pool_max: int = 10
    # ChromaDB configuration
    chroma_persist_path: str = "./chroma_data"
    chroma_collection: str = "redclouds_erp_docs"
    
    # Embedding model configuration
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2" # Using the one that worked for you

    # LLM (Large Language Model) configuration
    # Using 'gemini-1.5-flash-latest' for general purpose, you can change to 'gemini-1.5-pro-latest' if preferred
    llm_model: str = "gemini-1.5-flash-latest" 
    llm_temperature: float = 0.2
    llm_num_ctx: int = 4096 # Context window for prompt, less relevant for some cloud APIs but good to keep
    
    # Gemini API Key (IMPORTANT: Replace 'YOUR_GEMINI_API_KEY_HERE' with your actual key)
    # For production, consider loading this from an environment variable for security:
    # `gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")`
    gemini_api_key: str = "AIzaSyCVaI9_tAScB75MHmIwgE6n_ikCONCCnnU" 

    # Chatbot behavior
    greeting_message: str = (
        "Hello! I'm RedClouds AI Assistant. I'm here to help with any questions "
        "about our ERP solutions and services. How can I assist you today?"
    )
    fallback_message: str = (
        "I'm sorry, I couldn't find specific information about that in our documentation. "
        "Would you like me to connect you with a human support agent?"
    )
    
    # Conversation settings
    conversation_timeout: int = 1800 # Seconds (30 minutes) for conversation expiry

settings = Settings()
