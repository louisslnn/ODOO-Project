# Finance Employee AI Agent

An autonomous "Finance AI Agent" designed to act as a digital finance team member. While initially integrated with **Odoo**, the core architecture is ERP-agnostic to support future integrations with NetSuite, SAP, and other systems.

## 🎯 Core Mission

The Agent operates in two modes:

1. **Assistant Mode ("Copilot"):** The AI proposes entries/reconciliations; a human validates.
2. **Auto Mode:** The AI performs actions directly for low-risk cases and logs the activity.

## 🏗️ Architecture

This is an **external microservice** - a standalone Python application that connects to the ERP via API, NOT an internal ERP module. This design ensures:

- **ERP-agnostic architecture:** Uses an Adapter pattern to switch between ERPs easily.
- **Independent deployment:** Can run on a separate server, Docker container, or local machine.
- **No ERP system modifications:** Zero code changes required inside Odoo.

## 🤖 The 4 Internal Roles (Bots)

### 1. PostingBot (The Accountant)
Converts documents (invoices, receipts) into accounting entries.
*(Status: Planned)*

### 2. MatchingBot (The Reconciler)
Links payments to invoices and performs bank reconciliations.
*(Status: Planned)*

### 3. ControlBot (The Controller) - ✅ MVP Live
Detects anomalies, compliance issues, and risks. Currently operational with the following checks:
- **Zero Cost Items:** Detects products configured with a cost of 0.00 (margin risk).
- **Zero Amount Entries:** Flags journal entries with 0.00 value.
- **Unbalanced Journals:** Ensures debits equal credits.
- **Garbage Account Usage:** Alerts if deprecated accounts are used.
- **Invoice/Receipt Mismatch:** Checks for consistency between invoice totals and residuals.

### 4. ReportBot (The Analyst)
Generates KPIs and explains the "Why" behind the numbers using Natural Language.
*(Status: Next Phase - Interactivity Focus)*

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Access to an Odoo instance (v14-v17 tested)
- Modules installed on Odoo: `Invoicing`, `Sales`, `Inventory`

### Installation

1. **Clone the repository**
   ```bash
   cd ODOO-Project
   ```

2. **Create a virtual environment**
   ```python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```pip install -r requirements.txt```

4. **Configure environment variables**

Create a ```.env``` file in the project root:
   ```# ERP Configuration
   ERP_TYPE=odoo
   ERP_URL=http://localhost:8069
   ERP_DATABASE=dev_db
   ERP_USERNAME=admin
   ERP_PASSWORD=admin

   # App Configuration
   APP_MODE=assistant
   LOG_LEVEL=INFO
   LOG_FILE=logs/finance_agent.log
   CHECK_INTERVAL_HOURS=24
   ```

5. **Run the agent**
```python -m src.main```

## 📊 ControlBot Output

The ControlBot generates a high-visibility **"Finance To-Do List"**:

1. **Console Output:** Immediate feedback for developers.
2. **Audit Logs:** Saves a timestamped report in `logs/todo_list_YYYYMMDD_HHMMSS.txt`.

**Severity Levels:**
- 🔴 **ERROR**: Critical issues (e.g., Unbalanced journals).
- 🟡 **WARNING**: Business risks (e.g., Selling items at 0 cost).
- ℹ️ **INFO**: General notifications.

## 🔌 ERP Integration

### Current Implementation: Odoo

The project features a robust `OdooClient` based on `xmlrpc` that handles:
- Authentication & Connection management.
- Dynamic data fetching (`search_read`).
- Transaction creation (`create`, `post`).

### Architecture for Growth

The project uses a structured approach:
- `src/core/config.py`: **Pydantic** based configuration management (Type safety).
- `src/core/erp_client.py`: Abstract Base Class ensuring all ERP integrations follow the same contract.
- `src/main.py`: Central entry point with **Loguru** logging.

## 📝 Development Roadmap

### Phase 1: Setup & ControlBot MVP (Completed) ✅
- [x] Project scaffolding & Directory structure.
- [x] Environment setup (Docker, Pydantic, Loguru).
- [x] ERP Adapter Interface & Odoo Client implementation.
- [x] Connection established with Odoo Local.
- [x] **ControlBot Implementation**:
    - [x] Logic for detecting anomalies.
    - [x] Validated against test data (Zero cost products, Draft invoices).
    - [x] Report generation (Console + File).

### Phase 2: ReportBot & Interactivity (Next Step) 🚧
- [ ] **Interactive Mode:** Allow the user to query the bot (e.g., "Give me the P&L for Q1").
- [ ] **Data Aggregation:** Build helpers to fetch Sales/Margin data.
- [ ] **Natural Language Output:** Simple variance explanation.

### Phase 3: Actionable Insights
- [ ] **Write-Back:** Convert ControlBot issues into Odoo "Activities" (To-Do tasks inside the ERP).
- [ ] **MatchingBot:** Implement automatic bank reconciliation logic.

### Phase 4: PostingBot & Automation
- [ ] Document OCR simulation.
- [ ] Draft entry creation.

## 📁 Project Structure

```text
ODOO-Project/
├── src/
│   ├── core/               # Core infrastructure
│   │   ├── config.py       # Pydantic settings
│   │   ├── erp_client.py   # Abstract Interface
│   │   └── odoo_client.py  # Odoo Implementation
│   ├── bots/
│   │   ├── control/        # ControlBot (MVP Live)
│   │   │   └── control_bot.py
│   │   ├── matching/       # MatchingBot (Planned)
│   │   ├── posting/        # PostingBot (Planned)
│   │   └── reporting/      # ReportBot (Next Step)
│   ├── main.py             # Application Entry Point
│   └── __init__.py
├── logs/                   # Audit trails
├── .env                    # Secrets (Gitignored)
├── requirements.txt
└── README.md

## Contributing

This project is currently in the Alpha / Research phase.

## 📧 Contact

Project Lead: Nelson, Lead Developer: Louis