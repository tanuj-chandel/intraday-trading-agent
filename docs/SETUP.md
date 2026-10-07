# Setup and Installation Guide

## Prerequisites

- **Python**: 3.10+ (Tested with 3.12)
- **Node.js**: 18.0+ (Tested with 20 / 24)
- **Git**

---

## Local Development Quickstart

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run automated tests
pytest -v

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be live at `http://localhost:8000`.
Interactive Swagger API Documentation: `http://localhost:8000/docs`.

---

### 2. Frontend Setup

```bash
cd frontend

# Install npm dependencies
npm install

# Start Next.js development server
npm run dev
```

Frontend dashboard will be live at `http://localhost:3000`.

---

## Docker Deployment

To launch the complete stack with PostgreSQL database:

```bash
cd docker
docker-compose up --build -d
```

Services:
- **Frontend Dashboard**: `http://localhost:3000`
- **FastAPI Backend**: `http://localhost:8000`
- **PostgreSQL**: `localhost:5432`
