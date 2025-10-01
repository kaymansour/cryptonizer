"""
Portfolio Optimization Module
Implements portfolio optimization using PyPortfolioOpt for cryptocurrency portfolio management.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from pypfopt import EfficientFrontier, risk_models, expected_returns
from pypfopt.discrete_allocation import DiscreteAllocation, get_latest_prices
from pypfopt.exceptions import OptimizationError
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class CryptoPortfolioOptimizer:
    """
    Cryptocurrency Portfolio Optimizer using Modern Portfolio Theory
    """
    
    def __init__(self, symbols: List[str], period: str = "1y"):
        """
        Initialize the portfolio optimizer
        
        Args:
            symbols: List of cryptocurrency symbols (e.g., ['BTC-USD', 'ETH-USD'])
            period: Time period for historical data (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        """
        self.symbols = symbols
        self.period = period
        self.price_data = None
        self.mu = None  # Expected returns
        self.S = None   # Covariance matrix
        self.ef = None  # Efficient Frontier object
        
    def fetch_price_data(self) -> pd.DataFrame:
        """
        Fetch historical price data for the given symbols
        
        Returns:
            DataFrame with historical prices
        """
        try:
            # Download price data
            data = yf.download(self.symbols, period=self.period, progress=False)
            
            # Handle different data structures based on number of symbols
            if len(self.symbols) == 1:
                # Single symbol case - yfinance still returns MultiIndex columns
                if isinstance(data.columns, pd.MultiIndex):
                    # MultiIndex columns for single symbol
                    if 'Close' in data.columns.get_level_values(0):
                        self.price_data = data['Close']
                    else:
                        # Fallback to first price column
                        first_price_col = data.columns[0]
                        self.price_data = data[first_price_col]
                else:
                    # Regular columns (shouldn't happen with yfinance)
                    self.price_data = data
                
                # Ensure it's a DataFrame with proper column name
                if isinstance(self.price_data, pd.Series):
                    self.price_data = pd.DataFrame({self.symbols[0]: self.price_data})
                elif isinstance(self.price_data, pd.DataFrame) and len(self.price_data.columns) == 1:
                    # Rename column to symbol name
                    self.price_data.columns = [self.symbols[0]]
            else:
                # Multiple symbols case
                if isinstance(data.columns, pd.MultiIndex):
                    # MultiIndex columns (multiple symbols)
                    if 'Adj Close' in data.columns.get_level_values(0):
                        self.price_data = data['Adj Close']
                    else:
                        self.price_data = data['Close']
                else:
                    # Single level columns
                    self.price_data = data
            
            # Ensure we have a DataFrame
            if not isinstance(self.price_data, pd.DataFrame):
                self.price_data = pd.DataFrame(self.price_data)
            
            # Remove any symbols with insufficient data
            self.price_data = self.price_data.dropna(axis=1, thresh=len(self.price_data) * 0.8)
            
            # Update symbols list to only include valid ones
            self.symbols = list(self.price_data.columns)
            
            print(f"Fetched data for {len(self.symbols)} symbols: {self.symbols}")
            return self.price_data
            
        except Exception as e:
            raise Exception(f"Error fetching price data: {str(e)}")
    
    def calculate_expected_returns(self, method: str = "mean_historical_return") -> pd.Series:
        """
        Calculate expected returns for the assets
        
        Args:
            method: Method to calculate expected returns
                   - "mean_historical_return": Simple historical mean
                   - "ema_historical_return": Exponentially weighted mean
                   - "capm_return": CAPM-based returns
        
        Returns:
            Series of expected returns
        """
        if self.price_data is None:
            self.fetch_price_data()
        
        try:
            if method == "mean_historical_return":
                self.mu = expected_returns.mean_historical_return(self.price_data)
            elif method == "ema_historical_return":
                self.mu = expected_returns.ema_historical_return(self.price_data)
            elif method == "capm_return":
                self.mu = expected_returns.capm_return(self.price_data)
            else:
                raise ValueError(f"Unknown method: {method}")
            
            return self.mu
            
        except Exception as e:
            raise Exception(f"Error calculating expected returns: {str(e)}")
    
    def calculate_risk_matrix(self, method: str = "sample_cov") -> pd.DataFrame:
        """
        Calculate the risk (covariance) matrix
        
        Args:
            method: Method to calculate covariance matrix
                   - "sample_cov": Sample covariance
                   - "semicovariance": Semicovariance (downside risk)
                   - "exp_cov": Exponentially weighted covariance
                   - "ledoit_wolf": Ledoit-Wolf shrinkage
        
        Returns:
            Covariance matrix
        """
        if self.price_data is None:
            self.fetch_price_data()
        
        try:
            if method == "sample_cov":
                self.S = risk_models.sample_cov(self.price_data)
            elif method == "semicovariance":
                self.S = risk_models.semicovariance(self.price_data)
            elif method == "exp_cov":
                self.S = risk_models.exp_cov(self.price_data)
            elif method == "ledoit_wolf":
                self.S = risk_models.CovarianceShrinkage(self.price_data).ledoit_wolf()
            else:
                raise ValueError(f"Unknown method: {method}")
            
            return self.S
            
        except Exception as e:
            raise Exception(f"Error calculating risk matrix: {str(e)}")
    
    def optimize_portfolio(self, 
                          objective: str = "max_sharpe",
                          risk_free_rate: float = 0.02,
                          target_return: Optional[float] = None,
                          target_volatility: Optional[float] = None) -> Dict:
        """
        Optimize the portfolio based on the specified objective
        
        Args:
            objective: Optimization objective
                      - "max_sharpe": Maximize Sharpe ratio
                      - "min_volatility": Minimize volatility
                      - "efficient_return": Efficient portfolio for target return
                      - "efficient_risk": Efficient portfolio for target risk
            risk_free_rate: Risk-free rate for Sharpe ratio calculation
            target_return: Target return (for efficient_return objective)
            target_volatility: Target volatility (for efficient_risk objective)
        
        Returns:
            Dictionary containing optimization results
        """
        if self.mu is None:
            self.calculate_expected_returns()
        if self.S is None:
            self.calculate_risk_matrix()
        
        try:
            # Create Efficient Frontier object
            self.ef = EfficientFrontier(self.mu, self.S)
            
            # Perform optimization based on objective
            if objective == "max_sharpe":
                weights = self.ef.max_sharpe(risk_free_rate=risk_free_rate)
            elif objective == "min_volatility":
                weights = self.ef.min_volatility()
            elif objective == "efficient_return":
                if target_return is None:
                    raise ValueError("target_return must be specified for efficient_return objective")
                weights = self.ef.efficient_return(target_return)
            elif objective == "efficient_risk":
                if target_volatility is None:
                    raise ValueError("target_volatility must be specified for efficient_risk objective")
                weights = self.ef.efficient_risk(target_volatility)
            else:
                raise ValueError(f"Unknown objective: {objective}. Available: max_sharpe, min_volatility, efficient_return, efficient_risk")
            
            # Clean weights (remove tiny allocations)
            cleaned_weights = self.ef.clean_weights()
            
            # Calculate portfolio performance
            performance = self.ef.portfolio_performance(risk_free_rate=risk_free_rate, verbose=False)
            
            return {
                'weights': cleaned_weights,
                'expected_return': performance[0],
                'volatility': performance[1],
                'sharpe_ratio': performance[2],
                'objective': objective,
                'symbols': self.symbols
            }
            
        except OptimizationError as e:
            raise Exception(f"Optimization failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Error optimizing portfolio: {str(e)}")
    
    def calculate_efficient_frontier(self, num_portfolios: int = 100) -> Tuple[List[float], List[float]]:
        """
        Calculate the efficient frontier
        
        Args:
            num_portfolios: Number of portfolios to calculate along the frontier
        
        Returns:
            Tuple of (volatilities, returns) for the efficient frontier
        """
        if self.mu is None:
            self.calculate_expected_returns()
        if self.S is None:
            self.calculate_risk_matrix()
        
        try:
            # Generate range of target returns
            min_ret = self.mu.min()
            max_ret = self.mu.max()
            target_returns = np.linspace(min_ret, max_ret, num_portfolios)
            
            volatilities = []
            returns = []
            
            for target_ret in target_returns:
                try:
                    ef_copy = EfficientFrontier(self.mu, self.S)
                    ef_copy.efficient_return(target_ret)
                    performance = ef_copy.portfolio_performance(verbose=False)
                    returns.append(performance[0])
                    volatilities.append(performance[1])
                except:
                    # Skip if optimization fails for this target return
                    continue
            
            return volatilities, returns
            
        except Exception as e:
            raise Exception(f"Error calculating efficient frontier: {str(e)}")
    
    def discrete_allocation(self, total_portfolio_value: float, weights: Dict[str, float]) -> Dict:
        """
        Calculate discrete allocation of assets based on portfolio weights
        
        Args:
            total_portfolio_value: Total value of the portfolio in USD
            weights: Portfolio weights dictionary
        
        Returns:
            Dictionary containing discrete allocation results
        """
        try:
            # Get latest prices
            latest_prices = get_latest_prices(self.price_data)
            
            # Filter weights to only include assets with meaningful allocation
            filtered_weights = {k: v for k, v in weights.items() if v > 0.001}
            
            # Calculate discrete allocation
            da = DiscreteAllocation(filtered_weights, latest_prices, total_portfolio_value=total_portfolio_value)
            allocation, leftover = da.greedy_portfolio()
            
            return {
                'allocation': allocation,
                'leftover': leftover,
                'latest_prices': latest_prices.to_dict(),
                'total_value': total_portfolio_value
            }
            
        except Exception as e:
            raise Exception(f"Error calculating discrete allocation: {str(e)}")
    
    def get_portfolio_metrics(self, weights: Dict[str, float], risk_free_rate: float = 0.02) -> Dict:
        """
        Calculate comprehensive portfolio metrics
        
        Args:
            weights: Portfolio weights
            risk_free_rate: Risk-free rate for calculations
        
        Returns:
            Dictionary of portfolio metrics
        """
        try:
            # Convert weights to numpy array in correct order
            weight_array = np.array([weights.get(symbol, 0) for symbol in self.symbols])
            
            # Portfolio return and volatility
            portfolio_return = np.sum(weight_array * self.mu)
            portfolio_variance = np.dot(weight_array.T, np.dot(self.S, weight_array))
            portfolio_volatility = np.sqrt(portfolio_variance)
            
            # Sharpe ratio
            sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility
            
            # Value at Risk (VaR) - 95% confidence
            var_95 = portfolio_return - 1.645 * portfolio_volatility
            
            # Maximum Drawdown (simplified calculation)
            returns = self.price_data.pct_change().dropna()
            portfolio_returns = (returns * weight_array).sum(axis=1)
            cumulative_returns = (1 + portfolio_returns).cumprod()
            rolling_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - rolling_max) / rolling_max
            max_drawdown = drawdown.min()
            
            return {
                'expected_return': portfolio_return,
                'volatility': portfolio_volatility,
                'sharpe_ratio': sharpe_ratio,
                'var_95': var_95,
                'max_drawdown': max_drawdown,
                'weights': weights
            }
            
        except Exception as e:
            raise Exception(f"Error calculating portfolio metrics: {str(e)}")

def optimize_crypto_portfolio(symbols: List[str], 
                            total_value: float = 10000,
                            objective: str = "max_sharpe",
                            period: str = "1y") -> Dict:
    """
    Convenience function to optimize a cryptocurrency portfolio
    
    Args:
        symbols: List of cryptocurrency symbols
        total_value: Total portfolio value in USD
        objective: Optimization objective
        period: Historical data period
    
    Returns:
        Complete optimization results
    """
    try:
        # Initialize optimizer
        optimizer = CryptoPortfolioOptimizer(symbols, period)
        
        # Fetch data and calculate inputs
        optimizer.fetch_price_data()
        optimizer.calculate_expected_returns()
        optimizer.calculate_risk_matrix()
        
        # Optimize portfolio
        optimization_result = optimizer.optimize_portfolio(objective=objective)
        
        # Calculate discrete allocation
        allocation_result = optimizer.discrete_allocation(total_value, optimization_result['weights'])
        
        # Get comprehensive metrics
        metrics = optimizer.get_portfolio_metrics(optimization_result['weights'])
        
        # Calculate efficient frontier
        volatilities, returns = optimizer.calculate_efficient_frontier()
        
        return {
            'optimization': optimization_result,
            'allocation': allocation_result,
            'metrics': metrics,
            'efficient_frontier': {
                'volatilities': volatilities,
                'returns': returns
            },
            'symbols': optimizer.symbols,
            'period': period
        }
        
    except Exception as e:
        raise Exception(f"Portfolio optimization failed: {str(e)}")

# Example usage and testing
if __name__ == "__main__":
    # Example cryptocurrency symbols
    crypto_symbols = ['BTC-USD', 'ETH-USD', 'ADA-USD', 'SOL-USD', 'MATIC-USD']
    
    try:
        # Optimize portfolio with a larger value
        result = optimize_crypto_portfolio(
            symbols=crypto_symbols,
            total_value=150000,  # Increased to $150,000 to accommodate expensive cryptos like BTC
            objective="max_sharpe",
            period="1y"
        )
        
        print("Portfolio Optimization Results:")
        print("=" * 50)
        print(f"Expected Annual Return: {result['optimization']['expected_return']:.2%}")
        print(f"Annual Volatility: {result['optimization']['volatility']:.2%}")
        print(f"Sharpe Ratio: {result['optimization']['sharpe_ratio']:.3f}")
        print("\nOptimal Weights:")
        for symbol, weight in result['optimization']['weights'].items():
            if weight > 0.001:  # Only show meaningful allocations
                print(f"  {symbol}: {weight:.2%}")
        
        print(f"\nDiscrete Allocation (${result['allocation']['total_value']:,}):")
        total_allocated = 0
        if result['allocation']['allocation']:
            for symbol, shares in result['allocation']['allocation'].items():
                price = result['allocation']['latest_prices'][symbol]
                value = shares * price
                total_allocated += value
                print(f"  {symbol}: {shares} shares @ ${price:.2f} = ${value:.2f}")
            print(f"  Total allocated: ${total_allocated:.2f}")
            print(f"  Cash remaining: ${result['allocation']['leftover']:.2f}")
        else:
            print("  No meaningful allocations possible with current weights")
            print(f"  Cash remaining: ${result['allocation']['leftover']:.2f}")
        
        # Show additional metrics
        print(f"\nAdditional Risk Metrics:")
        print(f"  Value at Risk (95%): {result['metrics']['var_95']:.2%}")
        print(f"  Maximum Drawdown: {result['metrics']['max_drawdown']:.2%}")
        
    except Exception as e:
        print(f"Error: {e}")
