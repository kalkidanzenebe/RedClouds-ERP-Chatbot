RedClouds ERP Intelligent Chatbot Assistance
Project Overview
This project develops an Intelligent Chatbot Assistance system designed to enhance the efficiency and information accessibility for users of the RedClouds Enterprise Resource Planning (ERP) system. Modern ERPs are powerful but complex, often leading to user frustration, difficulty in finding information, and over-reliance on traditional support channels.

This chatbot aims to mitigate these challenges by providing an intuitive, real-time conversational interface that offers instant answers, guides users through complex processes, and reduces the workload on support staff.

Features
Intelligent Q&A: Answers user queries about RedClouds ERP functionalities, policies, and troubleshooting.

Retrieval-Augmented Generation (RAG): Leverages a knowledge base of ERP documentation to provide accurate and context-aware responses.

Source Attribution: Cites the specific documents and pages from which information is retrieved.

Conversation History: Stores and allows retrieval of past chat sessions for continuity and reference.

Suggested Questions: Provides relevant follow-up questions to guide users to further information.

Responsive User Interface: A modern and intuitive chat interface accessible across various devices (desktop, tablet, mobile).

Scalable Architecture: Designed for future expansion and integration into the main RedClouds ERP application.

Technologies Used
The project is built with a robust tech stack, separating the backend API from the frontend user interface.

Backend (Python)
FastAPI: High-performance web framework for building RESTful APIs.

SQL Server: Relational database for persistent storage of chat history and conversation states.

ChromaDB: Vector database for storing and retrieving document embeddings.

Sentence Transformers: Used for generating text embeddings from ERP documentation.

Google Gemini API (gemini-1.5-flash-latest): The Large Language Model (LLM) powering the chatbot's conversational capabilities.

LangChain Community: Framework for building LLM-powered applications, orchestrating the RAG pipeline.

Pydantic: Data validation and settings management.

httpx: Asynchronous HTTP client for API calls.

pandas, tqdm, uuid, dotenv: Supporting libraries for data processing, progress display, ID generation, and environment variable management.

Frontend (React)
React: JavaScript library for building the interactive user interface.

Tailwind CSS: Utility-first CSS framework for rapid and responsive UI styling.

Lucide React: Icon library for visual elements.

Folder Structure
.
├── backend/
│   └── app/
│       ├── config.py             # Application settings (LLM, DB, paths)
│       ├── database.py           # Database connection and utils
│       ├── main.py               # FastAPI application entry point, API endpoints
│       ├── models.py             # Pydantic data models for API requests/responses
│       ├── rag.py                # Core RAG logic (LLM, embeddings, vector store interaction)
│       ├── ingest_data.py        # Script for ingesting documents into ChromaDB
│       └── init_db.py            # Script for initializing SQL Server database schema
├── data/
│   └── redclouds_erp_faqs.csv    # Example ERP documentation/knowledge base data
├── frontend-vite/
│   ├── public/                   # Public assets (e.g., vite.svg)
│   ├── src/
│   │   ├── App.jsx               # Main React application component
│   │   └── components/
│   │       ├── ChatInput.jsx     # User input field and send button
│   │       ├── ChatModal.jsx     # Main chatbot modal container
│   │       ├── ChatWindow.jsx    # Displays chat messages
│   │       ├── MessageBubble.jsx # Renders individual chat messages
│   │       └── Sidebar.jsx       # Displays past conversations
│   ├── package.json              # Frontend dependencies and scripts
│   └── ... (other Vite/React config files)
├── .env                          # Environment variables (sensitive data, configurations)
├── .gitignore                    # Specifies files/directories to ignore in Git
├── requirements.txt              # Python dependencies for the backend
└── README.md                     # Project overview and instructions

Setup and Running Instructions
Follow these steps to set up and run the RedClouds ERP Chatbot locally.

1. Prerequisites
Python 3.10+

Node.js & npm (or Yarn)

SQL Server: Ensure you have access to a SQL Server instance (local or remote).

Git

2. Backend Setup
Clone the Repository:

git clone https://github.com/kalkidanzenebe/RedClouds-ERP-Chatbot.git
cd RedClouds-ERP-Chatbot

Create and Activate Python Virtual Environment:

python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

Install Python Dependencies:

pip install -r requirements.txt

Configure Environment Variables:

Create a .env file in the root of your RedClouds-ERP-Chatbot directory.

Add your SQL Server connection details and Google Gemini API key:

# .env
DB_SERVER=your_sql_server_host
DB_NAME=RedCloudsERP
DB_USER=your_sql_user
DB_PASSWORD=your_sql_password

GOOGLE_API_KEY=your_gemini_api_key

LLM_MODEL=gemini-1.5-flash-latest
LLM_TEMPERATURE=0.7
LLM_TIMEOUT_SECONDS=120
LLM_MAX_OUTPUT_TOKENS=1024

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_CACHE_DIR=./.cache/embeddings

CHROMA_PERSIST_DIRECTORY=./chroma_db
RETRIEVER_K_RESULTS=5

TEXT_CHUNK_SIZE=1000
TEXT_CHUNK_OVERLAP=200

DATA_DIRECTORY=./data

# Frontend URL for CORS (adjust if your frontend runs on a different port/host)
CORS_ORIGINS=http://localhost:5173

Important: Replace placeholders (your_sql_server_host, your_sql_user, your_sql_password, your_gemini_api_key) with your actual credentials.

Initialize SQL Server Database:

python backend/scripts/init_db.py

This script will create the conversations and messages tables in your specified SQL Server database.

Ingest ERP Documentation into ChromaDB:

Ensure your ERP knowledge base documents (e.g., PDFs) are placed in the ./data directory. The example includes redclouds_erp_faqs.csv.

Run the ingestion script:

python backend/scripts/ingest_data.py

This will process your documents, create embeddings, and store them in the ./chroma_db directory. This step might take some time depending on the volume of data.

Run the FastAPI Backend Server:

uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

The backend will now be running on http://localhost:8000.

3. Frontend Setup
Navigate to the Frontend Directory:

cd frontend-vite

Install Node.js Dependencies:

npm install
# Or if using yarn: yarn install

Run the React Development Server:

npm run dev
# Or if using yarn: yarn dev

The frontend will typically open in your browser at http://localhost:5173 (or another available port).

Usage
Open the Frontend: Access the chatbot in your web browser via the URL provided by npm run dev (e.g., http://localhost:5173).

Interact: Type your questions related to RedClouds ERP into the input field and press Enter or click the send button.

Explore History: Use the sidebar to view and navigate your past conversations.

Start New Chat: Click the "New Chat" button in the sidebar to begin a fresh conversation.

Future Enhancements
Advanced ERP Integration: Deeper integration with ERP modules to perform actions (e.g., creating draft reports, retrieving live data via ERP APIs).

User Authentication: Implement user authentication within the chatbot itself for personalized experiences.

Multi-modal Input: Add support for voice input (Speech-to-Text).

User Feedback: Implement a feedback mechanism for users to rate chatbot responses.

Admin Dashboard: Develop a dedicated dashboard for monitoring chatbot performance, usage analytics, and knowledge base management.

License
(You can choose a license like MIT, Apache 2.0, etc., and add it here. For example, if MIT:)

This project is licensed under the MIT License - see the LICENSE.md file for details.
