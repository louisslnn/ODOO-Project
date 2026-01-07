# Odoo Local Installation & Connection Guide

This document summarizes how Odoo was installed locally and how to connect to it.

## Installation Summary

Odoo has been installed **from source** in this project. The full Odoo source code is located in the `odoo/` directory, and a dedicated Python virtual environment (`venv-odoo/`) was created for running Odoo.

## Prerequisites

Before setting up Odoo, ensure you have the following installed:

1. **Python 3.10+** (Project uses Python 3.14.0)
   - Check your version: `python3 --version`

2. **PostgreSQL Database Server**
   - Database must be running on `localhost:5432`
   - User: `odoo`
   - Password: `odoo`
   - Ensure PostgreSQL is installed and running

3. **System Dependencies** (macOS-specific for M1/M2 Macs)
   - Some packages have special versions for Mac M1/M2 compatibility (noted in `odoo/requirements.txt`)

## Installation Steps

### 1. Set Up PostgreSQL Database

First, ensure PostgreSQL is installed and running:

```bash
# On macOS with Homebrew
brew install postgresql@14
brew services start postgresql@14

# Create the Odoo database user
createuser -s odoo
# Set password (if needed, connect to postgres and run: ALTER USER odoo WITH PASSWORD 'odoo';
```

### 2. Create Virtual Environment for Odoo

```bash
cd /Users/louissalanon/ODOO-Project
python3 -m venv venv-odoo
source venv-odoo/bin/activate
```

### 3. Install Odoo Dependencies

```bash
# Install Odoo requirements
pip install --upgrade pip
pip install -r odoo/requirements.txt
```

**Note for Mac M1/M2 Users**: The `odoo/requirements.txt` file includes special version pins for Python 3.10+ on macOS, particularly for:
- `gevent` and `greenlet` (async support)
- `psycopg2-binary` (PostgreSQL adapter)

### 4. Configure Odoo

The Odoo configuration file (`odoo.conf`) is located in the project root:

```ini
[options]
admin_passwd = $pbkdf2-sha512$600000$GoOQkpJy7h0jZIwxBqDUeg$kkI7aPlFZZ6x6CR83.Mi3I28O5eU3LgJPaPZgScNk85J76hzFcej0YptZyYwN6EUI6ZcfxSBYMsbCztBTIpkEQ
db_host = localhost
db_port = 5432
db_user = odoo
db_password = odoo
addons_path = odoo/addons, custom_addons
xmlrpc_port = 8069
```

**Key Configuration Details:**
- **Database Connection**: PostgreSQL on localhost:5432
- **Database User**: `odoo` / Password: `odoo`
- **XML-RPC Port**: `8069` (this is the port your Finance Agent connects to)
- **Addons Path**: Includes both standard Odoo addons and custom addons in `custom_addons/`

### 5. Initialize Odoo Database

```bash
# Activate the virtual environment
source venv-odoo/bin/activate

# Run Odoo to initialize the database
python3 odoo/odoo-bin -c odoo.conf -d your_database_name --init base --stop-after-init
```

Or use the `odoo-bin` script directly:
```bash
./odoo/odoo-bin -c odoo.conf -d your_database_name --init base --stop-after-init
```

### 6. Start Odoo Server

```bash
# With virtual environment activated
python3 odoo/odoo-bin -c odoo.conf
```

Or:
```bash
./odoo/odoo-bin -c odoo.conf
```

Odoo will be accessible at: **http://localhost:8069**

## Connecting to Odoo Locally

### From the Finance Agent Application

The Finance Employee AI Agent connects to Odoo via XML-RPC. Configure the connection in your `.env` file:

```env
# ERP Configuration
ERP_TYPE=odoo
ERP_URL=http://localhost:8069
ERP_DATABASE=your_database_name
ERP_USERNAME=admin
ERP_PASSWORD=admin
```

### From a Browser

1. Start Odoo server (see step 6 above)
2. Open your browser and navigate to: `http://localhost:8069`
3. Log in with your Odoo credentials (default: `admin` / `admin`)

### From Python (XML-RPC)

```python
import xmlrpc.client

# Connection parameters
url = "http://localhost:8069"
db = "your_database_name"
username = "admin"
password = "admin"

# Connect to Odoo
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Example: Search for invoices
invoice_ids = models.execute_kw(
    db, uid, password,
    'account.move', 'search',
    [[('state', '=', 'posted')]]
)
```

## Running Odoo

### Start Odoo in Development Mode

```bash
# Activate virtual environment
source venv-odoo/bin/activate

# Run Odoo (runs until stopped with Ctrl+C)
python3 odoo/odoo-bin -c odoo.conf

# Or with specific database
python3 odoo/odoo-bin -c odoo.conf -d your_database_name
```

### Common Odoo Commands

```bash
# Initialize/Update database
./odoo/odoo-bin -c odoo.conf -d database_name -u all

# Update specific module
./odoo/odoo-bin -c odoo.conf -d database_name -u module_name

# Run Odoo with debug logging
./odoo/odoo-bin -c odoo.conf --log-level=debug

# Install module on startup
./odoo/odoo-bin -c odoo.conf -d database_name -i module_name

# Stop after initialization (for database setup)
./odoo/odoo-bin -c odoo.conf -d database_name --stop-after-init
```

## Project Structure

```
ODOO-Project/
├── odoo/                  # Odoo source code (installed from source)
│   ├── odoo-bin          # Odoo entry point script
│   ├── addons/           # Standard Odoo addons
│   └── requirements.txt  # Odoo Python dependencies
├── custom_addons/        # Custom Odoo modules
│   └── my_first_module/  # Example custom module
├── venv-odoo/            # Python virtual environment for Odoo
├── odoo.conf             # Odoo configuration file
└── src/                  # Finance Agent application code
    └── core/
        └── odoo_client.py # Odoo XML-RPC client
```

## Troubleshooting

### Database Connection Issues

If you encounter database connection errors:

1. **Check PostgreSQL is running:**
   ```bash
   brew services list  # On macOS
   # or
   pg_isready
   ```

2. **Verify database user exists:**
   ```bash
   psql -U postgres -c "\du"
   ```

3. **Test connection:**
   ```bash
   psql -U odoo -d postgres -h localhost
   ```

### Port Already in Use

If port 8069 is already in use:

```bash
# Find process using port 8069
lsof -i :8069

# Kill the process
kill -9 <PID>
```

Or change the port in `odoo.conf`:
```ini
xmlrpc_port = 8070
```

### Module Import Errors

If you see import errors for Odoo modules:

1. Ensure virtual environment is activated: `source venv-odoo/bin/activate`
2. Verify all dependencies are installed: `pip install -r odoo/requirements.txt`
3. Check addons path in `odoo.conf` includes necessary directories

### Virtual Environment Issues

If the virtual environment is corrupted or missing:

```bash
# Remove and recreate
rm -rf venv-odoo
python3 -m venv venv-odoo
source venv-odoo/bin/activate
pip install --upgrade pip
pip install -r odoo/requirements.txt
```

## Additional Resources

- **Odoo Official Documentation**: https://www.odoo.com/documentation/17.0
- **Odoo Developer Documentation**: https://www.odoo.com/documentation/17.0/developer/
- **XML-RPC API Reference**: See `src/core/odoo_client.py` for implementation examples

## Notes

- The Finance Agent connects to Odoo via XML-RPC on port **8069**
- The Odoo installation uses a **source-based setup**, not a package installation
- Custom modules should be placed in the `custom_addons/` directory
- The `venv-odoo/` virtual environment is separate from any other Python environments you might use for the Finance Agent