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
"""CLI commands for GENESIS integration."""

import logging

import click
from flask.cli import with_appcontext

from superset.initialization.genesis_setup import setup_genesis
from superset.utils.decorators import transaction

logger = logging.getLogger(__name__)


@click.command()
@with_appcontext
@transaction()
def init_genesis() -> None:
    """Initialize GENESIS database connection.

    This command sets up the GENESIS German Federal Statistical Office
    database connection in Superset. It requires the SUPERSET_GENESIS_DB_URI
    environment variable to be set.

    Example:
        export SUPERSET_GENESIS_DB_URI="postgresql://genesis:genesis@localhost:5433/genesis"
        superset init-genesis
    """
    logger.info("Initializing GENESIS integration...")
    setup_genesis()
    logger.info("GENESIS initialization complete")
    click.echo("✅ GENESIS initialization complete!")
