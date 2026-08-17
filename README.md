<div align="center">

# ⚡ PrismAccuRAG
### **Accuracy-Preserving Adaptive RAG Context Compressor**

*Surgically compress retrieval context by 30–60% while maintaining 100% factual accuracy.*

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](https://reactjs.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Groq](https://img.shields.io/badge/Groq_LPU-F55036?style=for-the-badge&logo=fastapi&logoColor=white)](https://groq.com/)

---

</div>

> ## 🚀 **RUNNING LOCALLY (QUICK START GUIDE)**
> 
> Follow these simple copy-paste steps to clone, set up, and run **PrismAccuRAG** locally in under 3 minutes.

### 📋 Prerequisites
- **Python 3.10+** (Python 3.11 recommended)
- **Node.js 18+** & `npm`
- Free **Groq API Key** from [console.groq.com/keys](https://console.groq.com/keys)

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/mannatnandi2007/PrismAccuRAG.git
cd PrismAccuRAG
```

---

### Step 2: Configure Environment Variables
Create a `.env` file in the root folder:
```bash
# Windows (PowerShell):
Copy-Item .env.example .env

# macOS / Linux (Bash):
cp .env.example .env
```
Open `.env` and add your **Groq API Key**:
```env
GROQ_API_KEY=gsk_your_actual_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

---

### Step 3: Start the Backend (Terminal 1)

#### **On Windows (PowerShell):**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn app.main:app --reload --port 8000
```

#### **On macOS / Linux (Bash):**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn app.main:app --reload --port 8000
```

> 🟢 **Backend API will be running at**: [http://localhost:8000](http://localhost:8000)  
> 📖 **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)  
> 🩺 **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

### Step 4: Start the Frontend (Terminal 2)

In a new terminal window:
```bash
cd frontend
npm install
npm run dev
```

> 🌐 **Open the Web UI in your browser**: **[http://localhost:3000](http://localhost:3000)**

---

### Step 5: Test with Sample Document
1. In the Web UI at `http://localhost:3000`, click **Upload .txt** and select the provided `sample.txt` file (or paste its content into the text area).
2. Click **Ingest Documents** (the badge turns green).
3. Try asking multi-hop and factual questions:
   - *"Why did the person who became the first female professor at the Sorbonne die in 1934?"*
   - *"What element discovered by the co-winner of the 1903 Nobel Prize was named after his wife's native country?"*
   - *"How did the Little Curies assist field hospitals in World War I?"*
4. View the real-time token reduction %, NLI claim entailment breakdown, and synthesized LLM answers!

---

## 📌 Overview

**PrismAccuRAG** is an accuracy-preserving context compressor for Retrieval-Augmented Generation (RAG). Instead of passing bulky, redundant chunks to costly LLMs, PrismAccuRAG runs a local 10-stage pipeline that parses cross-chunk entity links, builds a dependency graph, intelligently prunes low-value sentences, verifies atomic claims with a local NLI model, and surgically repairs dropped facts before sending the minimal context to the LLM.

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

## 🐳 Run with Docker Compose (Alternative)

```bash
docker compose up --build
```
- **Frontend App**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000/docs`

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
