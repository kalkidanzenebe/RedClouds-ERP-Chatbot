from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Optional
from datetime import datetime

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User's question")
    user_id: str = Field(..., min_length=1, description="Unique user identifier")
    conversation_id: Optional[str] = Field(None, description="Conversation session ID")

class SourceDocument(BaseModel):
    source: str = Field(..., description="Document source name")
    content: str = Field(..., description="Relevant content excerpt")
    details: Dict[str, str] = Field(default_factory=dict, description="Additional metadata")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Chatbot's response")
    sources: List[SourceDocument] = Field(default_factory=list, description="Supporting documents")
    suggested_questions: List[str] = Field(default_factory=list, description="Follow-up questions")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response time")
    conversation_id: Optional[str] = Field(None, description="The ID of the current conversation")

class ERPDocument(BaseModel):
    text: str = Field(..., description="Document content")
    metadata: Dict = Field(default_factory=dict, description="Document metadata")
    model_config = ConfigDict(arbitrary_types_allowed=True)

class ConversationState(BaseModel):
    conversation_id: str
    user_id: str
    context: Dict[str, str] = Field(default_factory=dict, description="Context for ongoing conversation")
    last_interaction: datetime = Field(default_factory=datetime.now, description="Timestamp of the last interaction")
