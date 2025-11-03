"""
Compare ML-Driven Trading vs Traditional Rebalancing Strategy
Shows side-by-side performance comparison
"""

import sys
import warnings
from datetime import datetime, timedelta
import pandas as pd

warnings.filterwarnings("ignore")

# Import both backtesting approaches
from backtester import Backtester
from ml_backtester import MLTradingBacktester


def compare_strategies(
    symbols: list,
    initial_capital: float = 100000,
    start_date: str = None,
    end_date: str = None,
    interval: str = "4h",
):
    """
    Run both strategies and compare results
    """
    
    if start_date is None:
        # Default to 3 months for comparison (yfinance hourly limit)
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    print("="*80)
    print("STRATEGY COMPARISON: ML Trading vs Traditional Rebalancing")
    print("="*80)
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Initial Capital: ${initial_capital:,.2f}")
    print(f"Interval: {interval} candles (for ML)")
    print("="*80)
    
    results = {}
    
    # Strategy 1: Traditional Rebalancing (Monthly)
    print("\n📊 Running Strategy 1: Traditional Monthly Rebalancing...")
    print("-"*80)
    try:
        # Equal weights for fair comparison
        weights = {symbol: 1.0 / len(symbols) for symbol in symbols}
        
        rebalance_backtester = Backtester(
            symbols=symbols,
            weights=weights,
            initial_investment=initial_capital,
            start_date=start_date,
            end_date=end_date,
            rebalance_frequency="monthly"
        )
        
        rebalance_backtester.fetch_historical_data()
        rebalance_backtester.calculate_portfolio_value()
        rebalance_report = rebalance_backtester.generate_report(include_detailed_data=False)
        
        results['rebalancing'] = {
            'final_value': rebalance_report['summary']['final_value'],
            'total_return': rebalance_report['summary']['total_return'],
            'annualized_return': rebalance_report['summary']['annualized_return'],
            'sharpe_ratio': rebalance_report['summary']['sharpe_ratio'],
            'max_drawdown': rebalance_report['summary']['max_drawdown'],
            'volatility': rebalance_report['summary']['annualized_volatility'],
            'num_rebalances': len(rebalance_report['portfolio_info'].get('rebalance_dates', [])),
        }
        
        print("✅ Rebalancing strategy completed")
        print(rebalance_backtester.get_performance_summary())
        
    except Exception as e:
        print(f"❌ Rebalancing strategy failed: {str(e)}")
        results['rebalancing'] = {'error': str(e)}
    
    # Strategy 2: ML-Driven Trading
    print("\n\n🤖 Running Strategy 2: ML-Driven Trading...")
    print("-"*80)
    try:
        ml_backtester = MLTradingBacktester(
            symbols=symbols,
            initial_capital=initial_capital,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
            signal_threshold=0.5,
            max_position_size=0.3,
            transaction_cost=0.001
        )
        
        ml_report = ml_backtester.run_backtest()
        
        results['ml_trading'] = {
            'final_value': ml_report['summary']['final_value'],
            'total_return': ml_report['summary']['total_return'],
            'annualized_return': ml_report['summary']['annualized_return'],
            'sharpe_ratio': ml_report['summary']['sharpe_ratio'],
            'max_drawdown': ml_report['summary']['max_drawdown'],
            'volatility': ml_report['summary']['volatility'],
            'num_trades': ml_report['trading_stats']['total_trades'],
            'win_rate': ml_report['trading_stats']['win_rate'],
        }
        
        print("✅ ML trading strategy completed")
        print(ml_backtester.get_performance_summary())
        
    except Exception as e:
        print(f"❌ ML trading strategy failed: {str(e)}")
        results['ml_trading'] = {'error': str(e)}
    
    # Strategy 3: Buy and Hold (Equal Weight)
    print("\n\n💰 Running Strategy 3: Buy and Hold (No Rebalancing)...")
    print("-"*80)
    try:
        weights = {symbol: 1.0 / len(symbols) for symbol in symbols}
        
        buy_hold_backtester = Backtester(
            symbols=symbols,
            weights=weights,
            initial_investment=initial_capital,
            start_date=start_date,
            end_date=end_date,
            rebalance_frequency="never"
        )
        
        buy_hold_backtester.fetch_historical_data()
        buy_hold_backtester.calculate_portfolio_value()
        buy_hold_report = buy_hold_backtester.generate_report(include_detailed_data=False)
        
        results['buy_hold'] = {
            'final_value': buy_hold_report['summary']['final_value'],
            'total_return': buy_hold_report['summary']['total_return'],
            'annualized_return': buy_hold_report['summary']['annualized_return'],
            'sharpe_ratio': buy_hold_report['summary']['sharpe_ratio'],
            'max_drawdown': buy_hold_report['summary']['max_drawdown'],
            'volatility': buy_hold_report['summary']['annualized_volatility'],
            'num_rebalances': 0,
        }
        
        print("✅ Buy and hold strategy completed")
        print(buy_hold_backtester.get_performance_summary())
        
    except Exception as e:
        print(f"❌ Buy and hold strategy failed: {str(e)}")
        results['buy_hold'] = {'error': str(e)}
    
    # Print Comparison Table
    print("\n\n")
    print("="*80)
    print("📊 STRATEGY COMPARISON SUMMARY")
    print("="*80)
    
    # Create comparison DataFrame
    comparison_data = []
    
    for strategy_name, metrics in results.items():
        if 'error' not in metrics:
            comparison_data.append({
                'Strategy': strategy_name.replace('_', ' ').title(),
                'Final Value': f"${metrics['final_value']:,.2f}",
                'Total Return': f"{metrics['total_return']:.2f}%",
                'Annual Return': f"{metrics['annualized_return']:.2f}%",
                'Sharpe Ratio': f"{metrics['sharpe_ratio']:.3f}",
                'Max Drawdown': f"{metrics['max_drawdown']:.2f}%",
                'Volatility': f"{metrics['volatility']:.2f}%",
                'Trades/Rebalances': metrics.get('num_trades', metrics.get('num_rebalances', 0))
            })
    
    if comparison_data:
        df = pd.DataFrame(comparison_data)
        print("\n" + df.to_string(index=False))
        
        # Determine winner
        print("\n" + "="*80)
        print("🏆 PERFORMANCE RANKINGS")
        print("="*80)
        
        # Best total return
        best_return_idx = df['Total Return'].str.rstrip('%').astype(float).idxmax()
        print(f"\n📈 Best Total Return: {df.loc[best_return_idx, 'Strategy']}")
        print(f"   Return: {df.loc[best_return_idx, 'Total Return']}")
        
        # Best Sharpe ratio
        best_sharpe_idx = df['Sharpe Ratio'].astype(float).idxmax()
        print(f"\n⚖️  Best Risk-Adjusted Return (Sharpe): {df.loc[best_sharpe_idx, 'Strategy']}")
        print(f"   Sharpe Ratio: {df.loc[best_sharpe_idx, 'Sharpe Ratio']}")
        
        # Lowest drawdown
        best_dd_idx = df['Max Drawdown'].str.rstrip('%').astype(float).idxmax()  # Less negative is better
        print(f"\n🛡️  Lowest Risk (Min Drawdown): {df.loc[best_dd_idx, 'Strategy']}")
        print(f"   Max Drawdown: {df.loc[best_dd_idx, 'Max Drawdown']}")
        
        # Key insights
        print("\n" + "="*80)
        print("💡 KEY INSIGHTS")
        print("="*80)
        
        if 'ml_trading' in results and 'error' not in results['ml_trading']:
            ml_return = results['ml_trading']['total_return']
            ml_trades = results['ml_trading']['num_trades']
            ml_winrate = results['ml_trading']['win_rate']
            
            if 'rebalancing' in results and 'error' not in results['rebalancing']:
                rebal_return = results['rebalancing']['total_return']
                outperformance = ml_return - rebal_return
                
                print(f"\n1. ML Trading vs Rebalancing:")
                print(f"   - ML outperformance: {outperformance:+.2f}%")
                print(f"   - ML executed {ml_trades} trades")
                print(f"   - ML win rate: {ml_winrate:.1f}%")
                
                if outperformance > 2:
                    print(f"   ✅ ML trading shows promising results!")
                elif outperformance > 0:
                    print(f"   ⚠️  ML trading slightly better, but consider transaction costs")
                else:
                    print(f"   ❌ ML trading underperformed - simpler strategy may be better")
            
            if 'buy_hold' in results and 'error' not in results['buy_hold']:
                bh_return = results['buy_hold']['total_return']
                vs_bh = ml_return - bh_return
                
                print(f"\n2. ML Trading vs Buy & Hold:")
                print(f"   - Outperformance: {vs_bh:+.2f}%")
                
                if vs_bh > 5:
                    print(f"   ✅ Active management adds significant value!")
                elif vs_bh > 0:
                    print(f"   ⚠️  Active management adds some value")
                else:
                    print(f"   ❌ Buy & hold would have been better (lower complexity)")
        
        print("\n3. Transaction Costs Impact:")
        if 'ml_trading' in results and 'error' not in results['ml_trading']:
            num_trades = results['ml_trading']['num_trades']
            est_costs = num_trades * 0.001 * initial_capital * 0.1  # Rough estimate
            print(f"   - ML trading executed {num_trades} trades")
            print(f"   - Estimated transaction costs: ~${est_costs:,.2f}")
            print(f"   - Cost as % of capital: ~{(est_costs/initial_capital)*100:.2f}%")
        
        if 'rebalancing' in results and 'error' not in results['rebalancing']:
            num_rebalances = results['rebalancing']['num_rebalances']
            est_costs_rebal = num_rebalances * len(symbols) * 0.001 * initial_capital * 0.1
            print(f"   - Rebalancing executed {num_rebalances} rebalances")
            print(f"   - Estimated transaction costs: ~${est_costs_rebal:,.2f}")
            print(f"   - Cost as % of capital: ~{(est_costs_rebal/initial_capital)*100:.2f}%")
    
    print("\n" + "="*80)
    print("📋 RECOMMENDATION")
    print("="*80)
    
    # Simple recommendation logic
    if 'ml_trading' in results and 'rebalancing' in results:
        if ('error' not in results['ml_trading'] and 'error' not in results['rebalancing']):
            ml_sharpe = results['ml_trading']['sharpe_ratio']
            rebal_sharpe = results['rebalancing']['sharpe_ratio']
            ml_return = results['ml_trading']['total_return']
            rebal_return = results['rebalancing']['total_return']
            
            if ml_sharpe > rebal_sharpe and ml_return > rebal_return + 2:
                print("\n✅ Use ML-Driven Trading Strategy")
                print("   - Superior risk-adjusted returns")
                print("   - Outperforms by meaningful margin")
                print("   - Worth the additional complexity")
            elif ml_return > rebal_return:
                print("\n⚠️  ML Trading Shows Promise But...")
                print("   - Marginally better performance")
                print("   - Consider if added complexity is worth it")
                print("   - Monitor for overfitting")
            else:
                print("\n✅ Stick with Traditional Rebalancing")
                print("   - Simpler and more reliable")
                print("   - Lower transaction costs")
                print("   - ML doesn't add sufficient value")
        else:
            print("\n⚠️  One or both strategies failed to run")
            print("   - Check error messages above")
            print("   - May need to retrain ML models or adjust parameters")
    
    print("\n" + "="*80)
    
    return results


if __name__ == "__main__":
    # Example comparison
    symbols = ["BTC-USD", "ETH-USD"]
    
    # Use recent 3-month period (within yfinance hourly limit)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    results = compare_strategies(
        symbols=symbols,
        initial_capital=100000,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        interval="4h"
    )
    
    print("\n✅ Comparison complete! Check results above.")
