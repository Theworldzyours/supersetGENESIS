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
"""SQLAlchemy models for GENESIS integration."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase

from superset import db


class GenesisTableMetadata(db.Model):
    """
    Model for tracking GENESIS table metadata and freshness.

    Stores information about loaded GENESIS tables including when data
    was last updated, record counts, and load status.
    """

    __tablename__ = "genesis_table_metadata"

    table_code = Column(String(50), primary_key=True, nullable=False)
    table_name = Column(String(250), nullable=False)
    description = Column(Text, nullable=True)
    last_updated = Column(DateTime, nullable=True)
    record_count = Column(Integer, nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<GenesisTableMetadata {self.table_code}: "
            f"{self.table_name} ({self.status})>"
        )

    @property
    def is_stale(self) -> bool:
        """
        Check if the data is considered stale (> 90 days old).

        Returns:
            True if data is older than 90 days or never updated
        """
        if not self.last_updated:
            return True
        age_days = (datetime.utcnow() - self.last_updated).days
        return age_days > 90

    @property
    def age_days(self) -> int | None:
        """
        Get the age of the data in days.

        Returns:
            Number of days since last update, or None if never updated
        """
        if not self.last_updated:
            return None
        return (datetime.utcnow() - self.last_updated).days
