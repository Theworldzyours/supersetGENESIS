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
"""Marshmallow schemas for GENESIS API endpoints."""

from marshmallow import fields, Schema


class GenesisTableMetadataSchema(Schema):
    """Schema for GENESIS table metadata."""

    table_code = fields.String(
        metadata={"description": "GENESIS table code (e.g., 12411-0001)"}
    )
    table_name = fields.String(
        metadata={"description": "SQL table name in database"}
    )
    description = fields.String(
        metadata={"description": "Human-readable table description"}
    )
    last_updated = fields.DateTime(
        metadata={"description": "Timestamp of last data update"}
    )
    record_count = fields.Integer(
        metadata={"description": "Number of records in table"}
    )
    status = fields.String(
        metadata={"description": "Load status: success, failed, or pending"}
    )
    error_message = fields.String(
        metadata={"description": "Error message if load failed"}, allow_none=True
    )
    created_at = fields.DateTime(
        metadata={"description": "Timestamp when table was first loaded"}
    )
    age_days = fields.Integer(
        metadata={"description": "Number of days since last update"}, allow_none=True
    )
    is_stale = fields.Boolean(
        metadata={"description": "Whether data is considered stale (> 90 days)"}
    )


class GenesisTableSearchResultSchema(Schema):
    """Schema for GENESIS table search result."""

    code = fields.String(metadata={"description": "GENESIS table code"})
    description = fields.String(metadata={"description": "Table description"})
    updated = fields.String(
        metadata={"description": "Last update date in GENESIS database"},
        allow_none=True,
    )


class GenesisMetadataListSchema(Schema):
    """Schema for list of GENESIS metadata."""

    count = fields.Integer(metadata={"description": "Total number of tables"})
    result = fields.List(fields.Nested(GenesisTableMetadataSchema))


class GenesisSearchResultsSchema(Schema):
    """Schema for GENESIS search results."""

    count = fields.Integer(metadata={"description": "Number of search results"})
    result = fields.List(fields.Nested(GenesisTableSearchResultSchema))


class GenesisRefreshResponseSchema(Schema):
    """Schema for GENESIS table refresh response."""

    message = fields.String(metadata={"description": "Status message"})
    table_code = fields.String(metadata={"description": "Table code that was refreshed"})
    status = fields.String(metadata={"description": "Refresh status: success or failed"})
