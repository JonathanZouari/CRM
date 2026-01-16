# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Smart CRM is a Hebrew/English bilingual CRM system for AI implementation sales teams. It includes:
- Flask REST API backend with Supabase database
- CrewAI-powered chatbot with multi-mode personas (service, sales, consulting)
- RAG-based natural language queries using ChromaDB vector store
- AI-powered lead scoring system
- Railway deployment configuration for production

## Commands

### Run the Server (Development)
```bash
cd smart-crm
python run.py
```
Server runs on `http://localhost:5000` by default.

### Run the Server (Production)
```bash
cd smart-crm
gunicorn run:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
```

### Seed Test Data
```bash
cd smart-crm
python seeds/seed_data.py
```
Creates test users, leads, deals, interactions, tasks, expenses, and work logs.

### Install Dependencies
```bash
cd smart-crm
pip install -r requirements.txt
```

## Architecture

### Backend Structure (`smart-crm/`)
```
app/
├── __init__.py      # Flask app factory, blueprint registration
├── config.py        # Environment-based configuration
├── models/          # Supabase ORM-like models (CRUD operations)
├── routes/          # API blueprints (auth, leads, deals, tasks, analytics, chat, rag)
├── services/        # Business logic (lead_scoring.py, vector_store.py)
└── crews/           # CrewAI agents (chatbot_crew.py, rag_crew.py)
```

### Key Components

**Models** (`app/models/`): Each model (User, Lead, Deal, Task, etc.) wraps Supabase client operations. Base model in `base.py` provides singleton Supabase client via `get_db()`.

**CrewAI Chatbot** (`app/crews/chatbot_crew.py`): Three agent modes with distinct system prompts:
- `service`: Customer support persona
- `sales`: Lead qualification persona
- `consulting`: AI implementation advisor persona

**RAG System** (`app/crews/rag_crew.py`): Natural language CRM queries using custom CrewAI tools:
- `CRMSearchTool`: Vector similarity search via ChromaDB
- `LeadStatsTool`, `DealStatsTool`, `TaskStatsTool`: Database aggregations
- `ProfitabilityTool`: Revenue/expense calculations

**Lead Scoring** (`app/services/lead_scoring.py`): Weighted scoring (0-100) based on:
- Business size (20 pts), Budget (25 pts), Source (15 pts)
- Interest level (15 pts), AI readiness (15 pts), Recency (10 pts)

### API Routes
- `/api/health` - Health check endpoint
- `/api/auth/*` - Authentication (JWT-based)
- `/api/leads/*` - Lead CRUD + scoring
- `/api/deals/*` - Deal pipeline management
- `/api/tasks/*` - Task management
- `/api/analytics/*` - Dashboard analytics
- `/api/chat/*` - Multi-mode chatbot
- `/api/rag/*` - Natural language queries

### Frontend Routes
The Flask app serves static HTML pages:
- `/` or `/login` - Login page
- `/dashboard` - Main CRM dashboard
- `/leads` - Lead management list
- `/pipeline` - Sales pipeline kanban
- `/lead/<lead_id>` - Lead details with AI scoring
- `/chat` - Multi-mode chatbot interface

### Database
Uses Supabase with schema in `migrations/001_initial_schema.sql`. Tables: users, leads, deals, interactions, tasks, expenses, work_logs, chat_sessions, chat_messages. All tables have RLS enabled.

### Frontend
Static HTML files in `stitch_representative_crm_dashboard/` with accompanying `screen.png` mockups. API client in `smart-crm/frontend/js/api.js`.

## Environment Variables

Required in `smart-crm/.env` (see `.env.example`):
- `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_SERVICE_KEY`
- `OPENAI_API_KEY` (for CrewAI and embeddings)
- `SECRET_KEY`, `JWT_SECRET_KEY`

Optional:
- `CHROMA_PERSIST_DIR` (default: `./chroma_data`)
- `COMPANY_NAME` (default: "Smart CRM AI Solutions")
- `DEFAULT_LANGUAGE` (default: "he")
- `CORS_ORIGINS` (comma-separated list of allowed origins)
- `FRONTEND_DIR` (override frontend static files location)

Railway auto-sets:
- `PORT` - The port to bind to
- `RAILWAY_PUBLIC_DOMAIN` - App's public domain (auto-added to CORS)

## Supabase MCP

This project has Supabase MCP configured in `.mcp.json`. Use MCP tools for:
- Database schema changes (`apply_migration`)
- Running queries (`execute_sql`)
- Checking tables (`list_tables`)
- Generating TypeScript types (`generate_typescript_types`)

Follow patterns in `SKILL.md` for Supabase best practices (RLS policies, indexes, triggers).

## Deployment

### Railway
Configured via `railway.json`:
- Build: Nixpacks with `pip install -r requirements.txt`
- Start: gunicorn with 2 workers, 4 threads, 120s timeout
- Health check: `/api/health` (300s timeout)

### Local Development
1. Copy `smart-crm/.env.example` to `smart-crm/.env`
2. Fill in Supabase and OpenAI credentials
3. Run `python run.py` from `smart-crm/`

## Test Credentials (after seeding)
- Admin: `admin@smartcrm.com` / `admin123`
- Rep 1: `alex@smartcrm.com` / `alex123`
- Rep 2: `maya@smartcrm.com` / `maya123`
