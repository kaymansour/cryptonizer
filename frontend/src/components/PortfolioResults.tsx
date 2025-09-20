"use client";

import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from 'lucide-react';
import { Progress } from './ui/progress';
import { 
  TrendingUp, 
  Shield, 
  DollarSign, 
  PieChart, 
  BarChart3,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';
import PortfolioCharts from './PortfolioCharts';

interface OptimizationResult {
  optimization: {
    weights: Record<string, number>;
    expected_return: number;
    volatility: number;
    sharpe_ratio: number;
    objective: string;
    symbols: string[];
  };
  allocation: {
    allocation: Record<string, number>;
    leftover: number;
    latest_prices: Record<string, number>;
    total_value: number;
  };
  metrics: {
    expected_return: number;
    volatility: number;
    sharpe_ratio: number;
    var_95: number;
    max_drawdown: number;
    weights: Record<string, number>;
  };
  efficient_frontier: {
    volatilities: number[];
    returns: number[];
  };
  symbols: string[];
  period: string;
}

interface PortfolioResultsProps {
  result: OptimizationResult;
}

const formatPercentage = (value: number) => {
  return `${(value * 100).toFixed(2)}%`;
};

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(value);
};

const getRiskLevel = (volatility: number) => {
  if (volatility < 0.2) return { level: 'Low', color: 'text-green-600', bgColor: 'bg-green-100' };
  if (volatility < 0.4) return { level: 'Medium', color: 'text-yellow-600', bgColor: 'bg-yellow-100' };
  return { level: 'High', color: 'text-red-600', bgColor: 'bg-red-100' };
};

const getSharpeRating = (sharpe: number) => {
  if (sharpe > 2) return { rating: 'Excellent', color: 'text-green-600' };
  if (sharpe > 1) return { rating: 'Good', color: 'text-blue-600' };
  if (sharpe > 0.5) return { rating: 'Fair', color: 'text-yellow-600' };
  return { rating: 'Poor', color: 'text-red-600' };
};

export default function PortfolioResults({ result }: PortfolioResultsProps) {
  const riskInfo = getRiskLevel(result.optimization.volatility);
  const sharpeInfo = getSharpeRating(result.optimization.sharpe_ratio);

  // Calculate total allocated value
  const totalAllocated = Object.entries(result.allocation.allocation).reduce((sum, [symbol, shares]) => {
    const price = result.allocation.latest_prices[symbol];
    return sum + (shares * price);
  }, 0);

  // Get meaningful allocations (filter out very small weights)
  const meaningfulWeights = Object.entries(result.optimization.weights)
    .filter(([, weight]) => weight > 0.001)
    .sort(([, a], [, b]) => b - a);

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Expected Return */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Expected Annual Return</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatPercentage(result.optimization.expected_return)}
            </div>
            <p className="text-xs text-muted-foreground">
              Based on historical data
            </p>
          </CardContent>
        </Card>

        {/* Risk Level */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Risk Level</CardTitle>
            <Shield className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${riskInfo.color}`}>
              {riskInfo.level}
            </div>
            <p className="text-xs text-muted-foreground">
              {formatPercentage(result.optimization.volatility)} volatility
            </p>
          </CardContent>
        </Card>

        {/* Sharpe Ratio */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Risk-Adjusted Return</CardTitle>
            <BarChart3 className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${sharpeInfo.color}`}>
              {result.optimization.sharpe_ratio.toFixed(2)}
            </div>
            <p className="text-xs text-muted-foreground">
              Sharpe Ratio - {sharpeInfo.rating}
            </p>
          </CardContent>
        </Card>

        {/* Portfolio Value */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Portfolio Value</CardTitle>
            <DollarSign className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(result.allocation.total_value)}
            </div>
            <p className="text-xs text-muted-foreground">
              {formatCurrency(result.allocation.leftover)} cash remaining
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Portfolio Allocation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Weights Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChart className="h-5 w-5" />
              Portfolio Allocation
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {meaningfulWeights.map(([symbol, weight]) => (
                <div key={symbol} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">{symbol}</span>
                    <Badge variant="secondary">{formatPercentage(weight)}</Badge>
                  </div>
                  <Progress value={weight * 100} className="h-2" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Actual Shares */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Share Allocation
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(result.allocation.allocation).map(([symbol, shares]) => {
                const price = result.allocation.latest_prices[symbol];
                const value = shares * price;
                const percentage = (value / totalAllocated) * 100;
                
                return (
                  <div key={symbol} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="font-medium">{symbol}</span>
                      <div className="text-right">
                        <div className="font-semibold">{shares} shares</div>
                        <div className="text-sm text-muted-foreground">
                          {formatCurrency(value)}
                        </div>
                      </div>
                    </div>
                    <Progress value={percentage} className="h-2" />
                  </div>
                );
              })}
              
              {result.allocation.leftover > 0 && (
                <div className="pt-2 border-t">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground">Cash Remaining</span>
                    <span className="font-medium">{formatCurrency(result.allocation.leftover)}</span>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Risk Metrics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-orange-600" />
            Risk Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-red-600">
                {formatPercentage(Math.abs(result.metrics.var_95))}
              </div>
              <div className="text-sm font-medium">Value at Risk (95%)</div>
              <div className="text-xs text-muted-foreground mt-1">
                Potential daily loss
              </div>
            </div>
            
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">
                {formatPercentage(Math.abs(result.metrics.max_drawdown))}
              </div>
              <div className="text-sm font-medium">Maximum Drawdown</div>
              <div className="text-xs text-muted-foreground mt-1">
                Worst historical loss
              </div>
            </div>
            
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {formatPercentage(result.optimization.volatility)}
              </div>
              <div className="text-sm font-medium">Annual Volatility</div>
              <div className="text-xs text-muted-foreground mt-1">
                Price fluctuation measure
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Strategy Information */}
      <Card className="border-blue-200 bg-blue-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-blue-800">
            <CheckCircle className="h-5 w-5" />
            Optimization Strategy
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-blue-700">
            <p className="mb-2">
              <strong>Strategy:</strong> {result.optimization.objective === 'max_sharpe' ? 'Maximum Sharpe Ratio (Risk-Adjusted Returns)' : 'Minimum Volatility (Conservative)'}
            </p>
            <p className="mb-2">
              <strong>Data Period:</strong> {result.period === '1y' ? '1 Year' : result.period === '6mo' ? '6 Months' : result.period}
            </p>
            <p className="mb-2">
              <strong>Cryptocurrencies:</strong> {result.symbols.join(', ')}
            </p>
            <p className="text-sm">
              This portfolio is optimized using Modern Portfolio Theory to {
                result.optimization.objective === 'max_sharpe' 
                  ? 'maximize your risk-adjusted returns (Sharpe ratio)'
                  : 'minimize portfolio volatility and risk'
              }.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Charts */}
      <PortfolioCharts result={result} />
    </div>
  );
}