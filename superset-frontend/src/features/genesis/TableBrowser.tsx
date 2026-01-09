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
import { useState, useEffect, useCallback, useMemo } from 'react';
import { SupersetClient, t, styled } from '@superset-ui/core';
import { Input, Table, Badge, Tooltip, Button, Space } from '@superset-ui/core/components';
import { Icons } from '@superset-ui/core/components/Icons';
import { useToasts } from 'src/components/MessageToasts/withToasts';
import type {
  GenesisTableMetadata,
  GenesisSearchResult,
  GenesisTableInfo,
} from './types';

const { Search } = Input;

const StyledContainer = styled.div`
  ${({ theme }) => `
    padding: ${theme.grid * 6}px;
    background-color: ${theme.colors.grayscale.light5};
    min-height: calc(100vh - 100px);

    .page-header {
      margin-bottom: ${theme.grid * 6}px;

      h2 {
        font-size: ${theme.typography.sizes.xl}px;
        font-weight: ${theme.typography.weights.bold};
        margin-bottom: ${theme.grid * 2}px;
      }

      .description {
        color: ${theme.colors.grayscale.base};
        font-size: ${theme.typography.sizes.m}px;
      }
    }

    .search-section {
      margin-bottom: ${theme.grid * 4}px;
      background: white;
      padding: ${theme.grid * 4}px;
      border-radius: ${theme.borderRadius}px;
      box-shadow: 0 1px 2px ${theme.colors.grayscale.light2};
    }

    .table-section {
      background: white;
      border-radius: ${theme.borderRadius}px;
      box-shadow: 0 1px 2px ${theme.colors.grayscale.light2};
      padding: ${theme.grid * 4}px;
    }

    .freshness-indicator {
      display: inline-flex;
      align-items: center;
      gap: ${theme.grid}px;
    }

    .action-button {
      color: ${theme.colors.primary.base};
      cursor: pointer;
      &:hover {
        color: ${theme.colors.primary.dark1};
      }
    }
  `}
`;

interface TableBrowserProps {
  addDangerToast: (msg: string) => void;
  addSuccessToast: (msg: string) => void;
}

export default function TableBrowser({
  addDangerToast,
  addSuccessToast,
}: TableBrowserProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [searchResults, setSearchResults] = useState<GenesisSearchResult[]>([]);
  const [metadata, setMetadata] = useState<Record<string, GenesisTableMetadata>>({});
  const [refreshing, setRefreshing] = useState<Record<string, boolean>>({});

  // Load metadata on mount
  useEffect(() => {
    loadMetadata();
  }, []);

  const loadMetadata = useCallback(async () => {
    try {
      const response = await SupersetClient.get({
        endpoint: '/api/v1/genesis/metadata',
      });

      const metadataMap: Record<string, GenesisTableMetadata> = {};
      response.json.result.forEach((item: GenesisTableMetadata) => {
        metadataMap[item.table_code] = item;
      });
      setMetadata(metadataMap);
    } catch (error) {
      console.error('Failed to load metadata:', error);
      addDangerToast(t('Failed to load GENESIS table metadata'));
    }
  }, [addDangerToast]);

  const handleSearch = useCallback(async (value: string) => {
    if (!value || value.length < 2) {
      setSearchResults([]);
      return;
    }

    setLoading(true);
    try {
      const response = await SupersetClient.get({
        endpoint: `/api/v1/genesis/search?q=${encodeURIComponent(value)}`,
      });

      setSearchResults(response.json.result);
    } catch (error) {
      console.error('Search failed:', error);
      addDangerToast(t('Failed to search GENESIS tables'));
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  }, [addDangerToast]);

  const handleRefresh = useCallback(async (tableCode: string) => {
    setRefreshing(prev => ({ ...prev, [tableCode]: true }));
    try {
      const response = await SupersetClient.post({
        endpoint: `/api/v1/genesis/refresh/${tableCode}`,
      });

      if (response.json.status === 'success') {
        addSuccessToast(t('Table data refreshed successfully'));
        // Reload metadata to get updated timestamp
        await loadMetadata();
      } else {
        addDangerToast(t('Failed to refresh table data'));
      }
    } catch (error) {
      console.error('Refresh failed:', error);
      addDangerToast(t('Failed to refresh table data'));
    } finally {
      setRefreshing(prev => ({ ...prev, [tableCode]: false }));
    }
  }, [addDangerToast, addSuccessToast, loadMetadata]);

  const tableData: GenesisTableInfo[] = useMemo(() => {
    return searchResults.map(result => ({
      ...result,
      metadata: metadata[result.code],
      is_loaded: !!metadata[result.code],
    }));
  }, [searchResults, metadata]);

  const getFreshnessDisplay = (item: GenesisTableInfo) => {
    if (!item.metadata || !item.metadata.last_updated) {
      return <Badge status="default" text={t('Not loaded')} />;
    }

    const { age_days, is_stale, status } = item.metadata;

    if (status === 'failed') {
      return (
        <Tooltip title={item.metadata.error_message || t('Load failed')}>
          <Badge status="error" text={t('Failed')} />
        </Tooltip>
      );
    }

    if (is_stale) {
      return (
        <Tooltip title={t('Data is over 90 days old')}>
          <Badge status="warning" text={t(`${age_days} days old`)} />
        </Tooltip>
      );
    }

    if (age_days !== null && age_days > 30) {
      return (
        <Badge status="processing" text={t(`${age_days} days old`)} />
      );
    }

    return <Badge status="success" text={t('Up to date')} />;
  };

  const columns = [
    {
      title: t('Table Code'),
      dataIndex: 'code',
      key: 'code',
      width: 150,
    },
    {
      title: t('Description'),
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: t('Status'),
      key: 'status',
      width: 150,
      render: (_: any, record: GenesisTableInfo) => getFreshnessDisplay(record),
    },
    {
      title: t('Records'),
      key: 'records',
      width: 100,
      render: (_: any, record: GenesisTableInfo) =>
        record.metadata?.record_count?.toLocaleString() || '-',
    },
    {
      title: t('Actions'),
      key: 'actions',
      width: 100,
      render: (_: any, record: GenesisTableInfo) => (
        <Space>
          {record.is_loaded && (
            <Tooltip title={t('Refresh data')}>
              <Button
                type="link"
                size="small"
                loading={refreshing[record.code]}
                onClick={() => handleRefresh(record.code)}
                icon={<Icons.SyncOutlined />}
              />
            </Tooltip>
          )}
          {!record.is_loaded && (
            <Tooltip title={t('Load this table first using the genesis-loader')}>
              <Button type="link" size="small" disabled>
                {t('Not loaded')}
              </Button>
            </Tooltip>
          )}
        </Space>
      ),
    },
  ];

  return (
    <StyledContainer>
      <div className="page-header">
        <h2>{t('GENESIS Data Browser')}</h2>
        <p className="description">
          {t('Search and manage German Federal Statistical Office (Destatis) data tables')}
        </p>
      </div>

      <div className="search-section">
        <Search
          placeholder={t('Search for tables (e.g., population, GDP, unemployment)...')}
          onSearch={handleSearch}
          onChange={e => setSearchTerm(e.target.value)}
          value={searchTerm}
          loading={loading}
          allowClear
          size="large"
          enterButton
        />
      </div>

      <div className="table-section">
        <Table
          columns={columns}
          dataSource={tableData}
          loading={loading}
          rowKey="code"
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => t(`${total} tables found`),
          }}
          locale={{
            emptyText: searchTerm
              ? t('No tables found. Try a different search term.')
              : t('Enter a search term to find GENESIS tables.'),
          }}
        />
      </div>
    </StyledContainer>
  );
}
