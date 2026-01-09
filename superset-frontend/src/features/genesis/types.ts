/**
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

/**
 * GENESIS table metadata from the backend API
 */
export interface GenesisTableMetadata {
  table_code: string;
  table_name: string;
  description: string;
  last_updated: string | null;
  record_count: number | null;
  status: 'success' | 'failed' | 'pending';
  error_message: string | null;
  created_at: string;
  age_days: number | null;
  is_stale: boolean;
}

/**
 * GENESIS table search result from the API
 */
export interface GenesisSearchResult {
  code: string;
  description: string;
  updated: string | null;
}

/**
 * API response for metadata list
 */
export interface GenesisMetadataListResponse {
  count: number;
  result: GenesisTableMetadata[];
}

/**
 * API response for search results
 */
export interface GenesisSearchResponse {
  count: number;
  result: GenesisSearchResult[];
}

/**
 * API response for table refresh
 */
export interface GenesisRefreshResponse {
  message: string;
  table_code: string;
  status: 'success' | 'failed';
}

/**
 * Combined table info (search result + metadata)
 */
export interface GenesisTableInfo extends GenesisSearchResult {
  metadata?: GenesisTableMetadata;
  is_loaded: boolean;
}
