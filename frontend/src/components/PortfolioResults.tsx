"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { BentoCard, BentoGrid } from './ui/bento-grid';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Button } from './ui/button';
import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip';
import PredictionsCard from './PredictionsCard';
import {
  TrendingUp,
  Shield,
  DollarSign,
  PieChart,
  BarChart3,
  AlertTriangle,
  CheckCircle,
  History,
  Sparkles,
  Info
} from 'lucide-react';

interface OptimizationResult {
  success: boolean;
  portfolio: {
    weights: Record<string, number>;
    expected_return: number;
    volatility: number;
    sharpe_ratio: number;
    objective: string;
  };
  allocation: {
    allocation: Record<string, number>;
    leftover: number;
    latest_prices: Record<string, number>;
    total_value: number;
  };
  metrics: {
    var_95: number;
    max_drawdown: number;
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
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'overview' | 'predictions' | 'backtest'>('overview');

  // Add safety checks to prevent undefined errors
  if (!result || !result.portfolio) {
    return (
      <div className="text-center p-8">
        <p className="text-destructive">Error: Invalid portfolio optimization result</p>
      </div>
    );
  }

  const riskInfo = getRiskLevel(result.portfolio?.volatility || 0);
  const sharpeInfo = getSharpeRating(result.portfolio?.sharpe_ratio || 0);

  // Calculate total allocated value
  const totalAllocated = Object.entries(result.allocation?.allocation || {}).reduce((sum, [symbol, shares]) => {
    const price = result.allocation?.latest_prices?.[symbol] || 0;
    return sum + (shares * price);
  }, 0);

  // Get meaningful allocations (filter out very small weights)
  const meaningfulWeights = Object.entries(result.portfolio?.weights || {})
    .filter(([, weight]) => (weight as number) > 0.001)
    .sort(([, a], [, b]) => (b as number) - (a as number));

  const handleBacktestPortfolio = () => {
    // Store portfolio data in localStorage for the backtest page
    const portfolioData = {
      symbols: result.symbols,
      weights: result.portfolio.weights,
      initial_investment: result.allocation?.total_value || 100000,
    };

    localStorage.setItem('portfolioData', JSON.stringify(portfolioData));

    // Navigate to backtest page with URL params as backup
    const params = new URLSearchParams({
      symbols: encodeURIComponent(JSON.stringify(result.symbols)),
      weights: encodeURIComponent(JSON.stringify(result.portfolio.weights)),
      investment: (result.allocation?.total_value || 100000).toString(),
    });

    router.push(`/backtest?${params.toString()}`);
  };

  return (
    <div className="space-y-8">
      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-border pb-2">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-6 py-3 rounded-t-lg font-medium transition-all duration-300 ${activeTab === 'overview'
            ? 'bg-primary text-primary-foreground shadow-lg'
            : 'bg-card text-muted-foreground hover:bg-accent hover:text-accent-foreground'
            }`}
        >
          <div className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Portfolio Overview
          </div>
        </button>
        <button
          onClick={() => setActiveTab('predictions')}
          className={`px-6 py-3 rounded-t-lg font-medium transition-all duration-300 ${activeTab === 'predictions'
            ? 'bg-primary text-primary-foreground shadow-lg'
            : 'bg-card text-muted-foreground hover:bg-accent hover:text-accent-foreground'
            }`}
        >
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4" />
            AI Predictions
          </div>
        </button>
        <button
          onClick={() => setActiveTab('backtest')}
          className={`px-6 py-3 rounded-t-lg font-medium transition-all duration-300 ${activeTab === 'backtest'
            ? 'bg-primary text-primary-foreground shadow-lg'
            : 'bg-card text-muted-foreground hover:bg-accent hover:text-accent-foreground'
            }`}
        >
          <div className="flex items-center gap-2">
            <History className="h-4 w-4" />
            Historical Backtest
          </div>
        </button>
      </div>

      {/* Tab Content with smooth transition */}
      <div className="relative overflow-hidden">
        <div
          className={`transition-all duration-500 ease-in-out ${activeTab === 'overview'
            ? 'opacity-100 translate-x-0'
            : 'opacity-0 -translate-x-full absolute inset-0 pointer-events-none'
            }`}
        >
          <div className="space-y-8">{/* Performance Metrics - Bento Grid */}
            <BentoGrid className="lg:grid-rows-1">
              {/* Expected Return */}
              <BentoCard
                name="Expected Annual Return"
                className="lg:col-start-1 lg:col-end-2 lg:row-start-1 lg:row-end-2 border-green-500/40"
                Icon={TrendingUp}
                description="Based on historical data"
                href="#"
                cta=""
                background={
                  <div className="absolute inset-0 bg-gradient-to-br from-green-500/10 to-transparent" />
                }
              >
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button className="absolute top-4 right-4 z-20">
                      <Info className="h-5 w-5 text-muted-foreground hover:text-foreground cursor-help" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs">
                    <p className="text-sm">The average yearly profit you can expect from this portfolio based on historical performance. For example, 15% means your investment could grow by $15 for every $100 invested annually.</p>
                  </TooltipContent>
                </Tooltip>
                <div className="relative z-10 mt-4">
                  <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                    {formatPercentage(result.portfolio?.expected_return || 0)}
                  </div>
                </div>
              </BentoCard>

              {/* Risk Level */}
              <BentoCard
                name="Risk Level"
                className="lg:col-start-2 lg:col-end-3 lg:row-start-1 lg:row-end-2 border-blue-500/40"
                Icon={Shield}
                description={`${formatPercentage(result.portfolio?.volatility || 0)} volatility`}
                href="#"
                cta=""
                background={
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-transparent" />
                }
              >
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button className="absolute top-4 right-4 z-20">
                      <Info className="h-5 w-5 text-muted-foreground hover:text-foreground cursor-help" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs">
                    <p className="text-sm">How much your portfolio value might swing up or down. Low risk means stable but slower growth, High risk means bigger potential gains but also bigger potential losses. Volatility measures these price fluctuations.</p>
                  </TooltipContent>
                </Tooltip>
                <div className="relative z-10 mt-4">
                  <div className={`text-3xl font-bold ${riskInfo.color}`}>
                    {riskInfo.level}
                  </div>
                </div>
              </BentoCard>

              {/* Sharpe Ratio */}
              <BentoCard
                name="Risk-Adjusted Return"
                className="lg:col-start-3 lg:col-end-4 lg:row-start-1 lg:row-end-2 border-purple-500/40"
                Icon={BarChart3}
                description={`Sharpe Ratio - ${sharpeInfo.rating}`}
                href="#"
                cta=""
                background={
                  <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-transparent" />
                }
              >
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button className="absolute top-4 right-4 z-20">
                      <Info className="h-5 w-5 text-muted-foreground hover:text-foreground cursor-help" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs">
                    <p className="text-sm">The Sharpe Ratio tells you how much return you&apos;re getting for the risk you&apos;re taking. Higher is better: &gt;2 is excellent, &gt;1 is good, &gt;0.5 is fair. Think of it as &quot;bang for your buck&quot; in investing.</p>
                  </TooltipContent>
                </Tooltip>
                <div className="relative z-10 mt-4">
                  <div className={`text-3xl font-bold ${sharpeInfo.color}`}>
                    {result.portfolio?.sharpe_ratio?.toFixed(2) || '0.00'}
                  </div>
                </div>
              </BentoCard>
            </BentoGrid>

            {/* Portfolio Value, Risk Analysis & Optimization Strategy */}
            <BentoGrid className="lg:grid-rows-1">
              {/* Portfolio Value & Allocation */}
              <BentoCard
                name="Portfolio Value & Allocation"
                className="lg:col-start-1 lg:col-end-2 lg:row-start-1 lg:row-end-2 border-primary/40"
                Icon={DollarSign}
                description="Optimized weights and share distribution"
                href="#"
                cta=""
                background={
                  <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent" />
                }
              >
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button className="absolute top-4 right-4 z-20">
                      <Info className="h-5 w-5 text-muted-foreground hover:text-foreground cursor-help" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs">
                    <p className="text-sm">Shows how your money is divided among different cryptocurrencies. The percentages show what portion of your total investment goes into each coin. Fractional shares mean you can own parts of expensive coins like Bitcoin.</p>
                  </TooltipContent>
                </Tooltip>
                <div className="relative z-10 mt-4">
                  <div className="text-3xl font-bold text-foreground mb-6">
                    {formatCurrency(result.allocation?.total_value || 0)}
                  </div>
                  <div className="space-y-4 mt-4">
                    {meaningfulWeights.map(([symbol, weight]) => {
                      const shares = result.allocation?.allocation?.[symbol] || 0;
                      const price = result.allocation?.latest_prices?.[symbol] || 0;
                      const value = shares * price;

                      return (
                        <div key={symbol} className="space-y-2">
                          <div className="flex justify-between items-center">
                            <div className="flex items-center gap-3">
                              <span className="font-medium text-foreground">{symbol}</span>
                              <Badge variant="secondary">{formatPercentage(weight)}</Badge>
                            </div>
                            <div className="text-right">
                              <div className="font-semibold text-foreground">
                                {shares.toFixed(6)} shares
                              </div>
                              <div className="text-sm text-muted-foreground">
                                {formatCurrency(value)}
                              </div>
                            </div>
                          </div>
                          <Progress value={weight * 100} className="h-2" />
                        </div>
                      );
                    })}

                    {(result.allocation?.leftover || 0) > 0 && (
                      <div className="pt-2 border-t border-border">
                        <div className="flex justify-between items-center text-sm">
                          <span className="text-muted-foreground">Cash Remaining</span>
                          <span className="font-medium text-foreground">{formatCurrency(result.allocation?.leftover || 0)}</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </BentoCard>

              {/* Risk Analysis */}
              <BentoCard
                name="Risk Analysis"
                className="lg:col-start-2 lg:col-end-3 lg:row-start-1 lg:row-end-2 border-yellow-500/40"
                Icon={AlertTriangle}
                description="Portfolio risk metrics"
                href="#"
                cta=""
                background={
                  <div className="absolute inset-0 bg-gradient-to-br from-yellow-500/10 to-transparent" />
                }
              >
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button className="absolute top-4 right-4 z-20">
                      <Info className="h-5 w-5 text-muted-foreground hover:text-foreground cursor-help" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs">
                    <p className="text-sm"><strong>Value at Risk (95%):</strong> The maximum you could lose in a bad day with 95% confidence.<br /><strong>Max Drawdown:</strong> The biggest loss from peak to bottom historically.<br /><strong>Volatility:</strong> How much prices typically fluctuate.</p>
                  </TooltipContent>
                </Tooltip>
                <div className="relative z-10 mt-4 space-y-4">
                  <div className="flex flex-col p-4 rounded-xl bg-card/50 border border-border">
                    <div className="text-sm text-muted-foreground mb-1">Value at Risk (95%)</div>
                    <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                      {formatPercentage(Math.abs(result.metrics?.var_95 || 0))}
                    </div>
                  </div>

                  <div className="flex flex-col p-4 rounded-xl bg-card/50 border border-border">
                    <div className="text-sm text-muted-foreground mb-1">Maximum Drawdown</div>
                    <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                      {formatPercentage(Math.abs(result.metrics?.max_drawdown || 0))}
                    </div>
                  </div>

                  <div className="flex flex-col p-4 rounded-xl bg-card/50 border border-border">
                    <div className="text-sm text-muted-foreground mb-1">Annual Volatility</div>
                    <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                      {formatPercentage(result.portfolio?.volatility || 0)}
                    </div>
                  </div>
                </div>
              </BentoCard>

              {/* Optimization Strategy */}
              <BentoCard
                name="Optimization Strategy"
                className="lg:col-start-3 lg:col-end-4 lg:row-start-1 lg:row-end-2 border-primary/40"
                Icon={CheckCircle}
                description="Portfolio optimization details"
                href="#"
                cta=""
                background={
                  <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent" />
                }
              >
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button className="absolute top-4 right-4 z-20">
                      <Info className="h-5 w-5 text-muted-foreground hover:text-foreground cursor-help" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent className="max-w-xs">
                    <p className="text-sm">The mathematical approach used to balance your portfolio. Maximum Sharpe aims for best returns relative to risk. Minimum Volatility focuses on stability. Uses historical data to predict optimal allocation.</p>
                  </TooltipContent>
                </Tooltip>
                <div className="relative z-10 mt-4 space-y-3 text-foreground">
                  <p>
                    <strong className="text-primary">Strategy:</strong>{" "}
                    <span className="text-muted-foreground">
                      {result.portfolio?.objective === "max_sharpe"
                        ? "Maximum Sharpe Ratio (Risk-Adjusted Returns)"
                        : "Minimum Volatility (Conservative)"}
                    </span>
                  </p>
                  <p>
                    <strong className="text-primary">Data Period:</strong>{" "}
                    <span className="text-muted-foreground">
                      {result.period === "1y"
                        ? "1 Year"
                        : result.period === "6mo"
                          ? "6 Months"
                          : result.period}
                    </span>
                  </p>
                  <p>
                    <strong className="text-primary">Cryptocurrencies:</strong>{" "}
                    <span className="text-muted-foreground">
                      {(result.symbols || []).join(", ")}
                    </span>
                  </p>
                  <p className="text-sm text-muted-foreground pt-2 border-t border-border">
                    This portfolio is optimized using Modern Portfolio Theory to{" "}
                    {result.portfolio?.objective === "max_sharpe"
                      ? "maximize your risk-adjusted returns (Sharpe ratio)"
                      : "minimize portfolio volatility and risk"}
                    .
                  </p>
                </div>
              </BentoCard>
            </BentoGrid>
          </div>
        </div>

        {/* AI Predictions Tab */}
        <div
          className={`transition-all duration-500 ease-in-out ${activeTab === 'predictions'
            ? 'opacity-100 translate-x-0'
            : 'opacity-0 translate-x-full absolute inset-0 pointer-events-none'
            }`}
        >
          <BentoGrid className="lg:grid-rows-1">
            <BentoCard
              name="AI Price Predictions"
              className="lg:col-start-1 lg:col-end-4 lg:row-start-1 lg:row-end-2 border-purple-500/40"
              Icon={Sparkles}
              description="LSTM neural network predictions for next 7 candles"
              href="#"
              cta=""
              background={
                <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 via-pink-500/10 to-transparent" />
              }
            >
              <div className="relative z-10 mt-4">
                <PredictionsCard symbols={result.symbols} />
              </div>
            </BentoCard>
          </BentoGrid>
        </div>

        {/* Backtest Tab */}
        <div
          className={`transition-all duration-500 ease-in-out ${activeTab === 'backtest'
            ? 'opacity-100 translate-x-0'
            : 'opacity-0 translate-x-full absolute inset-0 pointer-events-none'
            }`}
        >
          <BentoGrid className="lg:grid-rows-1">
            <BentoCard
              name="Historical Performance Analysis"
              className="lg:col-start-1 lg:col-end-4 lg:row-start-1 lg:row-end-2 border-emerald-500/40"
              Icon={History}
              description="Run a comprehensive backtest to analyze historical performance"
              href="#"
              cta=""
              background={
                <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-transparent" />
              }
            >
              <div className="relative z-10 mt-4">
                <p className="text-sm text-muted-foreground mb-4">
                  See how this portfolio would have performed historically with real market data.
                </p>
                <Button
                  onClick={handleBacktestPortfolio}
                  className="rounded-xl shadow-lg transition-all transform hover:scale-105"
                >
                  <History className="mr-2 h-4 w-4" />
                  Backtest Portfolio
                </Button>
              </div>
            </BentoCard>
          </BentoGrid>
        </div>
      </div>
    </div>
  );
}