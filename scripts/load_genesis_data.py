#!/usr/bin/env python3
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
Load GENESIS data into a database for Superset visualization.

This script fetches data from the GENESIS REST API (German Federal Statistical Office)
and loads it into a PostgreSQL database. The loaded data can then be connected to
Superset for visualization and analysis.

Environment Variables:
    SUPERSET_GENESIS_DB_URI: Database connection string
    GENESIS_USERNAME: GENESIS API username (default: GAST)
    GENESIS_PASSWORD: GENESIS API password (default: GAST)
"""

import argparse
import os
import re
import sys
from datetime import datetime
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path to import superset modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from superset.genesis_client import GenesisClient, GenesisClientError  # noqa: E402
from superset.genesis.models import GenesisTableMetadata  # noqa: E402

# List of commonly used GENESIS tables to load
DEFAULT_TABLES = [
    {
        "code": "12411-0001",
        "name": "population_germany",
        "description": "Population of Germany",
    },
    {
        "code": "12411-0003",
        "name": "population_by_state",
        "description": "Population by federal state",
    },
    {
        "code": "81000-0001",
        "name": "gdp_quarterly",
        "description": "GDP quarterly",
    },
    {
        "code": "61111-0001",
        "name": "consumer_price_index",
        "description": "Consumer price index",
    },
    {
        "code": "13211-0001",
        "name": "employment_by_sectors",
        "description": "Employment by sectors",
    },
    {
        "code": "13231-0001",
        "name": "unemployment_statistics",
        "description": "Unemployment statistics",
    },
    {
        "code": "51000-0001",
        "name": "foreign_trade_statistics",
        "description": "Foreign trade statistics",
    },
]


def clean_column_name(name: str) -> str:
    """
    Clean column names for SQL compatibility.

    Args:
        name: Original column name

    Returns:
        Cleaned column name suitable for SQL
    """
    # Replace spaces and special characters with underscores
    name = re.sub(r"[^\w\s]", "_", name)
    name = re.sub(r"\s+", "_", name)
    # Remove consecutive underscores
    name = re.sub(r"_+", "_", name)
    # Remove leading/trailing underscores
    name = name.strip("_")
    # Convert to lowercase
    name = name.lower()
    return name


def update_metadata(
    session: sessionmaker,
    table_code: str,
    table_name: str,
    description: str,
    status: str,
    record_count: int | None = None,
    error_message: str | None = None,
) -> None:
    """
    Update metadata table with load information.

    Args:
        session: SQLAlchemy session
        table_code: GENESIS table code
        table_name: SQL table name
        description: Table description
        status: Load status (success, failed, pending)
        record_count: Number of records loaded
        error_message: Error message if failed
    """
    Session = session()
    try:
        metadata = Session.query(GenesisTableMetadata).filter_by(
            table_code=table_code
        ).first()

        if metadata:
            # Update existing record
            metadata.last_updated = datetime.utcnow()
            metadata.status = status
            metadata.record_count = record_count
            metadata.error_message = error_message
        else:
            # Create new record
            metadata = GenesisTableMetadata(
                table_code=table_code,
                table_name=table_name,
                description=description,
                last_updated=datetime.utcnow(),
                record_count=record_count,
                status=status,
                error_message=error_message,
                created_at=datetime.utcnow(),
            )
            Session.add(metadata)

        Session.commit()
    except Exception as e:
        print(f"⚠️  Failed to update metadata: {e}")
        Session.rollback()
    finally:
        Session.close()


def load_table(
    client: GenesisClient,
    engine: Engine,
    metadata_session: sessionmaker,
    table_info: dict[str, Any],
) -> bool:
    """
    Load a single GENESIS table into the database.

    Args:
        client: GENESIS API client
        engine: SQLAlchemy engine
        metadata_session: SQLAlchemy session maker for metadata
        table_info: Dictionary containing table code, name, and description

    Returns:
        True if successful, False otherwise
    """
    code = table_info["code"]
    table_name = table_info["name"]
    description = table_info["description"]

    print(f"\n{'=' * 70}")
    print(f"Loading table: {code} - {description}")
    print(f"Target table name: {table_name}")
    print(f"{'=' * 70}")

    try:
        # Fetch data from GENESIS API
        print(f"Fetching data from GENESIS API...")
        df = client.get_table_data(code)

        if df.empty:
            print(f"⚠️  No data returned for table {code}")
            update_metadata(
                metadata_session,
                code,
                table_name,
                description,
                "failed",
                0,
                "No data returned from API",
            )
            return False

        print(f"✓ Fetched {len(df)} rows with {len(df.columns)} columns")

        # Clean column names
        df.columns = [clean_column_name(col) for col in df.columns]
        print(f"✓ Cleaned column names")

        # Add metadata columns
        df["genesis_table_code"] = code
        df["genesis_table_description"] = description

        # Load data into database
        print(f"Loading data into database table '{table_name}'...")
        df.to_sql(
            table_name,
            engine,
            if_exists="replace",
            index=False,
            chunksize=1000,
        )

        print(f"✅ Successfully loaded {len(df)} rows into '{table_name}'")

        # Update metadata
        update_metadata(
            metadata_session, code, table_name, description, "success", len(df)
        )

        # Display sample data
        print(f"\nSample data (first 3 rows):")
        print(df.head(3).to_string())

        return True

    except GenesisClientError as e:
        error_msg = f"GENESIS API error: {e}"
        print(f"❌ Failed to load table {code}: {error_msg}")
        update_metadata(
            metadata_session, code, table_name, description, "failed", None, error_msg
        )
        return False
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        print(f"❌ Failed to load table {code}: {error_msg}")
        update_metadata(
            metadata_session, code, table_name, description, "failed", None, error_msg
        )
        return False


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Load GENESIS data into a database for Superset visualization"
    )
    parser.add_argument(
        "--tables",
        type=str,
        help="Comma-separated list of table codes to load (e.g., 12411-0001,81000-0001). "
        "If not specified, all default tables will be loaded.",
    )
    return parser.parse_args()


def main() -> None:
    """Main function to load GENESIS data."""
    print("=" * 70)
    print("GENESIS Data Loader for Superset")
    print("=" * 70)

    # Parse command line arguments
    args = parse_args()

    # Get configuration from environment variables
    db_uri = os.getenv("SUPERSET_GENESIS_DB_URI")
    username = os.getenv("GENESIS_USERNAME", "GAST")
    password = os.getenv("GENESIS_PASSWORD", "GAST")

    if not db_uri:
        print(
            "\n❌ Error: SUPERSET_GENESIS_DB_URI environment variable is not set.\n"
        )
        print("Please set the database connection string, for example:")
        print('  export SUPERSET_GENESIS_DB_URI="postgresql://user:pass@localhost:5433/genesis"')
        print("\nOr copy .env.genesis.example to .env.genesis and configure it.")
        sys.exit(1)

    # Determine which tables to load
    if args.tables:
        # Load specific tables
        table_codes = [code.strip() for code in args.tables.split(",")]
        tables_to_load = []
        for code in table_codes:
            # Find matching table in defaults, or create minimal entry
            matching = next((t for t in DEFAULT_TABLES if t["code"] == code), None)
            if matching:
                tables_to_load.append(matching)
            else:
                # Create minimal table info for custom code
                tables_to_load.append({
                    "code": code,
                    "name": f"genesis_{code.replace('-', '_')}",
                    "description": f"GENESIS table {code}",
                })
    else:
        tables_to_load = DEFAULT_TABLES

    print(f"\nConfiguration:")
    print(f"  Database URI: {db_uri}")
    print(f"  GENESIS Username: {username}")
    print(f"  Tables to load: {len(tables_to_load)}")

    # Initialize GENESIS client
    print(f"\nInitializing GENESIS API client...")
    client = GenesisClient(username=username, password=password)

    # Test API connection
    print(f"Testing API credentials...")
    if client.login_check():
        print(f"✅ API credentials are valid")
    else:
        print(f"⚠️  API credentials could not be verified, but will attempt to proceed")

    # Create database engine
    print(f"\nConnecting to database...")
    try:
        engine = create_engine(db_uri)
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"✅ Database connection successful")
    except Exception as e:
        print(f"\n❌ Error: Failed to connect to database: {e}\n")
        print("Please check your SUPERSET_GENESIS_DB_URI configuration.")
        sys.exit(1)

    # Create session for metadata
    Session = sessionmaker(bind=engine)

    # Load tables
    print(f"\nLoading GENESIS tables...")
    success_count = 0
    for table_info in tables_to_load:
        if load_table(client, engine, Session, table_info):
            success_count += 1

    # Print summary
    print(f"\n{'=' * 70}")
    print(f"Summary")
    print(f"{'=' * 70}")
    print(f"Successfully loaded: {success_count}/{len(tables_to_load)} tables")

    if success_count > 0:
        print(f"\n✅ GENESIS data loading complete!")
        print(f"\nNext steps:")
        print(f"1. Open Superset in your browser")
        print(f"2. Go to Data → Databases")
        print(f"3. Add a new database connection with the URI: {db_uri}")
        print(f"4. Go to Data → Datasets and add the loaded tables")
        print(f"5. Start creating charts and dashboards!")
        print(f"\nLoaded tables:")
        for table_info in tables_to_load:
            print(f"  - {table_info['name']}: {table_info['description']}")
    else:
        print(f"\n❌ No tables were loaded successfully.")
        print(f"Please check the error messages above and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
