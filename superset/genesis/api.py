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
"""REST API for GENESIS integration."""

import logging
import os
from datetime import datetime

from flask import request, Response
from flask_appbuilder.api import expose, protect, safe
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from superset import db
from superset.constants import MODEL_API_RW_METHOD_PERMISSION_MAP
from superset.extensions import event_logger
from superset.genesis_client import GenesisClient, GenesisClientError
from superset.genesis.models import GenesisTableMetadata
from superset.genesis.schemas import (
    GenesisMetadataListSchema,
    GenesisRefreshResponseSchema,
    GenesisSearchResultsSchema,
    GenesisTableMetadataSchema,
)
from superset.views.base_api import BaseSupersetApi, statsd_metrics

logger = logging.getLogger(__name__)


class GenesisRestApi(BaseSupersetApi):
    """REST API for GENESIS German Federal Statistical Office data."""

    method_permission_name = MODEL_API_RW_METHOD_PERMISSION_MAP
    allow_browser_login = True
    class_permission_name = "Genesis"
    resource_name = "genesis"
    openapi_spec_tag = "Genesis"
    openapi_spec_component_schemas = (
        GenesisTableMetadataSchema,
        GenesisMetadataListSchema,
        GenesisSearchResultsSchema,
        GenesisRefreshResponseSchema,
    )

    @expose("/metadata", methods=("GET",))
    @protect()
    @safe
    @statsd_metrics
    @event_logger.log_this_with_context(
        action=lambda self, *args, **kwargs: f"{self.__class__.__name__}.metadata_list",
        log_to_statsd=True,
    )
    def metadata_list(self) -> Response:
        """Get list of all loaded GENESIS tables with metadata.
        ---
        get:
          summary: Get list of GENESIS tables with metadata
          description: >-
            Returns a list of all GENESIS tables that have been loaded into the
            database, including their freshness information, record counts, and
            load status.
          responses:
            200:
              description: List of GENESIS table metadata
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/GenesisMetadataListSchema'
            401:
              $ref: '#/components/responses/401'
            500:
              $ref: '#/components/responses/500'
        """
        try:
            metadata_list = db.session.query(GenesisTableMetadata).all()

            result = []
            for metadata in metadata_list:
                result.append({
                    "table_code": metadata.table_code,
                    "table_name": metadata.table_name,
                    "description": metadata.description,
                    "last_updated": metadata.last_updated.isoformat()
                    if metadata.last_updated
                    else None,
                    "record_count": metadata.record_count,
                    "status": metadata.status,
                    "error_message": metadata.error_message,
                    "created_at": metadata.created_at.isoformat(),
                    "age_days": metadata.age_days,
                    "is_stale": metadata.is_stale,
                })

            return self.response(200, count=len(result), result=result)

        except Exception as ex:
            logger.exception("Error fetching GENESIS metadata")
            return self.response(500, message=str(ex))

    @expose("/metadata/<table_code>", methods=("GET",))
    @protect()
    @safe
    @statsd_metrics
    @event_logger.log_this_with_context(
        action=lambda self, *args, **kwargs: f"{self.__class__.__name__}.metadata_get",
        log_to_statsd=True,
    )
    def metadata_get(self, table_code: str) -> Response:
        """Get metadata for a specific GENESIS table.
        ---
        get:
          summary: Get metadata for a specific GENESIS table
          description: >-
            Returns detailed metadata for a single GENESIS table including
            freshness information, record count, and load status.
          parameters:
          - in: path
            schema:
              type: string
            name: table_code
            description: GENESIS table code (e.g., 12411-0001)
          responses:
            200:
              description: GENESIS table metadata
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/GenesisTableMetadataSchema'
            404:
              $ref: '#/components/responses/404'
            401:
              $ref: '#/components/responses/401'
            500:
              $ref: '#/components/responses/500'
        """
        try:
            metadata = db.session.query(GenesisTableMetadata).filter_by(
                table_code=table_code
            ).first()

            if not metadata:
                return self.response(
                    404, message=f"Table {table_code} not found in metadata"
                )

            result = {
                "table_code": metadata.table_code,
                "table_name": metadata.table_name,
                "description": metadata.description,
                "last_updated": metadata.last_updated.isoformat()
                if metadata.last_updated
                else None,
                "record_count": metadata.record_count,
                "status": metadata.status,
                "error_message": metadata.error_message,
                "created_at": metadata.created_at.isoformat(),
                "age_days": metadata.age_days,
                "is_stale": metadata.is_stale,
            }

            return self.response(200, result=result)

        except Exception as ex:
            logger.exception(f"Error fetching metadata for table {table_code}")
            return self.response(500, message=str(ex))

    @expose("/search", methods=("GET",))
    @protect()
    @safe
    @statsd_metrics
    @event_logger.log_this_with_context(
        action=lambda self, *args, **kwargs: f"{self.__class__.__name__}.search",
        log_to_statsd=True,
    )
    def search(self) -> Response:
        """Search for GENESIS tables by keyword.
        ---
        get:
          summary: Search GENESIS database for tables
          description: >-
            Searches the GENESIS database for tables matching the given search term.
            Returns table codes and descriptions from the GENESIS API.
          parameters:
          - in: query
            schema:
              type: string
            name: q
            description: Search term (e.g., "population", "GDP")
            required: true
          responses:
            200:
              description: Search results
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/GenesisSearchResultsSchema'
            400:
              $ref: '#/components/responses/400'
            401:
              $ref: '#/components/responses/401'
            500:
              $ref: '#/components/responses/500'
        """
        search_term = request.args.get("q", type=str)

        if not search_term:
            return self.response(400, message="Search term 'q' is required")

        try:
            # Get GENESIS API credentials from environment
            username = os.getenv("GENESIS_USERNAME", "GAST")
            password = os.getenv("GENESIS_PASSWORD", "GAST")

            # Initialize client and search
            client = GenesisClient(username=username, password=password)
            tables = client.find_tables(search_term)

            # Format results
            result = []
            for table in tables:
                result.append({
                    "code": table.get("Code", ""),
                    "description": table.get("Content", ""),
                    "updated": table.get("Updated", None),
                })

            return self.response(200, count=len(result), result=result)

        except GenesisClientError as ex:
            logger.exception(f"GENESIS API error during search for '{search_term}'")
            return self.response(500, message=f"GENESIS API error: {str(ex)}")
        except Exception as ex:
            logger.exception(f"Error searching GENESIS for '{search_term}'")
            return self.response(500, message=str(ex))

    @expose("/refresh/<table_code>", methods=("POST",))
    @protect()
    @safe
    @statsd_metrics
    @event_logger.log_this_with_context(
        action=lambda self, *args, **kwargs: f"{self.__class__.__name__}.refresh",
        log_to_statsd=True,
    )
    def refresh(self, table_code: str) -> Response:
        """Refresh data for a specific GENESIS table.
        ---
        post:
          summary: Refresh data for a GENESIS table
          description: >-
            Fetches the latest data from the GENESIS API for the specified table
            and updates the database. This operation may take several seconds
            depending on table size.
          parameters:
          - in: path
            schema:
              type: string
            name: table_code
            description: GENESIS table code (e.g., 12411-0001)
          responses:
            200:
              description: Refresh completed successfully
              content:
                application/json:
                  schema:
                    $ref: '#/components/schemas/GenesisRefreshResponseSchema'
            404:
              $ref: '#/components/responses/404'
            401:
              $ref: '#/components/responses/401'
            500:
              $ref: '#/components/responses/500'
        """
        try:
            # Check if table exists in metadata
            metadata = db.session.query(GenesisTableMetadata).filter_by(
                table_code=table_code
            ).first()

            if not metadata:
                return self.response(
                    404, message=f"Table {table_code} not found in metadata"
                )

            # Get database URI and GENESIS credentials
            db_uri = os.getenv("SUPERSET_GENESIS_DB_URI")
            username = os.getenv("GENESIS_USERNAME", "GAST")
            password = os.getenv("GENESIS_PASSWORD", "GAST")

            if not db_uri:
                return self.response(
                    500,
                    message="SUPERSET_GENESIS_DB_URI environment variable not set",
                )

            # Initialize GENESIS client
            client = GenesisClient(username=username, password=password)

            # Fetch data from GENESIS API
            logger.info(f"Refreshing data for table {table_code}")
            df = client.get_table_data(table_code)

            if df.empty:
                metadata.status = "failed"
                metadata.error_message = "No data returned from API"
                db.session.commit()
                return self.response(
                    500,
                    message=f"No data returned for table {table_code}",
                    table_code=table_code,
                    status="failed",
                )

            # Load data into GENESIS database (not Superset's database)
            genesis_engine = create_engine(db_uri)
            df.to_sql(
                metadata.table_name,
                genesis_engine,
                if_exists="replace",
                index=False,
                chunksize=1000,
            )

            # Update metadata
            metadata.last_updated = datetime.utcnow()
            metadata.record_count = len(df)
            metadata.status = "success"
            metadata.error_message = None
            db.session.commit()

            logger.info(
                f"Successfully refreshed table {table_code} with {len(df)} records"
            )

            return self.response(
                200,
                message=f"Successfully refreshed {len(df)} records",
                table_code=table_code,
                status="success",
            )

        except GenesisClientError as ex:
            logger.exception(f"GENESIS API error refreshing table {table_code}")
            if metadata:
                metadata.status = "failed"
                metadata.error_message = f"GENESIS API error: {str(ex)}"
                db.session.commit()
            return self.response(
                500,
                message=f"GENESIS API error: {str(ex)}",
                table_code=table_code,
                status="failed",
            )
        except Exception as ex:
            logger.exception(f"Error refreshing table {table_code}")
            if metadata:
                metadata.status = "failed"
                metadata.error_message = f"Refresh error: {str(ex)}"
                db.session.commit()
            return self.response(
                500,
                message=str(ex),
                table_code=table_code,
                status="failed",
            )
