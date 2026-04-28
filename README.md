# Nishpaksh — निष्पक्ष
### India's First AI-Powered Hiring Bias Auditor

Detects India-specific proxy discrimination in hiring CSV data — caste via surnames, socioeconomic status via pin codes, and class via college tier. Generates plain-language audit reports aligned to India's **DPDP Act** and **Articles 14, 15, 16** of the Constitution.

---

## 🌍 UN SDG Alignment

| SDG | Goal | How Nishpaksh Contributes |
|-----|------|--------------------------|
| **SDG 8** | Decent Work & Economic Growth | Ensures fair hiring practices free from proxy discrimination |
| **SDG 10** | Reduced Inequalities | Detects caste, SES, and class-based disparities in employment |
| **SDG 16** | Peace, Justice & Strong Institutions | Provides DPDP-compliant audit reports for institutional accountability |

---

## Quick Start

### 1. Backend (Python + FastAPI)

```bash
cd backend

# Install dependencies (Python 3.10+ required)
pip install -r requirements.txt

# Add your Gemini API key
# Edit backend/.env and set: GEMINI_API_KEY=your-key-here

# Start the API server
python -m uvicorn main:app --reload --port 8000
```

### 2. Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

### 3. Demo Mode

Click the **"🎯 Try Demo Dataset"** button on the upload page to instantly load a pre-built 20-candidate synthetic hiring dataset — no file upload required.

### 4. Run Tests

```bash
cd backend
python -m pytest tests/ -v
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     React + Vite Frontend                   │
│  UploadPage → InspectPage → AuditPage → ReportPage         │
│  (ColumnMapper with auto-detect, SDG badges, demo mode)     │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API (JSON)
┌────────────────────────▼────────────────────────────────────┐
│                  FastAPI Backend (Python)                    │
│  /upload → /inspect → /audit → /narrative → /report         │
├─────────────────────────────────────────────────────────────┤
│  Engine Layer:                                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────┐│
│  │proxy_detector│ │ bias_metrics │ │ narrative_builder    ││
│  │(surname,     │ │ (DPD, EOD,   │ │ (Gemini AI-powered  ││
│  │ pincode, col)│ │  DIR, real   │ │  legal narrative)    ││
│  │              │ │  reweighing) │ │                      ││
│  └──────────────┘ └──────────────┘ └──────────────────────┘│
│  ┌──────────────┐ ┌──────────────┐                         │
│  │gemini_client │ │ pdf_builder  │                         │
│  │(task routing,│ │ (ReportLab)  │                         │
│  │ caching)     │ │              │                         │
│  └──────────────┘ └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

---

## What It Detects

| Proxy Type | Column | Mechanism | Flag Threshold |
|---|---|---|---|
| **Caste** | Names | Surname → caste group | Disparity ratio ≥ 1.5× |
| **Socioeconomic** | Pin codes | Pincode → SES tier | Tier-1 vs Tier-3 ratio ≥ 1.5× |
| **Class** | College | College → tier | Disparity ratio ≥ 1.5× |

## Severity Scale

- 🔴 **HIGH RISK** — disparity ratio ≥ 3.0×
- 🟡 **MEDIUM** — ratio ≥ 1.5×
- 🟢 **COMPLIANT** — ratio < 1.5×

## Bias Metrics (Pure Pandas — no sklearn/fairlearn required)

- **Demographic Parity Difference** (DPD) — threshold < 0.10
- **Equalized Odds Difference** (EOD) — threshold < 0.10
- **Disparate Impact Ratio** (DIR) — threshold > 0.80 (4/5ths rule)

## Mitigation

Real **statistical reweighing** — computes inverse-disparity weights per group (`w = overall_rate / group_rate`), applies them to derive corrected post-mitigation DPD/EOD/DIR. No fake multipliers.

---

## Key Features

- 🧠 **AI-Powered Proxy Detection** — Gemini classifies unknown surnames and colleges when static maps miss
- 📊 **Real Mitigation** — Statistical reweighing with transparent weight computation
- 🎯 **Auto-Detect Columns** — Smart heuristics pre-fill outcome, sensitive columns, and positive values
- 🎮 **Demo Mode** — One-click synthetic dataset to try the full audit flow
- ♿ **Accessible** — Skip-to-content, focus-visible, ARIA labels, keyboard navigation, prefers-reduced-motion
- 📱 **Responsive** — Works on mobile, tablet, and desktop
- 📄 **PDF Reports** — Downloadable compliance reports with DPDP checklist
- 🔒 **Privacy-First** — All data processed in-memory, never persisted

---

## Project Structure

```
nishpaksh/
├── backend/          # Python + FastAPI
│   ├── engine/       # proxy_detector, bias_metrics, narrative_builder, gemini_client
│   ├── data/         # surname_caste_map, pincode_ses_map, college_tier_map
│   ├── routers/      # upload, inspect, audit, narrative, report
│   ├── report/       # ReportLab PDF builder
│   └── tests/        # Unit + integration tests (pytest)
└── frontend/         # React + Vite + TypeScript
    └── src/
        ├── components/   # ui, upload, inspect, audit, report
        ├── pages/        # UploadPage, InspectPage, AuditPage, ReportPage
        ├── hooks/        # useAudit (state machine)
        └── lib/          # api, types, utils
```

## Environment Variables

```bash
# backend/.env
GEMINI_API_KEY=your-key-here

# frontend/.env
VITE_API_URL=http://localhost:8000
```

---

> "IBM AIF360 has existed for 7 years. Zero India-specific features. Nishpaksh is the only tool that knows what Ansari means in a hiring dataset."
