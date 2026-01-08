---
title: GENESIS Integration
---

# GENESIS Destatis API Integration

This guide explains how to integrate and use the GENESIS database from the German Federal Statistical Office (Destatis) with Apache Superset.

## Overview

The GENESIS database provides access to official German statistics through a REST API. This integration allows you to:

- Fetch data directly from the GENESIS API
- Load commonly used statistics into your database
- Visualize German official statistics in Superset dashboards

### Available Data

The GENESIS database includes:

- **Population data**: Demographics, birth rates, death rates
- **Economic indicators**: GDP, inflation, trade statistics
- **Labor market statistics**: Employment, unemployment rates
- **Regional data**: Statistics by federal states (Bundesländer)
- **Social statistics**: Health, education, housing

## Prerequisites

- Docker and Docker Compose (for Docker-based setup)
- Python 3.10+ (for manual setup)
- PostgreSQL database (provided in Docker setup)

## Quick Start with Docker

The easiest way to get started is using Docker Compose:

### 1. Configure Environment

Copy the example environment file and configure it:

```bash
cp .env.genesis.example .env.genesis
```

Edit `.env.genesis` to set your GENESIS API credentials:

```env
GENESIS_USERNAME=GAST
GENESIS_PASSWORD=GAST
SUPERSET_GENESIS_DB_URI=postgresql://genesis:genesis@genesis-db:5432/genesis
```

**Note**: The default credentials `GAST/GAST` provide public access with limited features. For full access, register at [https://www-genesis.destatis.de](https://www-genesis.destatis.de).

### 2. Start Services

Start the GENESIS database and Superset:

```bash
docker compose -f docker-compose.yml -f docker-compose-genesis.yml --profile genesis up -d
```

This will start:
- Main Superset services
- `genesis-db`: PostgreSQL database on port 5433
- GENESIS database will be available for loading data

### 3. Load GENESIS Data

Run the data loader to fetch and load statistics:

```bash
docker compose -f docker-compose.yml -f docker-compose-genesis.yml run genesis-loader
```

This will load the following tables:
- `population_germany`: Population of Germany
- `population_by_state`: Population by federal state
- `gdp_quarterly`: GDP quarterly
- `consumer_price_index`: Consumer price index
- `employment_by_sectors`: Employment by sectors
- `unemployment_statistics`: Unemployment statistics
- `foreign_trade_statistics`: Foreign trade statistics

### 4. Connect to Superset

1. Open Superset in your browser (default: http://localhost:8088)
2. Go to **Data → Databases**
3. Click **+ Database** to add a new connection
4. Select **PostgreSQL** as the database type
5. Enter the connection details:
   ```
   Host: genesis-db
   Port: 5432
   Database: genesis
   Username: genesis
   Password: genesis
   ```
   Or use the SQLAlchemy URI:
   ```
   postgresql://genesis:genesis@genesis-db:5432/genesis
   ```
6. Click **Test Connection** and then **Save**

### 5. Add Datasets

1. Go to **Data → Datasets**
2. Click **+ Dataset**
3. Select the `genesis` database
4. Choose one of the loaded tables (e.g., `population_germany`)
5. Click **Add** to create the dataset
6. Start creating charts and dashboards!

## Manual Setup (Without Docker)

If you prefer not to use Docker, you can set up GENESIS integration manually:

### 1. Install Dependencies

```bash
pip install -r requirements/genesis.txt
```

This installs:
- `requests`: For API communication
- `pandas`: For data manipulation
- `sqlalchemy`: For database operations
- `psycopg2-binary`: PostgreSQL driver

### 2. Set Up Database

Create a PostgreSQL database for GENESIS data:

```sql
CREATE DATABASE genesis;
CREATE USER genesis WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE genesis TO genesis;
```

### 3. Configure Environment

Set the required environment variables:

```bash
export GENESIS_USERNAME="GAST"
export GENESIS_PASSWORD="GAST"
export SUPERSET_GENESIS_DB_URI="postgresql://genesis:your_password@localhost:5432/genesis"
```

### 4. Load Data

Run the data loader script:

```bash
python scripts/load_genesis_data.py
```

### 5. Connect Database to Superset

Follow step 4-5 from the Docker Quick Start above, adjusting the connection details to match your local database.

## Using the GENESIS Client

You can also use the GENESIS client directly in your Python code:

```python
from superset.genesis_client import GenesisClient, fetch_genesis_data

# Initialize client
client = GenesisClient(username="GAST", password="GAST")

# Test connection
if client.login_check():
    print("Connected to GENESIS API")

# Search for tables
tables = client.find_tables(search_term="population")
for table in tables:
    print(f"{table.get('Code')}: {table.get('Content')}")

# Fetch data
df = client.get_table_data("12411-0001", startyear="2020", endyear="2023")
print(df.head())

# Or use the convenience function
df = fetch_genesis_data("12411-0001", startyear="2020", endyear="2023")
```

## Available Tables

The default data loader includes these commonly used tables:

| Table Code | Dataset Name | Description |
|------------|--------------|-------------|
| 12411-0001 | population_germany | Total population of Germany |
| 12411-0003 | population_by_state | Population by federal state |
| 81000-0001 | gdp_quarterly | Gross Domestic Product (quarterly) |
| 61111-0001 | consumer_price_index | Consumer Price Index (inflation) |
| 13211-0001 | employment_by_sectors | Employment statistics by sector |
| 13231-0001 | unemployment_statistics | Unemployment rates and statistics |
| 51000-0001 | foreign_trade_statistics | Import/export statistics |

## Adding Custom Tables

To load additional GENESIS tables:

### Method 1: Modify the Loader Script

Edit `scripts/load_genesis_data.py` and add to the `DEFAULT_TABLES` list:

```python
DEFAULT_TABLES = [
    # ... existing tables ...
    {
        "code": "YOUR_TABLE_CODE",
        "name": "your_table_name",
        "description": "Your table description",
    },
]
```

Then run the loader again.

### Method 2: Use the Client Directly

Create a custom Python script:

```python
from superset.genesis_client import GenesisClient
from sqlalchemy import create_engine
import os

client = GenesisClient(
    username=os.getenv("GENESIS_USERNAME", "GAST"),
    password=os.getenv("GENESIS_PASSWORD", "GAST")
)

engine = create_engine(os.getenv("SUPERSET_GENESIS_DB_URI"))

# Fetch and load your custom table
df = client.get_table_data("YOUR_TABLE_CODE")
df.to_sql("your_table_name", engine, if_exists="replace", index=False)
```

### Finding Table Codes

To find table codes for specific statistics:

```python
from superset.genesis_client import GenesisClient

client = GenesisClient()
tables = client.find_tables(search_term="employment")

for table in tables:
    print(f"{table.get('Code')}: {table.get('Content')}")
```

Or search on the GENESIS website: [https://www-genesis.destatis.de](https://www-genesis.destatis.de)

## Troubleshooting

### API Connection Issues

**Problem**: Cannot connect to GENESIS API

**Solutions**:
- Check your internet connection
- Verify credentials are correct (default: GAST/GAST)
- Check if the API is accessible: `curl https://www-genesis.destatis.de/genesisWS/rest/2020/helloworld/whoami`
- Ensure firewall allows outbound HTTPS connections

### Database Connection Issues

**Problem**: Cannot connect to genesis-db

**Solutions**:
- Verify the database service is running: `docker compose ps`
- Check database logs: `docker compose logs genesis-db`
- Ensure port 5433 is not already in use
- Verify credentials in `.env.genesis` match database configuration

### Empty Data or Missing Tables

**Problem**: Data loader completes but no data is loaded

**Solutions**:
- Check the table code is correct
- Verify you have access to the table (some require full API access, not just GAST)
- Check loader logs for specific error messages
- Try a different table code to verify API connectivity

### Permission Errors with GAST Account

**Problem**: Some tables return "access denied" errors

**Solution**: The GAST account has limited access. Register for a free account at [https://www-genesis.destatis.de](https://www-genesis.destatis.de) and update your credentials in `.env.genesis`.

### Data Loading Performance

**Problem**: Loading data takes a long time

**Solutions**:
- Use year filters to limit data size: `startyear="2020"`, `endyear="2023"`
- Load tables one at a time instead of all at once
- Increase database resources if loading large datasets
- Consider loading data during off-peak hours

## API Reference

### GenesisClient Class

#### `__init__(username, password, language)`

Initialize the GENESIS API client.

**Parameters**:
- `username` (str): GENESIS API username (default: "GAST")
- `password` (str): GENESIS API password (default: "GAST")
- `language` (str): Language for responses, "en" or "de" (default: "en")

#### `login_check()`

Test API credentials.

**Returns**: `bool` - True if credentials are valid

#### `find_tables(search_term, category)`

Search for tables in the GENESIS database.

**Parameters**:
- `search_term` (str): Search term or pattern (default: "*")
- `category` (str): Category to search in (default: "all")

**Returns**: `list[dict]` - List of table information dictionaries

#### `get_table_data(table_name, startyear, endyear, area)`

Download table data as a pandas DataFrame.

**Parameters**:
- `table_name` (str): Table code (e.g., "12411-0001")
- `startyear` (str): Starting year (optional)
- `endyear` (str): Ending year (optional)
- `area` (str): Geographic area filter (default: "all")

**Returns**: `pandas.DataFrame` - Table data

#### `list_cubes(selection)`

List available data cubes.

**Parameters**:
- `selection` (str): Selection pattern (default: "*")

**Returns**: `list[dict]` - List of cube information dictionaries

#### `get_cube_metadata(cube_name)`

Get metadata for a specific cube.

**Parameters**:
- `cube_name` (str): Cube name/code

**Returns**: `dict` - Cube metadata

#### `get_modified_data(date)`

Get datasets modified since a date.

**Parameters**:
- `date` (str): Date in format YYYY-MM-DD

**Returns**: `list[dict]` - List of modified datasets

### Convenience Functions

#### `fetch_genesis_data(table_name, username, password, startyear, endyear)`

Quick function to fetch GENESIS data.

**Parameters**:
- `table_name` (str): Table code
- `username` (str): API username (default: "GAST")
- `password` (str): API password (default: "GAST")
- `startyear` (str): Starting year (optional)
- `endyear` (str): Ending year (optional)

**Returns**: `pandas.DataFrame` - Table data

## Additional Resources

- **GENESIS Website**: [https://www-genesis.destatis.de](https://www-genesis.destatis.de)
- **API Documentation (English)**: [https://www.destatis.de/EN/Service/OpenData/api-webservice.html](https://www.destatis.de/EN/Service/OpenData/api-webservice.html)
- **OpenAPI Specification**: [https://destatis.api.bund.dev/openapi.yaml](https://destatis.api.bund.dev/openapi.yaml)
- **Destatis Open Data**: [https://www.destatis.de/EN/Service/OpenData/_node.html](https://www.destatis.de/EN/Service/OpenData/_node.html)

## License

This integration is part of Apache Superset and is licensed under the Apache License 2.0.
