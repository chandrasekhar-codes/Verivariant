# GENESIS — Multi-Agent Genomic Intelligence

> **Technorazz'26 · MedTech & HealthTech · Problem 4.4**  
> _Team 63 — Multi-Agent Genomic Variant Analyzer_

---

## 🧬 What is GENESIS?

GENESIS is an AI-powered genomic variant analysis platform that uses a **multi-agent architecture** to research, verify, and report on genomic variants from VCF files.

### How it works:

1. **VCF Parser** — Parses annotated VCF files, extracts variants (chrom, pos, ref, alt, rsID, gene)
2. **Evidence Retrieval** — Concurrently queries ClinVar, gnomAD v4, and Ensembl VEP for each variant
3. **Research Agent** — Analyzes multi-source evidence and generates grounded, atomic claims with citations
4. **Verification Agent** — Independently audits every claim against raw database payloads (SUPPORTED / UNSUPPORTED / UNCLEAR)
5. **Report Agent** — Compiles findings into a traceable report with conflict detection and medical safety disclaimers

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm

### Installation

```bash
# Clone and enter the project
cd genomescope

# Install backend dependencies
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Install frontend dependencies
cd ../frontend
npm install
```

### Running

```bash
# Terminal 1: Backend
cd backend
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

Or use the Makefile:
```bash
make install  # Install everything
make dev      # Start both servers
```

Then open **http://localhost:5173** in your browser.

---

## 🗄 Database (Supabase)

GENESIS uses **Supabase** (PostgreSQL) for persistent storage of analysis jobs, variants, evidence, claims, and reports.

### Setup (Optional — works without it)

1. Create a free project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** → paste and run [`backend/supabase_schema.sql`](backend/supabase_schema.sql)
3. Go to **Settings → API** → copy your **Project URL** and **service_role key**
4. Add to your `.env`:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-service-role-key
   ```

### Tables Created
| Table | Purpose |
|-------|---------|
| `analysis_jobs` | Job metadata, status tracking |
| `variants` | Parsed genomic variants per job |
| `evidence_items` | ClinVar/gnomAD/VEP evidence per variant |
| `claims` | Research Agent claims with verification verdicts |
| `reports` | Final compiled reports |
| `variant_summaries` | Per-variant summaries linked to reports |

> **Note:** If Supabase is not configured, GENESIS falls back to file-based persistence automatically. The demo works either way.

---

## 🎮 Demo Mode (Judge Walkthrough)

Click **"Try Live Demo"** on the landing page. This uses a curated VCF file with 8 clinically characterized variants, with offline fallback evidence, so it works **without internet**.

Demo covers:
- **BRCA1** — Pathogenic breast cancer gene variant
- **CFTR** — Cystic fibrosis delta-F508 deletion
- **TP53** — Li-Fraumeni syndrome tumor suppressor
- **APOE** — Alzheimer's disease risk allele
- **MTHFR** — Common polymorphism with clinical debate
- **LDLR** — Familial hypercholesterolemia
- **HFE** — Hereditary hemochromatosis
- **EGFR** — Lung cancer therapeutic target

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────┐
│                    FRONTEND                       │
│  React 19 · Vite 6 · TypeScript · Tailwind CSS   │
│  Dark glassmorphism · Lucide icons                │
└─────────────────────┬────────────────────────────┘
                      │ REST API
┌─────────────────────┴────────────────────────────┐
│                    BACKEND                        │
│  FastAPI · Pydantic v2 · cyvcf2 · httpx          │
│                                                   │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────┐│
│  │  VCF Parser  │→│  Evidence     │→│  Multi-   ││
│  │  (cyvcf2)    │  │  Retrieval   │  │  Agent   ││
│  └─────────────┘  │  ├ ClinVar   │  │  Pipeline ││
│                    │  ├ gnomAD    │  │  ├ Research││
│                    │  └ VEP       │  │  ├ Verify ││
│                    └──────────────┘  │  └ Report ││
│                                      └──────────┘│
└──────────────────────────────────────────────────┘
```

---

## 🧪 Testing

```bash
cd backend
.venv/bin/python -m pytest -v     # 31 tests
```

---

## ⚠️ Medical Disclaimer

> **GENESIS is a research and report-drafting prototype. It does NOT provide medical diagnosis, treatment recommendations, or clinical advice. All outputs are intended for research and educational purposes only and MUST be reviewed by qualified healthcare professionals before any clinical consideration. Never use GENESIS as a substitute for professional medical judgment.**

---

## 📁 Project Structure

```
genomescope/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── models.py            # Pydantic data models
│   │   ├── pipeline.py          # Multi-agent orchestrator
│   │   ├── jobs.py              # Job state & persistence
│   │   ├── agents/
│   │   │   ├── research_agent.py
│   │   │   ├── verification_agent.py
│   │   │   └── report_agent.py
│   │   ├── evidence/
│   │   │   ├── clinvar.py
│   │   │   ├── gnomad.py
│   │   │   ├── ensembl_vep.py
│   │   │   ├── curated_cache.py
│   │   │   └── service.py
│   │   ├── parsing/
│   │   │   └── vcf_parser.py
│   │   └── routes/
│   │       └── analysis.py
│   ├── tests/
│   └── sample_data/
│       └── demo.vcf
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── index.css
│   │   ├── components/
│   │   │   ├── Header.tsx
│   │   │   ├── Hero.tsx
│   │   │   ├── UploadSection.tsx
│   │   │   ├── WorkflowProgress.tsx
│   │   │   ├── VariantTable.tsx
│   │   │   ├── VariantDetailModal.tsx
│   │   │   ├── ReportView.tsx
│   │   │   ├── ConflictBanner.tsx
│   │   │   └── AboutPage.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   └── types/
│   │       └── genomics.ts
│   ├── index.html
│   └── tailwind.config.js
└── Makefile
```

---

**Team 63 · TECHNORAZZ 2026 · "Hack the Gap"**
