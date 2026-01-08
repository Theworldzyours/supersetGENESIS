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
GENESIS REST API client for accessing German Federal Statistical Office data.

This module provides a Python client for the GENESIS database REST API,
which offers access to official German statistics including population data,
economic indicators, labor market statistics, and regional data.

API Documentation:
- English: https://www.destatis.de/EN/Service/OpenData/api-webservice.html
- OpenAPI spec: https://destatis.api.bund.dev/openapi.yaml

Note: As of July 2025, only POST requests are supported (GET and SOAP deprecated).
"""

import io
import logging
from typing import Any

import pandas as pd
import requests

logger = logging.getLogger(__name__)


class GenesisClientError(Exception):
    """Exception raised for GENESIS API errors."""

    pass


class GenesisClient:
    """
    Client for interacting with the GENESIS REST API.

    The GENESIS database provides access to official statistics from the
    German Federal Statistical Office (Destatis).

    Default credentials (GAST/GAST) provide public access with limited features.
    Users can register at https://www-genesis.destatis.de for full access.
    """

    BASE_URL = "https://www-genesis.destatis.de/genesisWS/rest/2020"

    def __init__(
        self, username: str = "GAST", password: str = "GAST", language: str = "en"
    ) -> None:
        """
        Initialize the GENESIS API client.

        Args:
            username: GENESIS API username (default: "GAST" for public access)
            password: GENESIS API password (default: "GAST" for public access)
            language: Language for API responses ("en" or "de", default: "en")
        """
        self.username = username
        self.password = password
        self.language = language
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def _make_request(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Make a POST request to the GENESIS API.

        Args:
            endpoint: API endpoint path (e.g., "catalogue/cubes")
            params: Additional parameters to include in the request payload

        Returns:
            JSON response from the API

        Raises:
            GenesisClientError: If the API request fails
        """
        url = f"{self.BASE_URL}/{endpoint}"
        payload = {
            "username": self.username,
            "password": self.password,
            "language": self.language,
        }

        if params:
            payload.update(params)

        try:
            logger.debug(f"Making POST request to {url} with payload: {payload}")
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GENESIS API request failed: {e}")
            raise GenesisClientError(f"API request failed: {e}") from e

    def login_check(self) -> bool:
        """
        Test API credentials by attempting a login check.

        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            response = self._make_request("helloworld/logincheck")
            # Check if the response indicates success
            if isinstance(response, dict):
                status = response.get("Status", {})
                if isinstance(status, dict):
                    return status.get("Code") == 0
            return False
        except GenesisClientError:
            return False

    def find_tables(
        self, search_term: str = "*", category: str = "all"
    ) -> list[dict[str, Any]]:
        """
        Search for tables/statistics in the GENESIS database.

        Args:
            search_term: Search term or pattern (default: "*" for all)
            category: Category to search in (default: "all")

        Returns:
            List of dictionaries containing table information

        Raises:
            GenesisClientError: If the API request fails
        """
        response = self._make_request(
            "catalogue/tables",
            {
                "selection": search_term,
                "searchcriterion": category,
                "type": "all",
            },
        )

        # Extract tables from the response
        if isinstance(response, dict) and "Tables" in response:
            tables = response["Tables"]
            if isinstance(tables, list):
                return tables
            if isinstance(tables, dict) and "Table" in tables:
                table_data = tables["Table"]
                return table_data if isinstance(table_data, list) else [table_data]

        return []

    def get_table_data(
        self,
        table_name: str,
        startyear: str = "",
        endyear: str = "",
        area: str = "all",
    ) -> pd.DataFrame:
        """
        Download table data as a pandas DataFrame.

        Args:
            table_name: Name/code of the table to retrieve
            startyear: Starting year for data (empty for all available)
            endyear: Ending year for data (empty for all available)
            area: Geographic area filter (default: "all")

        Returns:
            pandas DataFrame containing the table data

        Raises:
            GenesisClientError: If the API request fails
        """
        url = f"{self.BASE_URL}/data/tablefile"
        payload = {
            "username": self.username,
            "password": self.password,
            "language": self.language,
            "name": table_name,
            "area": area,
            "format": "ffcsv",  # Flat file CSV format
        }

        if startyear:
            payload["startyear"] = startyear
        if endyear:
            payload["endyear"] = endyear

        try:
            logger.debug(f"Downloading table {table_name} from GENESIS API")
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()

            # The response should be CSV data
            csv_data = response.text
            df = pd.read_csv(io.StringIO(csv_data), sep=";")

            logger.info(f"Successfully downloaded table {table_name} with {len(df)} rows")
            return df

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download table {table_name}: {e}")
            raise GenesisClientError(f"Failed to download table data: {e}") from e
        except Exception as e:
            logger.error(f"Failed to parse table {table_name} data: {e}")
            raise GenesisClientError(f"Failed to parse table data: {e}") from e

    def list_cubes(self, selection: str = "*") -> list[dict[str, Any]]:
        """
        List available data cubes in the GENESIS database.

        Args:
            selection: Selection pattern (default: "*" for all cubes)

        Returns:
            List of dictionaries containing cube information

        Raises:
            GenesisClientError: If the API request fails
        """
        response = self._make_request(
            "catalogue/cubes",
            {"selection": selection, "type": "all"},
        )

        # Extract cubes from the response
        if isinstance(response, dict) and "Cubes" in response:
            cubes = response["Cubes"]
            if isinstance(cubes, list):
                return cubes
            if isinstance(cubes, dict) and "Cube" in cubes:
                cube_data = cubes["Cube"]
                return cube_data if isinstance(cube_data, list) else [cube_data]

        return []

    def get_cube_metadata(self, cube_name: str) -> dict[str, Any]:
        """
        Get metadata for a specific data cube.

        Args:
            cube_name: Name/code of the cube

        Returns:
            Dictionary containing cube metadata

        Raises:
            GenesisClientError: If the API request fails
        """
        response = self._make_request(
            "metadata/cube",
            {"name": cube_name},
        )
        return response

    def get_modified_data(self, date: str) -> list[dict[str, Any]]:
        """
        Get datasets that have been modified since a specific date.

        Args:
            date: Date in format YYYY-MM-DD or DD.MM.YYYY

        Returns:
            List of dictionaries containing information about modified datasets

        Raises:
            GenesisClientError: If the API request fails
        """
        response = self._make_request(
            "catalogue/modifieddata",
            {"selection": date, "type": "all"},
        )

        # Extract modified data from the response
        if isinstance(response, dict) and "ModifiedData" in response:
            data = response["ModifiedData"]
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return [data]

        return []


def fetch_genesis_data(
    table_name: str,
    username: str = "GAST",
    password: str = "GAST",
    startyear: str = "",
    endyear: str = "",
) -> pd.DataFrame:
    """
    Convenience function to quickly fetch GENESIS data.

    Args:
        table_name: Name/code of the table to retrieve
        username: GENESIS API username (default: "GAST")
        password: GENESIS API password (default: "GAST")
        startyear: Starting year for data (empty for all available)
        endyear: Ending year for data (empty for all available)

    Returns:
        pandas DataFrame containing the table data

    Raises:
        GenesisClientError: If the API request fails

    Example:
        >>> df = fetch_genesis_data("12411-0001", startyear="2020", endyear="2023")
        >>> print(df.head())
    """
    client = GenesisClient(username=username, password=password)
    return client.get_table_data(
        table_name=table_name, startyear=startyear, endyear=endyear
    )
