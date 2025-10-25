"""
Portfolio Backtesting Module
Provides comprehensive historical performance analysis for cryptocurrency portfolios.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class Backtester:
    """
    Comprehensive backtesting engine for cryptocurrency portfolios
    """
    
    def __init__(self, 
                 symbols: List[str], 
                 weights: Dict[str, float], 
                 initial_investment: float,
                 start_date: str, 
                 end_date: str,
                 rebalance_frequency: str = "monthly"):
        """
        Initialize the backtester
        
        Args:
            symbols: List of cryptocurrency symbols (e.g., ['BTC-USD', 'ETH-USD'])
            weights: Portfolio weights dictionary (e.g., {'BTC-USD': 0.6, 'ETH-USD': 0.4})
            initial_investment: Initial portfolio value in USD
            start_date: Start date for backtesting (YYYY-MM-DD)
            end_date: End date for backtesting (YYYY-MM-DD)
            rebalance_frequency: How often to rebalance ('daily', 'weekly', 'monthly', 'quarterly', 'never')
        """
        self.symbols = symbols
        self.weights = weights
        self.initial_investment = initial_investment
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.rebalance_frequency = rebalance_frequency
        
        # Data storage
        self.price_data = None
        self.portfolio_values = None
        self.returns = None
        self.metrics = None
        
        # Validation
        self._validate_inputs()
        
    def _validate_inputs(self):
        """Validate input parameters"""
        if not self.symbols:
            raise ValueError("Symbols list cannot be empty")
        
        if not self.weights:
            raise ValueError("Weights dictionary cannot be empty")
        
        # Ensure weights sum to approximately 1
        total_weight = sum(self.weights.values())
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total_weight:.4f}")
        
        # Ensure all symbols have weights
        for symbol in self.symbols:
            if symbol not in self.weights:
                raise ValueError(f"Weight not provided for symbol: {symbol}")
        
        if self.initial_investment <= 0:
            raise ValueError("Initial investment must be positive")
        
        if self.start_date >= self.end_date:
            raise ValueError("Start date must be before end date")
    
    def fetch_historical_data(self) -> pd.DataFrame:
        """
        Fetch historical price data for all symbols
        
        Returns:
            DataFrame with historical adjusted close prices
        """
        try:
            print(f"Fetching historical data for {len(self.symbols)} symbols...")
            print(f"Period: {self.start_date.date()} to {self.end_date.date()}")
            
            # Download data with some buffer before start date for calculations
            buffer_start = self.start_date - timedelta(days=30)
            
            # Download price data - note: yfinance changed to auto_adjust=True by default
            data = yf.download(
                self.symbols, 
                start=buffer_start.strftime('%Y-%m-%d'),
                end=(self.end_date + timedelta(days=1)).strftime('%Y-%m-%d'),
                progress=False,
                auto_adjust=False  # This ensures we get Adj Close
            )
            
            print(f"Downloaded data shape: {data.shape}")
            print(f"Columns: {data.columns}")
            
            # Handle different data structures based on number of symbols
            if len(self.symbols) == 1:
                # Single symbol case
                if isinstance(data.columns, pd.MultiIndex):
                    # Try Adj Close first, then Close
                    try:
                        self.price_data = data[('Adj Close', self.symbols[0])].to_frame()
                        self.price_data.columns = [self.symbols[0]]
                    except KeyError:
                        try:
                            self.price_data = data[('Close', self.symbols[0])].to_frame()
                            self.price_data.columns = [self.symbols[0]]
                        except KeyError:
                            # Use the first price column available
                            price_cols = [col for col in data.columns if col[0] in ['Adj Close', 'Close', 'Open']]
                            if price_cols:
                                self.price_data = data[price_cols[0]].to_frame()
                                self.price_data.columns = [self.symbols[0]]
                            else:
                                raise ValueError("No suitable price column found")
                else:
                    # Non-MultiIndex case
                    if 'Adj Close' in data.columns:
                        self.price_data = data[['Adj Close']].copy()
                    elif 'Close' in data.columns:
                        self.price_data = data[['Close']].copy()
                    else:
                        # Use first column
                        self.price_data = data.iloc[:, 0:1].copy()
                    self.price_data.columns = [self.symbols[0]]
            else:
                # Multiple symbols case
                if isinstance(data.columns, pd.MultiIndex):
                    # Try to extract price data for all symbols
                    try:
                        self.price_data = data['Adj Close'].copy()
                    except KeyError:
                        try:
                            self.price_data = data['Close'].copy()
                        except KeyError:
                            # Find any price column and use it
                            available_price_types = [level for level in data.columns.levels[0] 
                                                   if level in ['Adj Close', 'Close', 'Open', 'High', 'Low']]
                            if available_price_types:
                                self.price_data = data[available_price_types[0]].copy()
                            else:
                                raise ValueError("No suitable price columns found")
                else:
                    # Assume data is already in the right format
                    self.price_data = data.copy()
                    if len(self.price_data.columns) != len(self.symbols):
                        self.price_data = self.price_data.iloc[:, :len(self.symbols)]
                        self.price_data.columns = self.symbols
            
            # Ensure we have a DataFrame
            if not isinstance(self.price_data, pd.DataFrame):
                self.price_data = pd.DataFrame(self.price_data)
            
            # Ensure column names match symbols
            if len(self.price_data.columns) == len(self.symbols):
                self.price_data.columns = self.symbols
            
            # Filter to actual backtesting period
            self.price_data = self.price_data[
                (self.price_data.index >= self.start_date) & 
                (self.price_data.index <= self.end_date)
            ]
            
            # Remove symbols with insufficient data
            min_data_points = len(self.price_data) * 0.8
            self.price_data = self.price_data.dropna(axis=1, thresh=min_data_points)
            
            # Update symbols and weights to only include valid data
            valid_symbols = list(self.price_data.columns)
            invalid_symbols = set(self.symbols) - set(valid_symbols)
            
            if invalid_symbols:
                print(f"Warning: Removing symbols with insufficient data: {invalid_symbols}")
                
                # Recalculate weights for valid symbols only
                valid_weights = {s: self.weights[s] for s in valid_symbols if s in self.weights}
                total_valid_weight = sum(valid_weights.values())
                
                if total_valid_weight > 0:
                    # Normalize weights
                    self.weights = {s: w/total_valid_weight for s, w in valid_weights.items()}
                    self.symbols = valid_symbols
                else:
                    raise ValueError("No valid symbols with sufficient data")
            
            # Forward fill any remaining NaN values
            self.price_data = self.price_data.fillna(method='ffill').fillna(method='bfill')
            
            print(f"Successfully fetched data for {len(self.symbols)} symbols")
            print(f"Data shape: {self.price_data.shape}")
            print(f"Date range: {self.price_data.index[0].date()} to {self.price_data.index[-1].date()}")
            
            return self.price_data
            
        except Exception as e:
            raise Exception(f"Error fetching historical data: {str(e)}")
    
    def _get_rebalance_dates(self) -> List[pd.Timestamp]:
        """
        Get list of rebalancing dates based on frequency
        
        Returns:
            List of rebalancing dates
        """
        if self.rebalance_frequency == "never":
            return [self.start_date]
        
        dates = []
        current_date = self.start_date
        
        while current_date <= self.end_date:
            dates.append(current_date)
            
            if self.rebalance_frequency == "daily":
                current_date += timedelta(days=1)
            elif self.rebalance_frequency == "weekly":
                current_date += timedelta(weeks=1)
            elif self.rebalance_frequency == "monthly":
                # Move to first day of next month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1, day=1)
            elif self.rebalance_frequency == "quarterly":
                # Move to first day of next quarter
                current_quarter = (current_date.month - 1) // 3
                next_quarter_month = (current_quarter + 1) * 3 + 1
                if next_quarter_month > 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
                else:
                    current_date = current_date.replace(month=next_quarter_month, day=1)
        
        # Filter dates to only include trading days present in our data
        available_dates = set(self.price_data.index)
        valid_dates = []
        
        for date in dates:
            # Find the closest available trading day
            closest_date = min(available_dates, key=lambda x: abs((x - date).days))
            if abs((closest_date - date).days) <= 5:  # Within 5 days
                valid_dates.append(closest_date)
        
        return sorted(list(set(valid_dates)))  # Remove duplicates and sort
    
    def calculate_portfolio_value(self) -> pd.DataFrame:
        """
        Calculate portfolio value over time with optional rebalancing
        
        Returns:
            DataFrame with portfolio values, holdings, and metrics over time
        """
        if self.price_data is None:
            self.fetch_historical_data()
        
        try:
            print(f"Calculating portfolio performance with {self.rebalance_frequency} rebalancing...")
            
            # Get rebalancing dates
            rebalance_dates = self._get_rebalance_dates()
            print(f"Rebalancing {len(rebalance_dates)} times during backtesting period")
            
            # Initialize results dataframe
            results = pd.DataFrame(index=self.price_data.index)
            results['portfolio_value'] = 0.0
            
            # Initialize holdings for each symbol
            for symbol in self.symbols:
                results[f'{symbol}_shares'] = 0.0
                results[f'{symbol}_value'] = 0.0
            
            # Track cash and rebalancing
            results['cash'] = 0.0
            results['total_value'] = 0.0
            results['is_rebalance_day'] = False
            
            current_cash = self.initial_investment
            current_shares = {symbol: 0.0 for symbol in self.symbols}
            
            # Process each trading day
            for i, (date, _) in enumerate(results.iterrows()):
                # Check if this is a rebalancing day
                is_rebalance_day = date in rebalance_dates
                results.loc[date, 'is_rebalance_day'] = is_rebalance_day
                
                if is_rebalance_day or i == 0:
                    # Calculate current portfolio value before rebalancing
                    if i > 0:
                        portfolio_value = sum(
                            current_shares[symbol] * self.price_data.loc[date, symbol] 
                            for symbol in self.symbols
                        ) + current_cash
                    else:
                        portfolio_value = self.initial_investment
                    
                    # Rebalance portfolio
                    target_values = {symbol: portfolio_value * self.weights[symbol] for symbol in self.symbols}
                    
                    # Sell all current holdings
                    for symbol in self.symbols:
                        if current_shares[symbol] > 0:
                            current_cash += current_shares[symbol] * self.price_data.loc[date, symbol]
                            current_shares[symbol] = 0.0
                    
                    # Buy new holdings according to target weights
                    for symbol in self.symbols:
                        target_value = target_values[symbol]
                        price = self.price_data.loc[date, symbol]
                        shares_to_buy = target_value / price
                        cost = shares_to_buy * price
                        
                        if cost <= current_cash:
                            current_shares[symbol] = shares_to_buy
                            current_cash -= cost
                
                # Calculate current values
                total_holdings_value = 0.0
                for symbol in self.symbols:
                    current_price = self.price_data.loc[date, symbol]
                    symbol_value = current_shares[symbol] * current_price
                    total_holdings_value += symbol_value
                    
                    results.loc[date, f'{symbol}_shares'] = current_shares[symbol]
                    results.loc[date, f'{symbol}_value'] = symbol_value
                
                results.loc[date, 'cash'] = current_cash
                results.loc[date, 'portfolio_value'] = total_holdings_value
                results.loc[date, 'total_value'] = total_holdings_value + current_cash
            
            # Calculate returns
            results['portfolio_return'] = results['total_value'].pct_change()
            results['cumulative_return'] = (results['total_value'] / self.initial_investment) - 1
            
            self.portfolio_values = results
            print(f"Portfolio calculation complete. Final value: ${results['total_value'].iloc[-1]:,.2f}")
            
            return results
            
        except Exception as e:
            raise Exception(f"Error calculating portfolio value: {str(e)}")
    
    def calculate_metrics(self) -> Dict:
        """
        Calculate comprehensive portfolio performance metrics
        
        Returns:
            Dictionary containing all performance metrics
        """
        if self.portfolio_values is None:
            self.calculate_portfolio_value()
        
        try:
            print("Calculating performance metrics...")
            
            returns = self.portfolio_values['portfolio_return'].dropna()
            total_value = self.portfolio_values['total_value']
            
            # Basic performance metrics
            total_return = (total_value.iloc[-1] / self.initial_investment) - 1
            
            # Annualized metrics
            days = (self.end_date - self.start_date).days
            years = days / 365.25
            annualized_return = (1 + total_return) ** (1/years) - 1
            
            # Risk metrics
            daily_returns = returns
            volatility = daily_returns.std() * np.sqrt(252)  # Annualized volatility
            
            # Sharpe ratio (assuming 2% risk-free rate)
            risk_free_rate = 0.02
            excess_return = annualized_return - risk_free_rate
            sharpe_ratio = excess_return / volatility if volatility > 0 else 0
            
            # Maximum drawdown
            cumulative_values = total_value
            rolling_max = cumulative_values.expanding().max()
            drawdown = (cumulative_values - rolling_max) / rolling_max
            max_drawdown = drawdown.min()
            
            # Value at Risk (95% confidence)
            var_95 = np.percentile(daily_returns.dropna(), 5) if len(daily_returns.dropna()) > 0 else 0
            
            # Calmar ratio (annualized return / max drawdown)
            calmar_ratio = abs(annualized_return / max_drawdown) if max_drawdown < 0 else 0
            
            # Sortino ratio (downside deviation)
            downside_returns = daily_returns[daily_returns < 0]
            downside_deviation = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
            sortino_ratio = excess_return / downside_deviation if downside_deviation > 0 else 0
            
            # Win rate
            positive_days = len(daily_returns[daily_returns > 0])
            total_days = len(daily_returns)
            win_rate = positive_days / total_days if total_days > 0 else 0
            
            # Best and worst days
            best_day = daily_returns.max() if len(daily_returns) > 0 else 0
            worst_day = daily_returns.min() if len(daily_returns) > 0 else 0
            
            # Final portfolio composition
            final_composition = {}
            for symbol in self.symbols:
                final_value = self.portfolio_values[f'{symbol}_value'].iloc[-1]
                final_composition[symbol] = {
                    'value': final_value,
                    'percentage': final_value / total_value.iloc[-1] if total_value.iloc[-1] > 0 else 0,
                    'shares': self.portfolio_values[f'{symbol}_shares'].iloc[-1]
                }
            
            self.metrics = {
                # Basic metrics
                'initial_investment': self.initial_investment,
                'final_value': total_value.iloc[-1],
                'total_return': total_return,
                'total_return_percentage': total_return * 100,
                
                # Annualized metrics
                'annualized_return': annualized_return,
                'annualized_return_percentage': annualized_return * 100,
                'annualized_volatility': volatility,
                'annualized_volatility_percentage': volatility * 100,
                
                # Risk-adjusted metrics
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio,
                'calmar_ratio': calmar_ratio,
                
                # Risk metrics
                'max_drawdown': max_drawdown,
                'max_drawdown_percentage': max_drawdown * 100,
                'var_95': var_95,
                'var_95_percentage': var_95 * 100,
                
                # Trading metrics
                'win_rate': win_rate,
                'win_rate_percentage': win_rate * 100,
                'best_day': best_day,
                'best_day_percentage': best_day * 100,
                'worst_day': worst_day,
                'worst_day_percentage': worst_day * 100,
                
                # Period information
                'start_date': self.start_date.strftime('%Y-%m-%d'),
                'end_date': self.end_date.strftime('%Y-%m-%d'),
                'trading_days': len(total_value),
                'years': years,
                'rebalance_frequency': self.rebalance_frequency,
                
                # Portfolio composition
                'final_composition': final_composition,
                'symbols': self.symbols,
                'initial_weights': self.weights
            }
            
            print("Metrics calculation complete")
            return self.metrics
            
        except Exception as e:
            raise Exception(f"Error calculating metrics: {str(e)}")
    
    def generate_report(self, include_detailed_data: bool = False) -> Dict:
        """
        Generate comprehensive performance report
        
        Args:
            include_detailed_data: Whether to include daily portfolio values
        
        Returns:
            Complete backtesting report
        """
        if self.metrics is None:
            self.calculate_metrics()
        
        try:
            print("Generating backtesting report...")
            
            report = {
                'summary': {
                    'backtest_period': f"{self.metrics['start_date']} to {self.metrics['end_date']}",
                    'initial_investment': self.metrics['initial_investment'],
                    'final_value': self.metrics['final_value'],
                    'total_return': self.metrics['total_return_percentage'],
                    'annualized_return': self.metrics['annualized_return_percentage'],
                    'volatility': self.metrics['annualized_volatility_percentage'],
                    'sharpe_ratio': self.metrics['sharpe_ratio'],
                    'max_drawdown': self.metrics['max_drawdown_percentage']
                },
                
                'performance_metrics': {
                    'returns': {
                        'total_return': self.metrics['total_return_percentage'],
                        'annualized_return': self.metrics['annualized_return_percentage'],
                        'best_day': self.metrics['best_day_percentage'],
                        'worst_day': self.metrics['worst_day_percentage']
                    },
                    'risk': {
                        'volatility': self.metrics['annualized_volatility_percentage'],
                        'max_drawdown': self.metrics['max_drawdown_percentage'],
                        'var_95': self.metrics['var_95_percentage'],
                        'win_rate': self.metrics['win_rate_percentage']
                    },
                    'risk_adjusted': {
                        'sharpe_ratio': self.metrics['sharpe_ratio'],
                        'sortino_ratio': self.metrics['sortino_ratio'],
                        'calmar_ratio': self.metrics['calmar_ratio']
                    }
                },
                
                'portfolio_info': {
                    'symbols': self.metrics['symbols'],
                    'initial_weights': self.metrics['initial_weights'],
                    'final_composition': self.metrics['final_composition'],
                    'rebalance_frequency': self.metrics['rebalance_frequency'],
                    'trading_days': self.metrics['trading_days']
                }
            }
            
            # Add detailed daily data if requested
            if include_detailed_data and self.portfolio_values is not None:
                report['daily_data'] = {
                    'dates': self.portfolio_values.index.strftime('%Y-%m-%d').tolist(),
                    'portfolio_values': self.portfolio_values['total_value'].tolist(),
                    'returns': self.portfolio_values['portfolio_return'].fillna(0).tolist(),
                    'cumulative_returns': self.portfolio_values['cumulative_return'].tolist()
                }
                
                # Add individual asset values
                for symbol in self.symbols:
                    report['daily_data'][f'{symbol}_values'] = self.portfolio_values[f'{symbol}_value'].tolist()
            
            print("Report generation complete")
            return report
            
        except Exception as e:
            raise Exception(f"Error generating report: {str(e)}")
    
    def get_performance_summary(self) -> str:
        """
        Get a formatted text summary of performance
        
        Returns:
            Formatted performance summary string
        """
        if self.metrics is None:
            self.calculate_metrics()
        
        summary = f"""
Portfolio Backtesting Results
{'='*50}
Period: {self.metrics['start_date']} to {self.metrics['end_date']}
Initial Investment: ${self.metrics['initial_investment']:,.2f}
Final Value: ${self.metrics['final_value']:,.2f}

Performance Summary:
  Total Return: {self.metrics['total_return_percentage']:.2f}%
  Annualized Return: {self.metrics['annualized_return_percentage']:.2f}%
  Annualized Volatility: {self.metrics['annualized_volatility_percentage']:.2f}%
  Sharpe Ratio: {self.metrics['sharpe_ratio']:.3f}
  Maximum Drawdown: {self.metrics['max_drawdown_percentage']:.2f}%

Risk Metrics:
  Value at Risk (95%): {self.metrics['var_95_percentage']:.2f}%
  Win Rate: {self.metrics['win_rate_percentage']:.1f}%
  Best Day: {self.metrics['best_day_percentage']:.2f}%
  Worst Day: {self.metrics['worst_day_percentage']:.2f}%

Portfolio Configuration:
  Symbols: {', '.join(self.metrics['symbols'])}
  Rebalancing: {self.metrics['rebalance_frequency']}
  Trading Days: {self.metrics['trading_days']}
"""
        return summary


# Convenience function for quick backtesting
def backtest_portfolio(symbols: List[str], 
                      weights: Dict[str, float],
                      initial_investment: float = 100000,
                      start_date: str = None,
                      end_date: str = None,
                      rebalance_frequency: str = "monthly") -> Dict:
    """
    Convenience function to run a complete backtest
    
    Args:
        symbols: List of cryptocurrency symbols
        weights: Portfolio weights dictionary
        initial_investment: Initial investment amount
        start_date: Start date (defaults to 1 year ago)
        end_date: End date (defaults to today)
        rebalance_frequency: Rebalancing frequency
    
    Returns:
        Complete backtesting report
    """
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    if end_date is None:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    backtester = Backtester(
        symbols=symbols,
        weights=weights,
        initial_investment=initial_investment,
        start_date=start_date,
        end_date=end_date,
        rebalance_frequency=rebalance_frequency
    )
    
    return backtester.generate_report(include_detailed_data=True)


# Example usage and testing
if __name__ == "__main__":
    # Example backtest
    symbols = ['BTC-USD', 'ETH-USD', 'ADA-USD']
    weights = {'BTC-USD': 0.5, 'ETH-USD': 0.3, 'ADA-USD': 0.2}
    
    try:
        print("Running example backtest...")
        
        # Create backtester
        backtester = Backtester(
            symbols=symbols,
            weights=weights,
            initial_investment=100000,
            start_date='2023-01-01',
            end_date='2024-01-01',
            rebalance_frequency='monthly'
        )
        
        # Run backtest
        report = backtester.generate_report(include_detailed_data=False)
        
        # Print summary
        print(backtester.get_performance_summary())
        
        print(f"\nFinal Portfolio Composition:")
        for symbol, data in report['portfolio_info']['final_composition'].items():
            print(f"  {symbol}: {data['percentage']:.1%} (${data['value']:,.2f})")
        
    except Exception as e:
        print(f"Error: {e}")