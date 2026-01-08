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

"""Unit tests for GENESIS API client"""

import io
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest
import requests

from superset.genesis_client import (
    GenesisClient,
    GenesisClientError,
    fetch_genesis_data,
)


class TestGenesisClient:
    """Test GENESIS API client functionality"""

    def setup_method(self) -> None:
        """Set up test fixtures"""
        self.client = GenesisClient(
            username="test_user", password="test_pass", language="en"
        )

    def test_initialization(self) -> None:
        """Test client initialization with custom credentials"""
        assert self.client.username == "test_user"
        assert self.client.password == "test_pass"
        assert self.client.language == "en"
        assert self.client.BASE_URL == "https://www-genesis.destatis.de/genesisWS/rest/2020"

    def test_initialization_defaults(self) -> None:
        """Test client initialization with default credentials"""
        client = GenesisClient()
        assert client.username == "GAST"
        assert client.password == "GAST"
        assert client.language == "en"

    @patch("superset.genesis_client.requests.Session.post")
    def test_login_check_success(self, mock_post: Mock) -> None:
        """Test successful login check"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Status": {"Code": 0, "Content": "Login successful"}
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.client.login_check()

        assert result is True
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "helloworld/logincheck" in call_args[0][0]

    @patch("superset.genesis_client.requests.Session.post")
    def test_login_check_failure(self, mock_post: Mock) -> None:
        """Test failed login check"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Status": {"Code": 1, "Content": "Login failed"}
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.client.login_check()

        assert result is False

    @patch("superset.genesis_client.requests.Session.post")
    def test_login_check_exception(self, mock_post: Mock) -> None:
        """Test login check with request exception"""
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        result = self.client.login_check()

        assert result is False

    @patch("superset.genesis_client.requests.Session.post")
    def test_find_tables_success(self, mock_post: Mock) -> None:
        """Test finding tables with successful response"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Tables": {
                "Table": [
                    {"Code": "12411-0001", "Content": "Population of Germany"},
                    {"Code": "12411-0003", "Content": "Population by state"},
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.client.find_tables(search_term="population")

        assert len(result) == 2
        assert result[0]["Code"] == "12411-0001"
        assert result[1]["Code"] == "12411-0003"

    @patch("superset.genesis_client.requests.Session.post")
    def test_find_tables_single_result(self, mock_post: Mock) -> None:
        """Test finding tables with single result"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Tables": {"Table": {"Code": "12411-0001", "Content": "Population"}}
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.client.find_tables(search_term="12411-0001")

        assert len(result) == 1
        assert result[0]["Code"] == "12411-0001"

    @patch("superset.genesis_client.requests.Session.post")
    def test_find_tables_empty_result(self, mock_post: Mock) -> None:
        """Test finding tables with empty result"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"Status": {"Code": 0}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.client.find_tables(search_term="nonexistent")

        assert result == []

    @patch("superset.genesis_client.requests.Session.post")
    def test_get_table_data_success(self, mock_post: Mock) -> None:
        """Test getting table data with successful response"""
        csv_data = "Year;Value\n2020;100\n2021;110\n2022;120"
        mock_response = MagicMock()
        mock_response.text = csv_data
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.client.get_table_data("12411-0001")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert "Year" in result.columns
        assert "Value" in result.columns
        assert result["Year"].iloc[0] == 2020

    @patch("superset.genesis_client.requests.Session.post")
    def test_get_table_data_with_years(self, mock_post: Mock) -> None:
        """Test getting table data with year filters"""
        csv_data = "Year;Value\n2020;100\n2021;110"
        mock_response = MagicMock()
        mock_response.text = csv_data
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.client.get_table_data(
            "12411-0001", startyear="2020", endyear="2021"
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        # Verify the request was made with the correct parameters
        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["startyear"] == "2020"
        assert payload["endyear"] == "2021"

    @patch("superset.genesis_client.requests.Session.post")
    def test_get_table_data_request_error(self, mock_post: Mock) -> None:
        """Test getting table data with request error"""
        mock_post.side_effect = requests.exceptions.RequestException("API error")

        with pytest.raises(GenesisClientError) as exc_info:
            self.client.get_table_data("12411-0001")

        assert "API request failed" in str(exc_info.value)

    @patch("superset.genesis_client.requests.Session.post")
    def test_get_table_data_parse_error(self, mock_post: Mock) -> None:
        """Test getting table data with parse error"""
        mock_response = MagicMock()
        mock_response.text = "Invalid CSV data"
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with pytest.raises(GenesisClientError) as exc_info:
            self.client.get_table_data("12411-0001")

        assert "Failed to parse table data" in str(exc_info.value)

    @patch("superset.genesis_client.requests.Session.post")
    def test_list_cubes_success(self, mock_post: Mock) -> None:
        """Test listing cubes with successful response"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Cubes": {
                "Cube": [
                    {"Code": "12411", "Content": "Population cube"},
                    {"Code": "81000", "Content": "GDP cube"},
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.client.list_cubes()

        assert len(result) == 2
        assert result[0]["Code"] == "12411"
        assert result[1]["Code"] == "81000"

    @patch("superset.genesis_client.requests.Session.post")
    def test_list_cubes_single_result(self, mock_post: Mock) -> None:
        """Test listing cubes with single result"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Cubes": {"Cube": {"Code": "12411", "Content": "Population cube"}}
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.client.list_cubes(selection="12411")

        assert len(result) == 1
        assert result[0]["Code"] == "12411"

    @patch("superset.genesis_client.requests.Session.post")
    def test_get_cube_metadata(self, mock_post: Mock) -> None:
        """Test getting cube metadata"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "Cube": {
                "Code": "12411",
                "Content": "Population",
                "Variables": ["Year", "Region"],
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.client.get_cube_metadata("12411")

        assert result["Cube"]["Code"] == "12411"
        assert "Variables" in result["Cube"]

    @patch("superset.genesis_client.requests.Session.post")
    def test_get_modified_data_list(self, mock_post: Mock) -> None:
        """Test getting modified data with list response"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ModifiedData": [
                {"Code": "12411-0001", "LastUpdate": "2023-01-15"},
                {"Code": "81000-0001", "LastUpdate": "2023-01-20"},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.client.get_modified_data("2023-01-01")

        assert len(result) == 2
        assert result[0]["Code"] == "12411-0001"

    @patch("superset.genesis_client.requests.Session.post")
    def test_get_modified_data_single(self, mock_post: Mock) -> None:
        """Test getting modified data with single result"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "ModifiedData": {"Code": "12411-0001", "LastUpdate": "2023-01-15"}
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = self.client.get_modified_data("2023-01-01")

        assert len(result) == 1
        assert result[0]["Code"] == "12411-0001"

    @patch("superset.genesis_client.requests.Session.post")
    def test_make_request_error_handling(self, mock_post: Mock) -> None:
        """Test error handling in _make_request"""
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")

        with pytest.raises(GenesisClientError) as exc_info:
            self.client._make_request("test/endpoint")

        assert "API request failed" in str(exc_info.value)


class TestFetchGenesisData:
    """Test convenience function for fetching GENESIS data"""

    @patch("superset.genesis_client.GenesisClient.get_table_data")
    def test_fetch_genesis_data_default_credentials(
        self, mock_get_table_data: Mock
    ) -> None:
        """Test fetch_genesis_data with default credentials"""
        mock_df = pd.DataFrame({"Year": [2020, 2021], "Value": [100, 110]})
        mock_get_table_data.return_value = mock_df

        result = fetch_genesis_data("12411-0001")

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        mock_get_table_data.assert_called_once_with(
            table_name="12411-0001", startyear="", endyear=""
        )

    @patch("superset.genesis_client.GenesisClient.get_table_data")
    def test_fetch_genesis_data_with_credentials(
        self, mock_get_table_data: Mock
    ) -> None:
        """Test fetch_genesis_data with custom credentials"""
        mock_df = pd.DataFrame({"Year": [2020], "Value": [100]})
        mock_get_table_data.return_value = mock_df

        result = fetch_genesis_data(
            "12411-0001",
            username="custom_user",
            password="custom_pass",
            startyear="2020",
            endyear="2020",
        )

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        mock_get_table_data.assert_called_once_with(
            table_name="12411-0001", startyear="2020", endyear="2020"
        )

    @patch("superset.genesis_client.GenesisClient.get_table_data")
    def test_fetch_genesis_data_error(self, mock_get_table_data: Mock) -> None:
        """Test fetch_genesis_data with API error"""
        mock_get_table_data.side_effect = GenesisClientError("API error")

        with pytest.raises(GenesisClientError):
            fetch_genesis_data("invalid-table")
