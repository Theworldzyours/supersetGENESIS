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
"""Initialization script for GENESIS German Federal Statistical Office integration."""

import logging
import os

from superset.extensions import db
from superset.models.core import Database

logger = logging.getLogger(__name__)


def init_genesis_database() -> bool:
    """
    Initialize GENESIS database connection in Superset.

    This function checks if the SUPERSET_GENESIS_DB_URI environment variable
    is set and creates a database connection for GENESIS data if it doesn't
    already exist.

    Returns:
        True if database was created or already exists, False if URI not configured
    """
    # Get GENESIS database URI from environment
    genesis_db_uri = os.getenv("SUPERSET_GENESIS_DB_URI")

    if not genesis_db_uri:
        logger.info(
            "GENESIS integration not configured: SUPERSET_GENESIS_DB_URI not set"
        )
        return False

    # Check if GENESIS database already exists
    existing_db = db.session.query(Database).filter_by(
        database_name="GENESIS (German Statistics)"
    ).first()

    if existing_db:
        logger.info("GENESIS database connection already exists")
        return True

    try:
        # Create new database connection
        genesis_db = Database(
            database_name="GENESIS (German Statistics)",
            sqlalchemy_uri=genesis_db_uri,
            expose_in_sqllab=True,
            allow_ctas=False,
            allow_cvas=False,
            allow_dml=False,
            allow_run_async=True,
            allow_file_upload=False,
            extra='{"metadata_params": {}, "engine_params": {}, "metadata_cache_timeout": {}, "schemas_allowed_for_file_upload": []}',
        )

        # Set description
        genesis_db.description = (
            "Official German Federal Statistical Office (Destatis) data from the "
            "GENESIS database. Contains population statistics, economic indicators, "
            "labor market data, and regional statistics."
        )

        # Add to session and commit
        db.session.add(genesis_db)
        db.session.commit()

        logger.info(
            "Successfully created GENESIS database connection: "
            "GENESIS (German Statistics)"
        )
        return True

    except Exception as ex:
        logger.exception("Failed to create GENESIS database connection")
        db.session.rollback()
        return False


def setup_genesis() -> None:
    """
    Set up GENESIS integration.

    This is the main entry point for GENESIS initialization. It creates
    the database connection and can be extended to load example data or
    create sample dashboards.

    This function is designed to be idempotent - it can be called multiple
    times safely.
    """
    logger.info("Starting GENESIS integration setup...")

    # Initialize database connection
    if init_genesis_database():
        logger.info("GENESIS database connection setup complete")
    else:
        logger.info("GENESIS database connection setup skipped (not configured)")

    logger.info("GENESIS setup complete")
