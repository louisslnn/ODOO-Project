# Finance Employee AI Agent

An autonomous "Finance AI Agent" designed to act as a digital finance team member. While initially integrated with **Odoo**, the core architecture is ERP-agnostic to support future integrations with NetSuite, SAP, and other systems.

## 🎯 Core Mission

The Agent operates in two modes:

1. **Assistant Mode ("Copilot"):** The AI proposes entries/reconciliations; a human validates.
2. **Auto Mode:** The AI performs actions directly for low-risk cases and logs the activity.

## 🏗️ Architecture

This is an **external microservice** - a standalone Python application that connects to the ERP via API, NOT an internal ERP module. This design ensures:

- ERP-agnostic architecture (Adapter pattern)
- Independent deployment and scaling
- No ERP system modifications required

## 🤖 The 4 Internal Roles (Bots)

### 1. PostingBot (The Accountant)
Converts documents (invoices, receipts) into accounting entries.

### 2. MatchingBot (The Reconciler)
Links payments to invoices and performs bank reconciliations.

### 3. ControlBot (The Controller) - **MVP Priority**
Detects anomalies, compliance issues, and risk. Currently implemented with checks for:
- Zero amount entries
- Unbalanced journals
- Garbage/deprecated account usage
- Invoice-receipt mismatches
- (Placeholder for inventory and VAT checks)

### 4. ReportBot (The Analyst)
Generates KPIs and explains the "Why" behind the numbers.

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Access to an Odoo instance (or configure for your ERP)

### Installation

1. **Clone the repository**
   ```bash
   cd ODOO-Project
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Create a `.env` file in the project root:
   ```env
   ERP_TYPE=odoo
   ERP_URL=http://localhost:8069
   ERP_DATABASE=your_database_name
   ERP_USERNAME=your_username
   ERP_PASSWORD=your_password
   
   APP_MODE=assistant
   LOG_LEVEL=INFO
   LOG_FILE=logs/finance_agent.log
   CHECK_INTERVAL_HOURS=24
   ```

5. **Run the agent**
   ```bash
   python -m src.main
   ```

## 🐳 Docker Deployment

### Using Docker Compose

1. **Create `.env` file** (see above)

2. **Build and run**
   ```bash
   docker-compose up -d
   ```

3. **View logs**
   ```bash
   docker-compose logs -f finance-agent
   ```

### Using Docker directly

```bash
docker build -t finance-employee-agent .
docker run --env-file .env finance-employee-agent
```

## 📁 Project Structure

```
ODOO-Project/
├── src/
│   ├── core/               # Core ERP adapters and configuration
│   │   ├── __init__.py
│   │   ├── erp_client.py   # Abstract ERPClient interface
│   │   ├── odoo_client.py  # Odoo implementation
│   │   └── config.py       # Configuration management
│   ├── bots/
│   │   ├── posting/        # PostingBot (future)
│   │   ├── matching/       # MatchingBot (future)
│   │   ├── control/        # ControlBot (MVP)
│   │   │   └── control_bot.py
│   │   └── reporting/      # ReportBot (future)
│   ├── main.py             # Main entry point
│   └── __init__.py
├── config/                 # Configuration files
├── logs/                   # Log files and todo lists
├── tests/                  # Test files
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 🔧 Configuration

The application uses environment variables for configuration. See `.env.example` for all available options.

Key configuration options:
- `ERP_TYPE`: ERP system type (currently: `odoo`)
- `ERP_URL`: Base URL of your ERP instance
- `ERP_DATABASE`: Database name
- `ERP_USERNAME`: Username for authentication
- `ERP_PASSWORD`: Password for authentication
- `APP_MODE`: `assistant` or `auto`
- `LOG_LEVEL`: `DEBUG`, `INFO`, `WARNING`, or `ERROR`

## 📊 ControlBot Output

ControlBot generates a "Finance To-Do List" that includes:

- **Errors**: Critical issues that must be fixed immediately
- **Warnings**: Items that should be reviewed
- **Info**: Informational messages

The todo list is displayed in the console and saved to `logs/todo_list_YYYYMMDD_HHMMSS.txt`.

## 🔌 ERP Integration

### Current Implementation: Odoo

The `OdooClient` uses XML-RPC to communicate with Odoo. It implements the abstract `ERPClient` interface, providing methods for:

- Fetching accounting entries and lines
- Creating and validating journal entries
- Retrieving invoices, payments, and bank statements
- Accessing chart of accounts and journals

### Future Integrations

The adapter pattern allows easy addition of new ERP clients:

1. Create a new class inheriting from `ERPClient`
2. Implement all abstract methods
3. Configure via `ERP_TYPE` environment variable

Planned integrations:
- NetSuite
- SAP
- Microsoft Dynamics

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest

# With coverage
pytest --cov=src tests/
```

## 📝 Development Roadmap

### Phase 1: Setup & ControlBot MVP ✅
- [x] Project scaffolding
- [x] ERP adapter interface
- [x] Odoo client implementation
- [x] ControlBot basic checks

### Phase 2: Enhanced ControlBot
- [ ] Complete inventory checks
- [ ] Full VAT validation
- [ ] Advanced consistency checks

### Phase 3: MatchingBot
- [ ] Payment-invoice matching
- [ ] Bank reconciliation
- [ ] PSP payment matching

### Phase 4: PostingBot
- [ ] Document extraction
- [ ] Entry proposal logic
- [ ] Human validation workflow

### Phase 5: ReportBot
- [ ] KPI generation
- [ ] Variance analysis
- [ ] Natural language explanations

## 📄 License

[Add your license here]

## 🤝 Contributing

[Add contributing guidelines here]

## 📧 Support

[Add support contact information here]

