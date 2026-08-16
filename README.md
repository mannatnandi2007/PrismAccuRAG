<div align="center">

# ⚡ PrismAccuRAG
### **Accuracy-Preserving Adaptive RAG Compressor**

*Surgically compress retrieval context by 30–60% while maintaining 100% factual accuracy.*

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Groq](https://img.shields.io/badge/Groq_LPU-F55036?style=for-the-badge&logo=fastapi&logoColor=white)](https://groq.com/)
[![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com/)
[![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com/)

---

</div>

## 📌 Overview

**PrismAccuRAG** is a full-stack, deployment-ready context compressor for Retrieval-Augmented Generation (RAG). Instead of passing bulky, redundant chunks to costly LLMs, PrismAccuRAG runs a local 10-stage pipeline that parses cross-chunk entity links, builds a dependency graph, intelligently prunes low-value sentences, verifies atomic claims with a local NLI model, and surgically repairs dropped facts before sending the minimal context to the LLM.

---

## 🔬 10-Stage Pipeline Architecture

```
User Query
    │
    ▼
[ 1. Dense Retrieval (FAISS) ] ─── Cosine similarity top-k search with all-MiniLM-L6-v2
    │
    ▼
[ 2. Cross-Chunk Coref & NER ] ─── Joint entity linking & pronoun resolution across chunks
    │
    ▼
[ 3. Dependency Graph Build ] ─── NetworkX graph (Nodes=Sentences, Edges=Shared Entities)
    │
    ▼
[ 4. Query Classifier ] ───────── Categorizes query ("factoid" @ 30% vs "multi-hop" @ 60%)
    │
    ▼
[ 5. Graph Pruning ] ─────────── Budget-aware node scoring with anchor preservation
    │
    ▼
[ 6. Claim Extraction ] ──────── SPO atomic triple extraction via spaCy dependency parsing
    │
    ▼
[ 7. NLI Entailment Check ] ──── Local DeBERTa-v3 model flags unentailed / missing claims
    │
    ▼
[ 8. Surgical Repair ] ───────── Re-inserts necessary source sentences for failed claims
    │
    ▼
[ 9. LLM Answer Generation ] ─── Single call to Groq (Llama-3.3-70B / Qwen) on compressed context
    │
    ▼
[ 10. Real-time Metrics ] ────── Token savings %, entailment pass rate %, latency breakdown
```

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend** | Python 3.11, FastAPI, Uvicorn | Async REST API & pipeline orchestrator |
| **Frontend** | React 18, Vite, Tailwind CSS v4 | Responsive dark navy/teal dashboard |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` | Dense vector embeddings |
| **Vector Index** | `faiss-cpu` (In-Memory FlatIP) | Sub-millisecond cosine similarity search |
| **Entity & Coref** | `spaCy` (`en_core_web_sm`) | Cross-chunk entity clustering & pronoun linking |
| **Graph Pruning** | `networkx` | Graph centrality & anchor connectivity preservation |
| **Claim Verification**| `cross-encoder/nli-deberta-v3-small` | Local zero-shot NLI premise-hypothesis check |
| **LLM Generation** | Groq (`llama-3.3-70b-versatile`) | Blazing fast answer synthesis (free tier) |
| **Deployment** | Docker, Docker Compose, Nginx | Multi-container production deployment |

---

## 🚀 Quick Start

### 1. Clone & Configure

```bash
git clone https://github.com/yourusername/prismax.git
cd prismax
```

Copy the environment template and insert your free **Groq API Key** (from [console.groq.com](https://console.groq.com/keys)):

```bash
cp .env.example .env
# Edit .env and set GROQ_API_KEY=gsk_...
```

---

### 2. Run Locally

#### **Backend (FastAPI)**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn app.main:app --reload --port 8000
```

#### **Frontend (React + Vite)**
```powershell
cd frontend
npm install
npm run dev
```

Open your browser at **`http://localhost:3000`**.

---

### 3. Deploy to Cloud (Vercel + Render) 🌐

#### **A. Backend on Render (Web Service)**
1. Push this repository to GitHub.
2. Go to [dashboard.render.com](https://dashboard.render.com/) → **New +** → **Web Service**.
3. Connect your repository:
   - **Root Directory**: `backend`
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. In **Environment Variables**, add:
   - `GROQ_API_KEY`: *your Groq API key*
   - `GROQ_MODEL`: `llama-3.3-70b-versatile`
5. Click **Deploy**. Note your Render backend URL (e.g. `https://prismaccurag-backend.onrender.com`).

#### **B. Frontend on Vercel**
1. Go to [vercel.com](https://vercel.com/) → **Add New Project** → Import your repository.
2. Configure settings:
   - **Root Directory**: `frontend`
   - **Framework Preset**: `Vite`
3. Under **Environment Variables**, add:
   - `VITE_API_URL`: *your Render backend URL* (e.g. `https://prismaccurag-backend.onrender.com`)
4. Click **Deploy**!

---

### 4. Run with Docker Compose 🐳

```bash
docker compose up --build
```

- **Frontend App**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/api/health`

---

## 📡 API Reference

### `POST /api/ingest`
Ingests, chunks, embeds, and indexes text documents into FAISS with disk caching.
```json
{
  "documents": ["Marie Curie was a pioneering physicist..."]
}
```

### `POST /api/query`
Runs the complete 10-stage adaptive compression pipeline and returns the synthesized answer with claim explainability.
```json
{
  "query": "Who did Marie Curie marry?",
  "top_k": 5
}
```

**Sample Response:**
```json
{
  "answer": "Marie Curie was married to Pierre Curie.",
  "query_type": "factoid",
  "token_stats": {
    "original_tokens": 181,
    "compressed_tokens": 82,
    "final_tokens": 98,
    "percent_saved": 45.9
  },
  "entailment_pass_rate": 100.0,
  "claims": [
    {
      "claim_text": "Marie Curie married Pierre Curie",
      "status": "preserved",
      "entailment_score": 0.98,
      "source_sentence": "Her husband, Pierre Curie, was a co-winner of her first Nobel Prize in 1903."
    }
  ]
}
```

---

## 📄 License

MIT License © 2026. Built with precision for intelligent, budget-friendly RAG pipelines.
