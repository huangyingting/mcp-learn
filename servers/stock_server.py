import argparse
from fastmcp import FastMCP
import datetime
import json
import yfinance as yf
import math
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("stock")

stock_mcp = FastMCP("stock")

@stock_mcp.prompt()
def stock_summary(stock_data: str) -> str:
  """Prompt template for summarising stock price"""
  return f"""You are a helpful financial assistant designed to summarise stock data.
                Using the information below, summarise the pertintent points relevant to stock price movement
                Data {stock_data}"""

def fetch_yahoo_finance_data(stock_ticker: str, modules: str) -> dict:
  """Helper function to fetch data from Yahoo Finance API using yfinance
  
  Args:
      stock_ticker: Alphanumeric stock ticker symbol
      modules: Yahoo Finance API modules to request (used to determine what data to fetch)
      
  Returns:
      dict: The structured data mimicking Yahoo Finance API response format
  """
  try:
    ticker = yf.Ticker(stock_ticker)
    
    # Map modules to yfinance data
    result = {}
    
    if 'incomeStatementHistory' in modules or 'incomeStatementHistoryQuarterly' in modules:
      # Get income statement data
      result['incomeStatementHistory'] = {'incomeStatementHistory': []}
      result['incomeStatementHistoryQuarterly'] = {'incomeStatementHistory': []}
      
      # Annual income statements
      annual = ticker.income_stmt
      if not annual.empty:
        for col in annual.columns:
          date_timestamp = int(col.timestamp())
          statement = {
            'endDate': {'raw': date_timestamp},
            'totalRevenue': {'raw': annual.loc['Total Revenue', col] if 'Total Revenue' in annual.index else None},
            'costOfRevenue': {'raw': annual.loc['Cost Of Revenue', col] if 'Cost Of Revenue' in annual.index else None},
            'grossProfit': {'raw': annual.loc['Gross Profit', col] if 'Gross Profit' in annual.index else None},
            'operatingIncome': {'raw': annual.loc['Operating Income', col] if 'Operating Income' in annual.index else None},
            'netIncome': {'raw': annual.loc['Net Income', col] if 'Net Income' in annual.index else None}
          }
          result['incomeStatementHistory']['incomeStatementHistory'].append(statement)
      
      # Quarterly income statements
      quarterly = ticker.quarterly_income_stmt
      if not quarterly.empty:
        for col in quarterly.columns:
          date_timestamp = int(col.timestamp())
          statement = {
            'endDate': {'raw': date_timestamp},
            'totalRevenue': {'raw': quarterly.loc['Total Revenue', col] if 'Total Revenue' in quarterly.index else None},
            'costOfRevenue': {'raw': quarterly.loc['Cost Of Revenue', col] if 'Cost Of Revenue' in quarterly.index else None},
            'grossProfit': {'raw': quarterly.loc['Gross Profit', col] if 'Gross Profit' in quarterly.index else None},
            'operatingIncome': {'raw': quarterly.loc['Operating Income', col] if 'Operating Income' in quarterly.index else None},
            'netIncome': {'raw': quarterly.loc['Net Income', col] if 'Net Income' in quarterly.index else None}
          }
          result['incomeStatementHistoryQuarterly']['incomeStatementHistory'].append(statement)
    
    return result
  except Exception as e:
    print(f"Error fetching data with yfinance: {e}")
    return None

def fetch_yahoo_finance_chart(stock_ticker: str, interval: str = "1d", range_period: str = "1mo") -> dict:
  """Helper function to fetch chart data using yfinance
  
  Args:
      stock_ticker: Alphanumeric stock ticker symbol
      interval: Data interval (e.g., "1d" for daily)
      range_period: Time range (e.g., "1mo" for one month)
      
  Returns:
      dict: The parsed chart data in a structure compatible with the original API
  
  Raises:
      Exception: If there's an error in the request
  """
  try:
    # Convert Yahoo Finance API period to yfinance period
    period_map = {
      "1d": "1d",
      "5d": "5d",
      "7d": "7d", 
      "1mo": "1mo",
      "3mo": "3mo",
      "6mo": "6mo",
      "1y": "1y",
      "2y": "2y",
      "5y": "5y",
      "max": "max"
    }
    
    period = period_map.get(range_period, "1mo")
    
    # Get historical data using yfinance
    ticker = yf.Ticker(stock_ticker)
    hist = ticker.history(period=period, interval=interval)
    
    if hist.empty:
      return None
    
    # Format data to match the structure expected by the original code
    result = {
      'timestamp': [int(date.timestamp()) for date in hist.index],
      'indicators': {
        'quote': [{
          'close': hist['Close'].tolist()
        }]
      }
    }
    
    return result
  except Exception as e:
    print(f"Error fetching chart data with yfinance: {e}")
    return None

@stock_mcp.tool()
def stock_price(stock_ticker: str, start_date: str = None, end_date: str = None) -> str:
  """
  Tool to get historical stock price information for a given ticker and optional date range.

  Args:
      stock_ticker: Stock ticker symbol (e.g., "AAPL").
      start_date: Optional start date in YYYY-MM-DD format (e.g., "2023-07-01").
      end_date: Optional end date in YYYY-MM-DD format (e.g., "2023-07-25").
          - If both start_date and end_date are provided, returns prices for that range.
          - If neither is provided, returns prices for the last 7 days.

  Returns:
      str: Human-readable summary of stock price data.
  """
  try:
      # Validate stock ticker
      ticker = yf.Ticker(stock_ticker)
      # Quick check to see if the ticker is valid
      if not ticker.info or ticker.info.get('regularMarketPrice') is None:
          return f"Invalid ticker symbol: {stock_ticker}. Please provide a valid stock ticker."
      
      # If date range is provided, fetch data for that range
      if start_date and end_date:
          try:
              # Parse the dates
              start = datetime.datetime.strptime(start_date, '%Y-%m-%d')
              end = datetime.datetime.strptime(end_date, '%Y-%m-%d')
              
              # Check if end date is after start date
              if end <= start:
                  return "End date must be after start date."
                  
              # Check if dates are in the future
              today = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
              if start > today or end > today:
                  return "Date cannot be in the future."
              
              # Calculate days between dates to determine appropriate range
              days_diff = (end - start).days
              
              # Map to Yahoo Finance range values
              if days_diff <= 5:
                  range_period = "5d"
              elif days_diff <= 30:
                  range_period = "1mo"
              elif days_diff <= 90:
                  range_period = "3mo"
              elif days_diff <= 180:
                  range_period = "6mo"
              elif days_diff <= 365:
                  range_period = "1y"
              elif days_diff <= 730:
                  range_period = "2y"
              else:
                  range_period = "5y"
              
              result = fetch_yahoo_finance_chart(stock_ticker, interval="1d", range_period=range_period)
          except ValueError:
              return "Invalid date format. Please use YYYY-MM-DD format."
      else:
          # Default to 7 days if no date range is provided
          range_period = "7d"
          result = fetch_yahoo_finance_chart(stock_ticker, interval="1d", range_period=range_period)
      
      if result and 'timestamp' in result and 'indicators' in result:
          timestamps = result['timestamp']
          close_prices = result['indicators']['quote'][0]['close']
          
          # Create a series-like representation of the closing prices
          price_data = {}
          for i, ts in enumerate(timestamps):
              if i < len(close_prices) and close_prices[i] is not None:  # Skip None values and check bounds
                  date_str = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                  price_data[date_str] = close_prices[i]
          
          # If no data points were found
          if not price_data:
              return f"No price data available for {stock_ticker} in the specified period."
          
          # If date range was provided, filter to the specified range
          if start_date and end_date:
              filtered_data = {}
              start = datetime.datetime.strptime(start_date, '%Y-%m-%d')
              end = datetime.datetime.strptime(end_date, '%Y-%m-%d')
              
              for d in price_data:
                  curr_date = datetime.datetime.strptime(d, '%Y-%m-%d')
                  if start <= curr_date <= end:
                      filtered_data[d] = price_data[d]
              
              # Calculate percentage change when there are multiple data points
              price_points = list(filtered_data.items())
              percentage_change = ""
              if len(price_points) >= 2:
                  first_price = price_points[0][1]
                  last_price = price_points[-1][1]
                  change = ((last_price - first_price) / first_price) * 100
                  change_direction = "up" if change >= 0 else "down"
                  percentage_change = f"\nPrice changed {change_direction} {abs(change):.2f}% over this period."
              
              # Format the date range output
              if filtered_data:
                  price_str = '\n'.join([f"{d}: ${filtered_data[d]:.2f}" for d in sorted(filtered_data.keys())])
                  return f"Stock price for {stock_ticker} from {start_date} to {end_date}:\n{price_str}{percentage_change}"
              else:
                  return f"No data available for {stock_ticker} in the date range {start_date} to {end_date}"
          
          # For the default case (last 7 days)
          else:
              # Calculate percentage change for the period
              sorted_dates = sorted(price_data.keys())
              percentage_change = ""
              if len(sorted_dates) >= 2:
                  first_date = sorted_dates[0]
                  last_date = sorted_dates[-1]
                  change = ((price_data[last_date] - price_data[first_date]) / price_data[first_date]) * 100
                  change_direction = "up" if change >= 0 else "down"
                  percentage_change = f"\nPrice changed {change_direction} {abs(change):.2f}% over the last 7 days."
              
              price_str = '\n'.join([f"{d}: ${price_data[d]:.2f}" for d in sorted_dates])
              return f"Stock price over the last 7 days for {stock_ticker}:\n{price_str}{percentage_change}"
      else:
          return f"Could not retrieve price data for {stock_ticker}. The stock symbol may be invalid or there may be no data available."
  except Exception as e:
      return f"Error retrieving stock price for {stock_ticker}: {str(e)}"

@stock_mcp.tool()
def stock_info(stock_ticker: str) -> str:
    """
    Tool to fetch fundamental information about a stock ticker from Yahoo Finance.
    
    Args:
        stock_ticker: Stock ticker symbol (e.g., "AAPL", "MSFT").
    
    Returns:
        str: A formatted string containing key information about the company including:
             company name, industry, sector, market cap, price metrics, dividend information,
             and business summary.
    """
    try:
        # Get stock information using yfinance
        ticker = yf.Ticker(stock_ticker)
        
        # Extract relevant information
        company_info = ticker.info
        
        # Select only the most relevant fields
        relevant_keys = [
            'shortName', 'longName', 'industry', 'sector', 'website', 
            'marketCap', 'previousClose', 'open', 'dayLow', 'dayHigh',
            'fiftyTwoWeekLow', 'fiftyTwoWeekHigh', 'volume', 'averageVolume',
            'dividendRate', 'dividendYield', 'trailingPE', 'forwardPE',
            'city', 'state', 'country', 'fullTimeEmployees', 'longBusinessSummary'
        ]
        
        # Format the information in a more readable way
        formatted_info = []
        
        # First add company name and key financial info
        if 'longName' in company_info:
            formatted_info.append(f"Company: {company_info.get('longName')}")
        elif 'shortName' in company_info:
            formatted_info.append(f"Company: {company_info.get('shortName')}")
            
        # Add other key information
        for key in relevant_keys:
            if key in company_info and company_info[key] is not None:
                # Format some fields specially
                if key == 'marketCap':
                    value = f"${company_info[key]/1000000000:.1f}B" if company_info[key] < 1000000000000 else f"${company_info[key]/1000000000000:.1f}T"
                    formatted_info.append(f"Market Cap: {value}")
                elif key == 'fiftyTwoWeekLow' and 'fiftyTwoWeekHigh' in company_info:
                    formatted_info.append(f"52 Week Range: ${company_info['fiftyTwoWeekLow']:.2f} - ${company_info['fiftyTwoWeekHigh']:.2f}")
                elif key == 'fiftyTwoWeekHigh':
                    # Skip as it's handled with fiftyTwoWeekLow
                    pass
                elif key == 'dividendYield' and company_info[key]:
                    formatted_info.append(f"Dividend Yield: {company_info[key]*100:.2f}%")
                elif key == 'longBusinessSummary':
                    formatted_info.append(f"\nBusiness Summary:\n{company_info[key]}")
                elif key not in ['shortName', 'longName']:  # Avoid duplication
                    # Format the key for better readability
                    formatted_key = ' '.join(word.capitalize() for word in key.split('_'))
                    formatted_key = ''.join(word[0].upper() + word[1:] for word in formatted_key.split())
                    formatted_info.append(f"{formatted_key}: {company_info[key]}")
        
        if not formatted_info:
            return f"No detailed information available for {stock_ticker}"
            
        return f"Background information for {stock_ticker}:\n" + "\n".join(formatted_info)
    except AttributeError:
        return f"Error: Invalid ticker symbol '{stock_ticker}' or information not available"
    except Exception as e:
        logger.error(f"Error in stock_info for {stock_ticker}: {str(e)}")
        return f"Error retrieving stock information for {stock_ticker}: {str(e)}"

@stock_mcp.tool()
def income_statement(stock_ticker: str, period: str = "quarterly") -> str:
    """
    Tool to get the income statement for a given stock ticker, supporting quarterly or yearly data.

    Args:
        stock_ticker: Alphanumeric stock ticker symbol (e.g., "AAPL", "MSFT").
        period: "quarterly" (default) or "yearly" to specify the type of income statement.

    Returns:
        str: Income statement data in JSON format, including key financial metrics:
            - Total Revenue
            - Cost of Revenue
            - Gross Profit
            - Operating Income
            - Net Income

        Example Response:
        Quarterly income statement for AAPL:
        [
          {
            "Date": "2023-06-30",
            "Total Revenue": "$81.80B",
            "Cost of Revenue": "$45.37B",
            "Gross Profit": "$36.43B",
            "Operating Income": "$23.12B",
            "Net Income": "$19.88B"
          }
        ]
    """
    try:
        # Determine which module to fetch
        if period == "yearly":
            module_key = "incomeStatementHistory"
            label = "Annual"
        else:
            module_key = "incomeStatementHistoryQuarterly"
            label = "Quarterly"

        result = fetch_yahoo_finance_data(stock_ticker, "incomeStatementHistory,incomeStatementHistoryQuarterly")

        if result and module_key in result:
            statements = result[module_key]['incomeStatementHistory']

            # Format the income statement data
            data = []
            for statement in statements:
                date = datetime.datetime.fromtimestamp(statement['endDate']['raw']).strftime('%Y-%m-%d')
                entry = {
                    'Date': date,
                    'Total Revenue': statement.get('totalRevenue', {}).get('raw', 'N/A'),
                    'Cost of Revenue': statement.get('costOfRevenue', {}).get('raw', 'N/A'),
                    'Gross Profit': statement.get('grossProfit', {}).get('raw', 'N/A'),
                    'Operating Income': statement.get('operatingIncome', {}).get('raw', 'N/A'),
                    'Net Income': statement.get('netIncome', {}).get('raw', 'N/A')
                }
                # Clean up and format values
                for key, value in entry.items():
                    if value != 'N/A' and (value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value)))):
                        entry[key] = 'N/A'
                    elif key != 'Date' and isinstance(value, (int, float)):
                        entry[key] = f"${value/1_000_000:.2f}M" if abs(value) < 1_000_000_000 else f"${value/1_000_000_000:.2f}B"
                data.append(entry)

            # Sort data by date (newest first)
            data.sort(key=lambda x: x['Date'], reverse=True)

            if not data:
                return f"No {label.lower()} income statement data available for {stock_ticker}"

            # Only return the latest entry by default for quarterly
            if period == "quarterly":
                data = data[:1]

            formatted_data = json.dumps(data, indent=2)
            return f"{label} income statement for {stock_ticker}:\n{formatted_data}"
        else:
            return f"Could not retrieve {label.lower()} income statement for {stock_ticker}"
    except Exception as e:
        return f"Error retrieving income statement for {stock_ticker}: {str(e)}"

# Example usage:
# To run the server with sse transport "uv run stock_server.py -t sse"
if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="stock mcp server")
  parser.add_argument("--transport", "-t", choices=["stdio", "sse", "http"], default="stdio",
                      help="MCP transport to use (stdio or sse or http)")
  args = parser.parse_args()
  stock_mcp.run(transport=args.transport)
