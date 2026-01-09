---
title: GENESIS User Guide
---

# GENESIS Data Browser - User Guide

This guide shows end users how to work with German Federal Statistical Office data in Superset.

## Accessing GENESIS Data

### Step 1: Navigate to the Data Browser

1. Log into Superset
2. Click on the **Data** menu in the top navigation
3. Select **GENESIS Data**

You'll see the GENESIS Data Browser interface.

## Searching for Tables

### Using the Search Box

The search box helps you find specific German statistics:

**Example Searches:**
- Type `population` to find population statistics
- Type `GDP` or `wirtschaft` for economic data
- Type `arbeitslos` or `unemployment` for labor market data
- Type `preis` or `price` for inflation/price data
- Type table codes like `12411` for specific tables

**Tips:**
- Use simple keywords
- Try both English and German terms
- Minimum 2 characters required
- Results update as you type

### Understanding Search Results

Each result shows:
- **Table Code**: Official GENESIS identifier (e.g., 12411-0001)
- **Description**: What the table contains
- **Status**: Data freshness indicator
- **Records**: Number of rows in the table
- **Actions**: Buttons to refresh or manage data

## Data Freshness Indicators

The **Status** column uses color-coded badges:

- 🟢 **Up to date**: Data is less than 30 days old - ready to use
- 🔵 **Moderately old**: Data is 30-90 days old - still usable
- 🟡 **Stale**: Data is over 90 days old - consider refreshing
- 🔴 **Failed**: Data load failed - see error message
- ⚪ **Not loaded**: Table hasn't been loaded yet

**When to refresh:**
- Yellow badges (stale data)
- Before creating important dashboards
- When you need the latest statistics

## Refreshing Data

To update a table with the latest data from GENESIS:

1. Find the table in the browser
2. Click the **refresh icon** (🔄) in the Actions column
3. Wait for the refresh to complete (usually 10-30 seconds)
4. Check the updated timestamp

**Note:** Only loaded tables can be refreshed. New tables must first be loaded using the data loader script (ask your administrator).

## Creating Charts from GENESIS Data

Once you've found data you want to visualize:

### Step 1: Create a Dataset

1. Go to **Data → Datasets**
2. Click **+ Dataset**
3. Select database: **GENESIS (German Statistics)**
4. Choose your table (e.g., `population_germany`)
5. Click **Create Dataset and Create Chart**

### Step 2: Build Your Chart

The Chart Builder will open:

1. **Choose visualization type**:
   - Line Chart: For trends over time
   - Bar Chart: For comparisons
   - Table: For detailed data
   - Map: For regional data (if geographic info available)

2. **Configure the chart**:
   - **Dimensions**: Select columns to group by (e.g., Year, State)
   - **Metrics**: Choose what to measure (e.g., Population, GDP)
   - **Filters**: Narrow down the data

3. Click **Update Chart** to preview
4. Click **Save** when satisfied

### Step 3: Add to a Dashboard

1. After saving, click **Add to Dashboard**
2. Select an existing dashboard or create a new one
3. Arrange your charts
4. Click **Save** to publish

## Common Use Cases

### Tracking Population Trends

**Tables to use:**
- `population_germany` - Overall population
- `population_by_state` - State-by-state breakdown

**Chart suggestions:**
- Line chart showing population over time
- Bar chart comparing states
- Big number card showing current population

### Monitoring Economic Indicators

**Tables to use:**
- `gdp_quarterly` - Economic growth
- `consumer_price_index` - Inflation
- `foreign_trade_statistics` - Imports/exports

**Chart suggestions:**
- Line charts for trends
- Multiple metrics on one chart
- Year-over-year comparisons

### Analyzing Labor Market

**Tables to use:**
- `employment_by_sectors` - Where people work
- `unemployment_statistics` - Unemployment rates

**Chart suggestions:**
- Stacked bar charts by sector
- Trend lines for unemployment
- Pie charts for sector distribution

## Understanding the Data

### Table Structures

GENESIS tables typically include:
- **Time dimensions**: Year, Quarter, Month
- **Geographic dimensions**: Federal state (Bundesland), Region
- **Measurements**: Counts, percentages, indices
- **Metadata columns**:
  - `genesis_table_code`: Source table identifier
  - `genesis_table_description`: What the data represents

### Data Quality Notes

- Official statistics are typically final after initial publication
- Some tables are updated quarterly, others annually
- Check the data freshness indicator before making decisions
- Historical data is generally stable and complete

## Tips for Better Visualizations

### 1. Choose the Right Chart Type

- **Time series** → Line charts
- **Comparisons** → Bar charts
- **Proportions** → Pie charts
- **Geographic** → Maps (if data includes state/region)
- **Detailed analysis** → Tables

### 2. Use Filters Effectively

- Filter by recent years for current trends
- Filter by specific states for regional analysis
- Use date ranges to focus on relevant periods

### 3. Add Context

- Use chart titles that explain what's shown
- Add descriptions to help viewers understand
- Include data source information
- Note the date range of your data

### 4. Combine Multiple Charts

Create dashboards that tell a story:
- Population trends + economic indicators
- Employment + unemployment together
- Regional comparisons side-by-side

## Troubleshooting

### "No tables found" when searching

- Check your search term (try simpler keywords)
- Try both English and German terms
- Verify you're searching for tables that exist in GENESIS

### Refresh button is disabled

The table hasn't been loaded yet. Contact your administrator to load the table first using:
```bash
docker compose run genesis-loader
```

### Error message when refreshing

Common causes:
- GENESIS API is temporarily unavailable
- Network connectivity issues
- Invalid API credentials

Check with your administrator if errors persist.

### Data looks outdated

- Check the data freshness indicator
- Click refresh to get the latest data
- Note: Some statistics are published with delay (e.g., annual data released mid-next year)

## Getting Help

### For Users

- Ask your Superset administrator
- Check the full integration documentation
- Review example dashboards for ideas

### For Administrators

- See [GENESIS Integration Guide](genesis-integration.md) for technical details
- Check API logs for errors
- Verify environment variables are set correctly

## Example Dashboard Ideas

### Economic Dashboard
- GDP growth over time (line chart)
- Inflation rate (gauge or line chart)
- Trade balance (bar chart)
- Employment rate (big number)

### Demographics Dashboard
- Population by state (map or bar chart)
- Population growth trend (line chart)
- Age distribution (stacked bar)
- Birth/death rates (line chart)

### Regional Comparison Dashboard
- Side-by-side state comparisons
- Top/bottom performers (bar chart)
- Geographic visualization (map)
- Detailed breakdowns (table)

## Best Practices

1. **Check data freshness** before creating reports
2. **Refresh regularly** if using in production dashboards
3. **Document your charts** with clear titles and descriptions
4. **Test filters** to ensure they work as expected
5. **Share insights** with your team through dashboards

## Next Steps

- Explore available tables in the Data Browser
- Create your first chart with GENESIS data
- Build a dashboard combining multiple data sources
- Share your visualizations with colleagues

For more information, see the [GENESIS Integration Documentation](genesis-integration.md).
