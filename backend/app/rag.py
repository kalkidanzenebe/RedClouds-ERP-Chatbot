from langchain_community.embeddings import HuggingFaceEmbeddings
from typing import List, Dict, Any, Optional
import chromadb
import time
import logging
import re
from datetime import datetime
from backend.app.config import settings
from backend.app.models import SourceDocument
import json
import httpx # For making asynchronous HTTP requests

# Configure logging for rag.py. DEBUG for verbose output, INFO for production.
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Custom GeminiLLM Class ---
class GeminiLLM:
    """
    A custom LLM class to integrate with Google's Gemini API.
    Mimics the interface needed by ERPChatbot's _generate_response method.
    """
    def __init__(self, model: str, api_key: str, temperature: float = 0.2):
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/"
        self.client = httpx.AsyncClient() # Use httpx for async requests
        logger.info(f"GeminiLLM initialized for model: {self.model}")

    async def invoke(self, prompt: str) -> str:
        """
        Invokes the Gemini API with the given prompt.
        """
        if not self.api_key:
            raise ValueError("Gemini API Key is not set. Please provide it in config.py.")

        url = f"{self.base_url}{self.model}:generateContent?key={self.api_key}"
        
        chat_history = []
        chat_history.append({"role": "user", "parts": [{"text": prompt}]})
        
        payload = {
            "contents": chat_history,
            "generationConfig": {
                "temperature": self.temperature,
                # Add other generation configs if desired, e.g., topK, topP
                # "stopSequences": ["\\n", "###", "<|endoftext|>", "User:", "Customer:", "Assistant:"]
                # Note: Gemini often handles conversational turns well, explicit stop sequences might be less critical.
            }
        }
        
        headers = {'Content-Type': 'application/json'}
        
        try:
            # Using httpx for async request
            response = await self.client.post(url, headers=headers, json=payload, timeout=60.0)
            response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
            
            result = response.json()
            
            if result.get("candidates") and result["candidates"][0].get("content") and \
               result["candidates"][0]["content"].get("parts") and \
               result["candidates"][0]["content"]["parts"][0].get("text"):
                return result["candidates"][0]["content"]["parts"][0]["text"]
            else:
                logger.warning(f"Gemini API response structure unexpected or content missing: {result}")
                # Fallback to a clear message if API returns empty content
                return "I apologize, the AI model did not provide a clear response. Please try again."
        except httpx.RequestError as e:
            logger.error(f"Gemini API request failed due to network or connection error: {e}")
            raise RuntimeError(f"Gemini API request failed: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Gemini API returned HTTP error: {e.response.status_code} - {e.response.text}")
            raise RuntimeError(f"Gemini API HTTP error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during Gemini API invocation: {e}")
            raise RuntimeError(f"Unexpected error with Gemini API: {e}")


# --- ERPChatbot Class (rest of your existing class) ---
class ERPChatbot:
    def __init__(self):
        logger.info("Initializing RedClouds AI Chatbot...")
        # Initialize Embedding model for RAG
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.embedding_model_name,
            model_kwargs={'device': 'cpu'}, # Use 'cuda' if you have a GPU
            encode_kwargs={'normalize_embeddings': True}
        )
        logger.info("HuggingFaceEmbeddings model loaded.")
        
        # Configure LLM to use GeminiLLM instead of Ollama
        self.llm = GeminiLLM(
            model=settings.llm_model,
            api_key=settings.gemini_api_key,
            temperature=settings.llm_temperature
        )
        logger.info(f"Gemini LLM initialized with model: {settings.llm_model}")

        # Initialize ChromaDB persistent client
        self.chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_path)
        self.collection = self._get_collection()
        logger.info(f"ChromaDB collection '{settings.chroma_collection}' loaded. Document count: {self.collection.count()}")
        if self.collection.count() == 0:
            logger.warning("ChromaDB collection is empty. Ensure data has been ingested using ingest_data.py.")
        
        self.query_cache: Dict[str, Any] = {}
        logger.info("RedClouds AI Chatbot initialization complete.")

    def _get_collection(self):
        """Retrieves or creates the ChromaDB collection."""
        try:
            collection = self.chroma_client.get_or_create_collection(name=settings.chroma_collection)
            logger.debug(f"ChromaDB collection '{settings.chroma_collection}' ensured to exist.")
            return collection
        except Exception as e:
            logger.error(f"Failed to get or create ChromaDB collection '{settings.chroma_collection}': {e}")
            raise

    def _is_greeting(self, question: str) -> bool:
        """Determines if the user's question is a greeting."""
        greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "greetings"]
        return any(greet in question.lower().strip() for greet in greetings)

    def _retrieve_relevant_documents(self, question: str, n_results: int = 5) -> List[Dict]:
        """
        Retrieves relevant documents from ChromaDB, combining vector search and keyword fallback.
        """
        logger.debug(f"Initiating document retrieval for question: '{question}' (n_results={n_results})")
        docs = []
        try:
            query_embedding = self.embeddings.embed_query(question)
            logger.debug(f"Generated query embedding for question (first 5 values): {query_embedding[:5]}...")

            vector_results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            logger.debug(f"Raw vector search results: {vector_results}")

            if vector_results and vector_results['documents'] and vector_results['documents'][0]:
                for i in range(len(vector_results['documents'][0])):
                    doc_content = vector_results['documents'][0][i]
                    metadata = vector_results['metadatas'][0][i]
                    dist = vector_results['distances'][0][i] 
                    
                    if dist < 0.8: # Cosine distance threshold (lower is better similarity)
                        docs.append({
                            "content": doc_content,
                            "metadata": metadata,
                            "distance": dist,
                            "type": "vector_search"
                        })
                        logger.debug(f"Retrieved vector document (dist: {dist:.4f}, source: {metadata.get('source', 'N/A')}): '{doc_content[:100]}...'")
                    else:
                        logger.debug(f"Skipping vector document due to high distance (dist: {dist:.4f}): '{doc_content[:100]}...'")
            else:
                logger.debug("Vector search returned no documents or empty results.")

            if len(docs) < n_results:
                logger.debug("Insufficient vector search results, attempting keyword search fallback.")
                keyword_docs = self._keyword_search(question, max_results=n_results - len(docs))
                docs.extend(keyword_docs)
                if keyword_docs:
                    logger.debug(f"Keyword search added {len(keyword_docs)} documents.")
                else:
                    logger.debug("Keyword search found no additional documents.")
            
            unique_docs = {}
            for doc in docs:
                key = (doc['content'], doc['metadata'].get('source'))
                if key not in unique_docs or doc.get('distance', float('inf')) < unique_docs[key].get('distance', float('inf')):
                    unique_docs[key] = doc
            
            final_docs = sorted(list(unique_docs.values()), key=lambda x: x.get('distance', float('inf')))[:n_results]
            
            logger.info(f"Final retrieved documents count: {len(final_docs)} for question: '{question[:50]}'")
            if final_docs:
                for d in final_docs:
                    logger.debug(f"Final relevant doc: Source='{d['metadata'].get('source', 'N/A')}', Dist={d.get('distance', 'N/A'):.4f}, Content='{d['content'][:150]}...'")
            return final_docs

        except Exception as e:
            logger.error(f"Error during document retrieval process: {e}")
            return []

    def _keyword_search(self, query: str, max_results: int = 3) -> List[Dict]:
        """Performs a basic keyword-based search as a fallback."""
        logger.debug(f"Performing keyword search for: '{query}' (max_results={max_results})")
        keyword_docs = []
        try:
            all_chroma_data = self.collection.get(include=['documents', 'metadatas']) 
            
            question_keywords = set(re.findall(r'\\w+', query.lower()))
            
            for i in range(len(all_chroma_data['documents'])):
                doc_content = all_chroma_data['documents'][i]
                metadata = all_chroma_data['metadatas'][i]
                
                doc_keywords = set(re.findall(r'\\w+', doc_content.lower()))
                common_keywords = question_keywords.intersection(doc_keywords)
                
                if common_keywords:
                    score = len(common_keywords) / len(question_keywords) if question_keywords else 0
                    keyword_docs.append({
                        "content": doc_content,
                        "metadata": metadata,
                        "distance": 1.0 - score, # Pseudo-distance for sorting
                        "type": "keyword_search"
                    })
                    if len(keyword_docs) >= max_results:
                        break
            
            return sorted(keyword_docs, key=lambda x: x['distance'])
        except Exception as e:
            logger.error(f"Error during keyword search: {e}", exc_info=True)
            return []

    async def _generate_response(self, question: str, docs: List[Dict]) -> Dict[str, Any]:
        """Generates a polite, formal, and friendly response using the LLM and retrieved documents."""
        logger.debug(f"Generating LLM response for question: '{question}' with {len(docs)} documents.")
        
        context_parts = []
        source_documents_for_response = []
        for doc in docs:
            source_info = doc["metadata"].get("source", "our documentation")
            faq_question = doc["metadata"].get("Question", "")
            faq_answer = doc["content"]
            
            if faq_question:
                context_parts.append(f"**Source: {source_info}**\\n**Question:** {faq_question}\\n**Answer:** {faq_answer}")
            else:
                context_parts.append(f"**Source: {source_info}**\\n**Content:** {faq_answer}")
            
            source_documents_for_response.append(SourceDocument(
                source=source_info,
                content=doc["content"],
                details=doc["metadata"]
            ))
        
        context = "\\n\\n".join(context_parts)
        logger.debug(f"Context provided to LLM (first 500 chars): {context[:500]}...")

        prompt = f"""
        You are RedClouds AI Assistant, a highly intelligent, polite, and friendly customer service chatbot for RedClouds ICT Solutions, a company specializing in software development using ERP systems. Your primary role is to assist customers by providing accurate, formal, and helpful answers based *strictly* on the provided "Documentation Context".

        **Your persona guidelines:**
        -   **Formal yet Friendly**: Maintain a professional and respectful tone, but be approachable and helpful.
        -   **Polite**: Always use polite language (e.g., "Certainly," "Please," "Thank you," "I apologize").
        -   **Data-driven**: ONLY use information directly provided in the "Documentation Context" below. Do not use outside knowledge.
        -   **Concise**: Provide clear and to-the-point answers without unnecessary jargon.
        -   **Handling Unknowns**: If the answer is NOT present in the provided context, politely state that you couldn't find the information in your documentation. Do NOT invent information.
        -   **Structured Answers**: Use bullet points or numbered lists for steps, features, or lists when appropriate for readability.
        -   **Suggested Questions**: Conclude your response by suggesting 1-3 concise, relevant follow-up questions that a user might have, based on the current interaction and the provided context. Format these as a clear list.

        ---
        Documentation Context:
        {context}
        ---

        User Question: {question}

        AI Assistant's Answer:
        """
        logger.debug(f"LLM Prompt (first 1000 chars): {prompt[:1000]}...")

        try:
            start_llm_time = time.time()
            # AWAITING the async invoke method of GeminiLLM
            raw_response = await self.llm.invoke(prompt) 
            end_llm_time = time.time()
            logger.debug(f"LLM invocation time: {end_llm_time - start_llm_time:.2f} seconds. Raw LLM response length: {len(raw_response)}")
            logger.debug(f"Raw LLM response: {raw_response[:500]}...")
            
            cleaned_response = self._clean_response(raw_response)
            
            suggested_questions = self._extract_suggested_questions(cleaned_response)
            
            for sq in suggested_questions:
                cleaned_response = re.sub(f'[\\s\\n]*[\\-\\*]?\\s*{re.escape(sq)}', '', cleaned_response, flags=re.IGNORECASE).strip()
            cleaned_response = re.sub(r'(?:Suggested|Follow-up) questions?:\\n*', '', cleaned_response, flags=re.IGNORECASE).strip()
            cleaned_response = re.sub(r'\\n{2,}', '\\n\\n', cleaned_response).strip()

            if not cleaned_response or any(phrase in cleaned_response.lower() for phrase in [
                "couldn't find specific information", "don't have enough information", "not explicitly stated", 
                "not found in the documentation", "i cannot provide specific information"
            ]):
                logger.warning("LLM response was empty or indicated lack of information. Initiating structured fallback.")
                return self._structured_fallback_response(docs, question)

            logger.info(f"Successfully generated LLM-based response for '{question[:50]}'.")
            return {
                "result": cleaned_response,
                "source_documents": source_documents_for_response,
                "suggested_questions": suggested_questions
            }
        except Exception as e:
            logger.error(f"Error during LLM response generation: {e}", exc_info=True)
            logger.warning("Falling back to structured fallback due to LLM error.")
            return self._structured_fallback_response(docs, question)

    def _extract_suggested_questions(self, text: str) -> List[str]:
        """Extracts suggested questions from the LLM's raw response."""
        questions = []
        match = re.search(r'(?:(?:Suggested|Follow-up) questions?:\\n+((?:[\\-\\d\\*]\\s*.+\\n?)+))', text, re.IGNORECASE | re.DOTALL)
        if match:
            lines = match.group(1).split('\\n')
            for line in lines:
                clean_line = re.sub(r'^[\\-\\d\\*\\s.]+', '', line).strip()
                if clean_line and clean_line.endswith('?'):
                    questions.append(clean_line)
        logger.debug(f"Extracted suggested questions: {questions[:3]}")
        return questions[:3]

    def _clean_response(self, response: str) -> str:
        """Cleans and formats the LLM's response for presentation."""
        response = re.sub(r'\\*\\*\\s*\\*\\*', '', response)
        response = response.replace('•', '-').replace(' - ', '\\n- ')
        response = '\\n'.join(line.strip() for line in response.split('\\n') if line.strip())
        
        if not any(phrase in response.lower() for phrase in [
            "let me know", "assist you further", "additional questions", "help you", "support you", "feel free", "clarification"
        ]):
            response += "\\n\\nPlease let me know if you need any further clarification or have additional questions."
        
        return response.strip()

    def _structured_fallback_response(self, docs: List[Dict], original_question: str) -> Dict[str, Any]:
        """
        Provides a structured fallback response when LLM cannot answer directly or an error occurs.
        """
        logger.debug(f"Executing structured fallback response. Docs available: {len(docs) > 0}")
        source_documents_list = []
        
        if not docs:
            logger.warning("No documents available for structured fallback. Returning general fallback message.")
            return {
                "result": settings.fallback_message,
                "source_documents": [],
                "suggested_questions": [
                    "Could you please rephrase your question more specifically?",
                    "What specific RedClouds ERP module are you interested in?",
                    "Would you like me to connect you with a human support agent?"
                ]
            }
        
        excerpts = []
        for doc in docs:
            source = doc["metadata"].get("source", "our documentation")
            content = doc["content"]
            faq_question = doc["metadata"].get("Question", "")
            
            excerpt_text = f"From {source} (related to '{faq_question[:100]}...'): {content[:300]}..."
            excerpts.append(excerpt_text)
            
            source_documents_list.append(SourceDocument(
                source=source,
                content=content,
                details=doc["metadata"]
            ))
        
        fallback_response_text = (
            "I apologize, I couldn't provide a direct, comprehensive answer to your question based on the specific information I have at hand. "
            "However, here's some related information from our documentation that might be helpful:\\n\\n" +
            "\\n\\n".join(excerpts) +
            "\\n\\nIf this doesn't fully address your query, please try rephrasing it or providing more details. "
            "I'm here to assist you further."
        )
        
        return {
            "result": fallback_response_text,
            "source_documents": source_documents_list,
            "suggested_questions": [
                "How can I rephrase my question to get a better answer?",
                "Can you tell me more about [topic from excerpt]?",
                "Is there a contact for human support?"
            ]
        }

    async def query(self, question: str, user_id: str, conversation_id: Optional[str]) -> Dict[str, Any]:
        """Main method to process a user query, handling greetings and the RAG pipeline."""
        logger.info(f"Received query: '{question[:50]}...' (User: {user_id}, Conv: {conversation_id})")

        if self._is_greeting(question):
            logger.info("Detected greeting. Returning pre-defined greeting message.")
            return {
                "result": settings.greeting_message,
                "sources": [],
                "suggested_questions": [
                    "What are the main ERP modules RedClouds offers?",
                    "How can RedClouds ERP benefit my business?",
                    "Tell me about your pricing structures.",
                    "How do I get technical support for RedClouds ERP?"
                ]
            }
        
        cache_key = f"{user_id}:{question}"
        if cache_key in self.query_cache:
            logger.debug(f"Returning response for '{question[:50]}...' from cache.")
            return self.query_cache[cache_key]

        relevant_docs = self._retrieve_relevant_documents(question)

        if not relevant_docs:
            logger.warning(f"No relevant documents found for '{question[:50]}...'. Returning general fallback message.")
            return {
                "result": settings.fallback_message,
                "sources": [],
                "suggested_questions": [
                    "Can you please rephrase your question more specifically?",
                    "What specific RedClouds ERP module are you interested in?",
                    "Would you like to speak to a human support agent?"
                ]
            }

        # Ensure _generate_response is awaited now that self.llm.invoke is async
        response_data = await self._generate_response(question, relevant_docs) 
        
        self.query_cache[cache_key] = response_data
        
        logger.info(f"Chatbot response successfully generated for '{question[:50]}...'.")
        return response_data