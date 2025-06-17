# main.py - Version 1.5 (Added first_question to user conversations)
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from backend.app.models import ChatRequest, ChatResponse, ConversationState, SourceDocument
from backend.app.rag import ERPChatbot
from backend.app.database import db_manager
from backend.app.config import settings
import logging
import json
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any

# Configure logging for the entire application
logging.basicConfig(
    level=logging.INFO, # Set to INFO for production, DEBUG for more detailed development logs
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RedClouds ERP AI Chatbot",
    version="1.0.0",
    description="An intelligent customer service assistant for RedClouds ICT Solutions."
)
chatbot = ERPChatbot() # Instantiate the chatbot

# Middleware setup
app.add_middleware(GZipMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1234",
        "http://127.0.0.1:1234",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "http://localhost:5174",  # Add this line
        "*",  # Keep this as fallback
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
active_conversations: Dict[str, ConversationState] = {}

@app.on_event("startup")
async def startup_event():
    """Handles startup tasks like DB connection, chatbot warmup, and conversation cleanup."""
    logger.info("Application startup initiated.")
    try:
        await db_manager.connect()
        logger.info("✅ Database connection pool established.")
        
        # Warm up the chatbot to pre-load models and collections
        start_time = time.time()
        # Send a dummy query to trigger initialization within ERPChatbot
        _ = await chatbot.query("system warm-up", user_id="system_warmup", conversation_id=None) 
        logger.info(f"Chatbot warmed up in {time.time() - start_time:.2f}s.")
        
        # Perform initial cleanup of expired conversations
        await _cleanup_conversations()
        logger.info("Initial conversation cleanup completed.")
        
        logger.info("Application startup complete.")
    except Exception as e:
        logger.critical(f"❌ Application startup failed: {e}", exc_info=True)
        sys.exit(1)

@app.post("/chat", response_model=ChatResponse, summary="Process a user's chat message")
async def chat(request: ChatRequest):
    """
    Handles incoming chat requests, processes them through the RAG pipeline,
    and returns a structured response.
    """
    start_time = time.time()
    logger.info(f"Received chat request from User ID '{request.user_id}' (Conv ID: {request.conversation_id}): '{request.question[:70]}...'")
    
    # Retrieve or create conversation state
    conversation = await _get_conversation(request.user_id, request.conversation_id)
    
    try:
        result = await chatbot.query(
            question=request.question,
            user_id=request.user_id,
            conversation_id=conversation.conversation_id
        )
        
        # Update conversation's last interaction time in memory and DB
        conversation.last_interaction = datetime.now()
        active_conversations[conversation.conversation_id] = conversation
        await db_manager.execute_operation(
            "UPDATE conversations SET context = ?, updated_at = GETDATE() WHERE conversation_id = ?", # FIXED: Added context = ? and GETDATE()
            [json.dumps(conversation.context), conversation.conversation_id]
        )
        logger.debug(f"Conversation '{conversation.conversation_id}' updated in DB.")

        # Prepare sources for database logging (ensure they are serializable)
        sources_for_db: List[Dict[str, Any]] = []
        if result.get("source_documents"):
            for doc in result["source_documents"]:
                if isinstance(doc, SourceDocument):
                    sources_for_db.append(doc.model_dump())
                else:
                    sources_for_db.append(doc)
        
        # Log chat interaction to database
        await db_manager.execute_operation(
            """INSERT INTO chat_history 
            (conversation_id, user_id, question, response, sources) 
            VALUES (?, ?, ?, ?, ?)""", # FIXED: Changed $N to ?
            [
                conversation.conversation_id,
                request.user_id,
                request.question,
                result["result"],
                json.dumps(sources_for_db) # Serialize sources to JSON string
            ]
        )
        logger.debug(f"Chat history logged for conversation '{conversation.conversation_id}'.")
        
        # Construct and return the ChatResponse
        response_data = {
            "response": result["result"],
            "sources": result.get("source_documents", []),
            "suggested_questions": result.get("suggested_questions", []),
            "timestamp": datetime.now(),
            "conversation_id": conversation.conversation_id 
        }
        response = ChatResponse(**response_data) 

        logger.info(f"Processed chat request for '{request.user_id}' in {time.time() - start_time:.2f}s.")
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat request for user '{request.user_id}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="I apologize, an unexpected error occurred. Our team has been notified. Please try again shortly."
        )

@app.get("/user_conversations/{user_id}", summary="Retrieve a list of all conversations for a user")
async def get_user_conversations(user_id: str):
    logger.info(f"Fetching conversation list for user: '{user_id}'.")
    try:
        conversations_raw = await db_manager.execute_query(
            """SELECT 
                c.conversation_id, 
                c.created_at, 
                c.updated_at, 
                c.context,
                (SELECT TOP 1 question FROM chat_history WHERE conversation_id = c.conversation_id ORDER BY timestamp ASC) AS first_question
            FROM conversations c
            WHERE c.user_id = ? 
            ORDER BY c.updated_at DESC""", 
            [user_id]
        )
        
        conversations = []
        # Accessing elements by index because aioodbc's fetchall() typically returns tuples by default
        # The order corresponds to the SELECT query: conversation_id, created_at, updated_at, context, first_question
        for conv_data in conversations_raw:
            processed_conv = {
                "conversation_id": conv_data[0], 
                "created_at": conv_data[1].isoformat() if isinstance(conv_data[1], datetime) else conv_data[1], 
                "updated_at": conv_data[2].isoformat() if isinstance(conv_data[2], datetime) else conv_data[2], 
                "context": json.loads(conv_data[3]) if conv_data[3] else {},
                "first_question": conv_data[4] # New: Index 4 for first_question
            }
            conversations.append(processed_conv)

        logger.info(f"Retrieved {len(conversations)} conversations for user '{user_id}'.")
        return {"conversations": conversations}
    except Exception as e:
        logger.error(f"Failed to fetch conversation list for user '{user_id}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation list.")


@app.get("/conversation/{conversation_id}", response_model=Dict[str, List[Dict[str, Any]]], summary="Retrieve chat history for a conversation")
async def get_conversation(conversation_id: str):
    """Retrieves the full chat history for a given conversation ID."""
    logger.info(f"Fetching chat history for ID: '{conversation_id}'.")
    try:
        records = await db_manager.execute_query(
            """SELECT question, response, sources, timestamp 
            FROM chat_history 
            WHERE conversation_id = ? 
            ORDER BY timestamp ASC""", 
            [conversation_id]
        )
        
        processed_records = []
        # Accessing elements by index for chat_history: question, response, sources, timestamp
        for record in records:
            sources_data = record[2] # Index 2 for sources
            if isinstance(sources_data, str):
                try:
                    sources_data = json.loads(sources_data)
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode JSON sources for record: {record}")
                    sources_data = []
            if sources_data is None:
                sources_data = []
            sources_list = [SourceDocument(**s) if isinstance(s, dict) else s for s in sources_data]
            
            processed_records.append({
                "question": record[0], # Index 0 for question
                "response": record[1], # Index 1 for response
                "sources": sources_list,
                "timestamp": record[3] # Index 3 for timestamp
            })

        logger.info(f"Retrieved {len(processed_records)} messages for conversation '{conversation_id}'.")
        return {"messages": processed_records}
    except Exception as e:
        logger.error(f"Failed to fetch chat history for '{conversation_id}': {e}", exc_info=True)
        raise HTTPException(status_code=404, detail="Conversation not found or an error occurred.")

async def _get_conversation(user_id: str, conversation_id: Optional[str]) -> ConversationState:
    """
    Manages and retrieves the conversation state for a user.
    If conversation_id is provided, attempts to load it.
    If not, attempts to load the most recent conversation for the user.
    Otherwise, creates a new one.
    """
    await _cleanup_conversations() # Perform cleanup before looking up/creating

    # 1. Check in-memory active_conversations cache first
    if conversation_id and conversation_id in active_conversations:
        conv = active_conversations[conversation_id]
        if conv.user_id == user_id: 
            logger.debug(f"Found active conversation '{conversation_id}' in memory for user '{user_id}'.")
            return conv
        else:
            logger.warning(f"Conversation ID '{conversation_id}' found in memory but belongs to different user. Ignoring.")

    # 2. Try to load specific conversation_id from database if provided
    if conversation_id:
        try:
            db_conv_records = await db_manager.execute_query(
                "SELECT conversation_id, user_id, context, created_at, updated_at FROM conversations WHERE conversation_id = ?", 
                [conversation_id]
            )
            if db_conv_records:
                conv_data = db_conv_records[0]
                # Accessing elements by index: conversation_id, user_id, context, created_at, updated_at
                conversation = ConversationState(
                    conversation_id=conv_data[0],
                    user_id=conv_data[1],
                    context=json.loads(conv_data[2]) if conv_data[2] else {}, 
                    last_interaction=conv_data[4]
                )
                active_conversations[conversation.conversation_id] = conversation
                logger.debug(f"Loaded conversation '{conversation_id}' from database for user '{user_id}'.")
                return conversation
            else:
                logger.warning(f"Explicit conversation_id '{conversation_id}' not found in database for user '{user_id}'.")
        except Exception as e:
            logger.error(f"Error loading explicit conversation '{conversation_id}' from DB for user '{user_id}': {e}", exc_info=True)

    try:
        recent_conv_records = await db_manager.execute_query(
            "SELECT conversation_id, user_id, context, created_at, updated_at FROM conversations WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1", 
            [user_id]
        )
        if recent_conv_records:
            conv_data = recent_conv_records[0]
            # Accessing elements by index: conversation_id, user_id, context, created_at, updated_at
            conversation = ConversationState(
                conversation_id=conv_data[0],
                user_id=conv_data[1],
                context=json.loads(conv_data[2]) if conv_data[2] else {}, 
                last_interaction=conv_data[4]
            )
            active_conversations[conversation.conversation_id] = conversation
            logger.info(f"Loaded most recent conversation '{conversation.conversation_id}' for user '{user_id}'.")
            return conversation
        else:
            logger.info(f"No existing conversations found for user '{user_id}'. Creating a new one.")
    except Exception as e:
        logger.error(f"Error loading most recent conversation for user '{user_id}': {e}", exc_info=True)

    new_id = f"conv_{int(time.time())}_{user_id[:8]}"
    conversation = ConversationState(
        conversation_id=new_id,
        user_id=user_id,
        context={}
    )
    
    try:
        await db_manager.execute_operation(
            """INSERT INTO conversations 
            (conversation_id, user_id, context) 
            VALUES (?, ?, ?)""", 
            [new_id, user_id, json.dumps(conversation.context)]
        )
        logger.info(f"Successfully created new conversation record: '{new_id}' for user '{user_id}'.")
    except Exception as e:
        if "duplicate key value violates unique constraint" in str(e):
            logger.warning(f"Attempted to create duplicate conversation ID '{new_id}'. Assuming it was created by another concurrent request and proceeding.")
        else:
            logger.error(f"Failed to create new conversation record in DB for '{user_id}': {e}", exc_info=True)
    
    active_conversations[new_id] = conversation
    return conversation

async def _cleanup_conversations():
    """Cleans up expired conversations from in-memory cache and updates their timestamps in the database."""
    logger.debug("Initiating conversation cleanup...")
    try:
        expiry_time = datetime.now() - timedelta(seconds=settings.conversation_timeout)
        
        expired_in_memory = [
            conv_id for conv_id, conv in active_conversations.items()
            if conv.last_interaction < expiry_time
        ]
        for conv_id in expired_in_memory:
            del active_conversations[conv_id]
            logger.debug(f"Removed expired conversation '{conv_id}' from in-memory cache.")
        
        await db_manager.execute_operation(
            """UPDATE conversations 
            SET updated_at = GETDATE() 
            WHERE updated_at < ?""", 
            [expiry_time]
        )
        logger.debug("Database conversation timestamps refreshed for old conversations.")
    except Exception as e:
        logger.error(f"❌ Conversation cleanup failed: {e}", exc_info=True)

@app.on_event("shutdown")
async def shutdown_event():
    """Handles application shutdown tasks like closing DB connection."""
    logger.info("Application shutdown initiated.")
    try:
        await db_manager.disconnect() 
        logger.info("✅ Database connection pool closed.")
    except Exception as e:
        logger.error(f"❌ Error during database connection close on shutdown: {e}", exc_info=True)
    logger.info("Application shutdown complete.")

def handle_signal(signum, frame):
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        workers=1,
        log_level="info",
        timeout_keep_alive=60
    )