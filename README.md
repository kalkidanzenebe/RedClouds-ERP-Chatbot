# RedClouds ERP Intelligent Chatbot Assistance

## Project Overview
This project develops an Intelligent Chatbot Assistance system designed to enhance the efficiency and information accessibility for users of the RedClouds Enterprise Resource Planning (ERP) system. Modern ERPs are powerful but complex, often leading to user frustration, difficulty in finding information, and over-reliance on traditional support channels.

This chatbot aims to mitigate these challenges by providing an intuitive, real-time conversational interface that offers instant answers, guides users through complex processes, and reduces the workload on support staff.

## Features
- **Intelligent Q&A**: Answers user queries about RedClouds ERP functionalities, policies, and troubleshooting.
- **Retrieval-Augmented Generation (RAG)**: Leverages a knowledge base of ERP documentation to provide accurate and context-aware responses.
- **Source Attribution**: Cites the specific documents and pages from which information is retrieved.
- **Conversation History**: Stores and allows retrieval of past chat sessions for continuity and reference.
- **Suggested Questions**: Provides relevant follow-up questions to guide users to further information.
- **Responsive User Interface**: A modern and intuitive chat interface accessible across various devices (desktop, tablet, mobile).
- **Scalable Architecture**: Designed for future expansion and integration into the main RedClouds ERP application.

## Technologies Used

### Backend (Python)
- **FastAPI**: High-performance web framework for building RESTful APIs.
- **SQL Server**: Relational database for persistent storage of chat history and conversation states.
- **ChromaDB**: Vector database for storing and retrieving document embeddings.
- **Sentence Transformers**: Used for generating text embeddings from ERP documentation.
- **Google Gemini API (gemini-1.5-flash-latest)**: The Large Language Model (LLM) powering the chatbot's conversational capabilities.
- **LangChain Community**: Framework for building LLM-powered applications, orchestrating the RAG pipeline.
- **Pydantic**: Data validation and settings management.
- **httpx**: Asynchronous HTTP client for API calls.
- **pandas, tqdm, uuid, dotenv**: Supporting libraries for data processing, progress display, ID generation, and environment variable management.

### Frontend (React)
- **React**: JavaScript library for building the interactive user interface.
- **Tailwind CSS**: Utility-first CSS framework for rapid and responsive UI styling.
- **Lucide React**: Icon library for visual elements.

## Folder Structure
```
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
```

## Setup and Running Instructions

### 1. Prerequisites
- Python 3.10+
- Node.js & npm (or Yarn)
- SQL Server
- Git

### 2. Backend Setup

**Clone the Repository**
```bash
git clone https://github.com/kalkidanzenebe/RedClouds-ERP-Chatbot.git
cd RedClouds-ERP-Chatbot
```

**Create and Activate Python Virtual Environment**
```bash
python -m venv venv
# On Windows:
.env\Scriptsctivate
# On macOS/Linux:
source venv/bin/activate
```

**Install Python Dependencies**
```bash
pip install -r requirements.txt
```

**Configure Environment Variables**

Create a `.env` file in the root of your project:

```env
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
CORS_ORIGINS=http://localhost:5173
```

**Initialize SQL Server Database**
```bash
python backend/scripts/init_db.py
```

**Ingest ERP Documentation into ChromaDB**
```bash
python backend/scripts/ingest_data.py
```

**Run the Backend Server**
```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

**Navigate to Frontend**
```bash
cd frontend-vite
```

**Install Dependencies**
```bash
npm install
# Or: yarn install
```

**Run Frontend Server**
```bash
npm run dev
# Or: yarn dev
```

### Usage

- **Access**: Open http://localhost:5173 in your browser.
- **Chat**: Ask questions about RedClouds ERP.
- **History**: View previous chats from the sidebar.
- **Start New Chat**: Use the sidebar button.

## Future Enhancements
- Advanced ERP Integration via APIs
- User Authentication and Personalization
- Voice Input (Speech-to-Text)
- Feedback Mechanism
- Admin Dashboard for Monitoring

## License
This project is licensed under the MIT License - see the `LICENSE.md` file for details.
