# Syntra

> An AI-powered developer agent that connects your GitHub repositories, understands your codebase, and helps you analyze, plan, and execute development tasks through an intelligent agent workflow.

## 🚀 Live Demo

**Frontend:** `https://syntra-livid.vercel.app`

**Backend API:** `https://syntra-backend-vkrw.onrender.com`

**API Documentation:** `https://syntra-backend-vkrw.onrender.com/docs`

**GitHub:** `https://github.com/Yash045-ycs/syntra`

---

## 📌 Overview

Syntra is a full-stack AI developer platform designed to help developers work with real GitHub repositories through an AI-powered workflow.

Instead of treating an AI assistant as a simple chatbot, Syntra connects the assistant to a developer's actual project context.

The platform allows users to:

* Create an account and securely authenticate
* Connect their GitHub account
* Select repositories to work with
* Register projects
* Analyze repository structure and source code
* Generate code embeddings for semantic code understanding
* Store project and agent execution data
* Run AI-powered development workflows
* Track agent activity and execution history

The goal is to provide a single workspace where developers can interact with an AI agent that understands their codebase rather than working from isolated prompts.

---

## ✨ Key Features

### 🔐 Authentication

* User registration and login
* Password hashing
* JWT-based authentication
* Protected API routes
* Persistent user sessions

### 🐙 GitHub Integration

* GitHub OAuth authentication
* GitHub account linking
* Repository access
* Repository metadata handling
* Secure GitHub OAuth state management

### 📂 Project Management

Users can create and manage projects connected to GitHub repositories.

Each project maintains its relationship with:

* User
* Repository
* Repository URL
* Project metadata

### 🧠 Codebase Understanding

Syntra processes source code into manageable chunks and generates vector embeddings.

This allows the platform to build a semantic representation of the repository and provides the foundation for intelligent code retrieval.

### 🤖 AI Agent Workflow

Syntra is designed around an agent-oriented development workflow rather than a simple question-and-answer chatbot.

The system can use project context to support tasks such as:

* Code analysis
* Repository understanding
* Development planning
* Problem investigation
* Code-related reasoning
* Agent execution tracking

### 📊 Activity Tracking

Agent executions and important system activity are stored for tracking and future analysis.

This provides visibility into what the system is doing rather than treating every AI response as an isolated interaction.

---

## 🏗️ Architecture

```text
                         ┌──────────────────────┐
                         │       User           │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   React + Vite       │
                         │      Frontend        │
                         └──────────┬───────────┘
                                    │ REST API
                                    ▼
                    ┌──────────────────────────────┐
                    │       FastAPI Backend        │
                    │                              │
                    │  Authentication              │
                    │  GitHub Integration          │
                    │  Projects                    │
                    │  Agent Runs                  │
                    │  Activity Logs               │
                    │  Code Processing             │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────┼───────────────┐
                    │              │               │
                    ▼              ▼               ▼
             ┌───────────┐  ┌────────────┐  ┌─────────────┐
             │ PostgreSQL│  │  GitHub    │  │  AI Models  │
             │ Supabase  │  │    API     │  │ Gemini/OpenAI│
             └───────────┘  └────────────┘  └─────────────┘
                    │
                    ▼
             ┌─────────────────┐
             │ pgvector        │
             │ Code Embeddings │
             └─────────────────┘
```

---

## 🛠️ Tech Stack

### Frontend

* React
* TypeScript
* Vite
* React Router
* Axios
* Tailwind CSS
* Lucide React

### Backend

* Python
* FastAPI
* SQLAlchemy
* Alembic
* PostgreSQL
* pgvector
* JWT Authentication
* Passlib / bcrypt

### AI

* Google Gemini
* OpenAI-compatible AI integration
* Vector embeddings
* Retrieval-oriented code understanding

### Integrations

* GitHub OAuth
* GitHub API
* Supabase PostgreSQL

### Deployment

* Render — Frontend
* Render — Backend
* Supabase — PostgreSQL

---

## 📁 Project Structure

```text
syntra/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── main.py
│   │
│   ├── alembic/
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── vite.config.*
│   └── .env
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## ⚙️ Local Setup

### Prerequisites

Make sure you have:

* Python 3.11+
* Node.js
* npm
* PostgreSQL / Supabase
* Git

### Clone the repository

```bash
git clone https://github.com/Yash045-ycs/syntra.git
cd syntra
```

---

## 🔧 Backend Setup

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create:

```text
backend/.env
```

Configure the required environment variables for:

```text
DATABASE_URL
JWT_SECRET
GITHUB_CLIENT_ID
GITHUB_CLIENT_SECRET
GITHUB_REDIRECT_URI
GEMINI_API_KEY
OPENAI_API_KEY
```

Run the backend:

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

---

## 💻 Frontend Setup

Open another terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Create:

```text
frontend/.env
```

Set the backend URL:

```env
VITE_API_URL=http://localhost:8000
```

Start the development server:

```bash
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:5173
```

---

## 🌐 Production Deployment

### Backend

The backend is deployed on Render.

```text
https://syntra-backend-vkrw.onrender.com
```

### Frontend

The frontend is deployed separately as a Render Static Site.

Production environment variable:

```env
VITE_API_URL=https://syntra-backend-vkrw.onrender.com
```

---

## 🔒 Environment Variables

Never commit `.env` files or API keys to GitHub.

Example:

```env
DATABASE_URL=your_database_url
JWT_SECRET=your_jwt_secret
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_REDIRECT_URI=your_github_redirect_uri
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
```

For the frontend:

```env
VITE_API_URL=http://localhost:8000
```

Production:

```env
VITE_API_URL=https://syntra-backend-vkrw.onrender.com
```

---

## 🔄 Core Workflow

```text
User
 │
 ▼
Register / Login
 │
 ▼
Connect GitHub
 │
 ▼
Select Repository
 │
 ▼
Create Syntra Project
 │
 ▼
Repository Processing
 │
 ▼
Source Code Chunking
 │
 ▼
Generate Embeddings
 │
 ▼
Store Semantic Code Representation
 │
 ▼
User submits development task
 │
 ▼
AI Agent receives task + project context
 │
 ▼
Agent analyzes relevant code
 │
 ▼
Agent execution
 │
 ▼
Result + activity tracking
```

---

## 🗄️ Database

Syntra uses PostgreSQL with pgvector support.

Core entities include:

* `users`
* `github_oauth_states`
* `projects`
* `code_embeddings`
* `agent_runs`
* `activity_logs`

The database schema is managed through SQLAlchemy and Alembic.

---

## 🧠 Why Vector Embeddings?

Large repositories cannot simply be sent to an AI model as one massive prompt.

Syntra therefore processes source code into smaller chunks and associates each chunk with a vector representation.

This enables semantic retrieval so that relevant sections of a repository can be identified when an agent needs project context.

Conceptually:

```text
Repository
    │
    ▼
Source Files
    │
    ▼
Code Chunks
    │
    ▼
Embeddings
    │
    ▼
Vector Database
    │
    ▼
Semantic Retrieval
    │
    ▼
AI Agent Context
```

---

## 🔮 Future Scope

Potential extensions include:

* Autonomous code modification
* Pull request generation
* Automated code review
* Test generation and execution
* Issue-to-implementation workflows
* Multi-agent development workflows
* Repository-wide dependency analysis
* Intelligent debugging
* Agent memory
* CI/CD integration
* Advanced retrieval and ranking
* Human approval checkpoints for sensitive actions

---

## 🎯 Project Goal

Syntra aims to move beyond the traditional AI chatbot model by giving an AI development agent access to structured project context.

The long-term goal is to make AI-assisted software development more contextual, traceable, and integrated with the developer's actual workflow.

---

## 📄 License

This project is currently intended as a personal/academic project.

See the repository for licensing information.

---

## 👨‍💻 Author

**Yash Shah**

GitHub:
https://github.com/Yash045-ycs
