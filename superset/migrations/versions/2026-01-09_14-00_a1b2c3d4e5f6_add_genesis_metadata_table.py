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
"""add_genesis_metadata_table

Revision ID: a1b2c3d4e5f6
Revises: f5b5f88d8526
Create Date: 2026-01-09 14:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import mysql

from superset.migrations.shared.utils import create_table, drop_table

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "f5b5f88d8526"


def upgrade():
    """
    Create genesis_table_metadata table to track GENESIS data freshness.

    This table stores metadata about loaded GENESIS tables including:
    - When data was last updated
    - Number of records loaded
    - Load status and error messages
    """
    create_table(
        "genesis_table_metadata",
        sa.Column("table_code", sa.String(length=50), nullable=False),
        sa.Column("table_name", sa.String(length=250), nullable=False),
        sa.Column(
            "description",
            sa.Text().with_variant(mysql.MEDIUMTEXT(), "mysql"),
            nullable=True,
        ),
        sa.Column("last_updated", sa.DateTime(), nullable=True),
        sa.Column("record_count", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, default="pending"),
        sa.Column(
            "error_message",
            sa.Text().with_variant(mysql.MEDIUMTEXT(), "mysql"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("table_code"),
    )


def downgrade():
    """Remove genesis_table_metadata table."""
    drop_table("genesis_table_metadata")
