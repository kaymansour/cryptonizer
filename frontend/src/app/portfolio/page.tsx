"use client";

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, TrendingUp, Shield, Target, BarChart3 } from 'lucide-react';
import PortfolioResults from '@/components/PortfolioResults';
import BackToMain from '@/components/backtomain';

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

const availableCryptos = [
  { symbol: 'BTC', name: 'Bitcoin', description: 'The original cryptocurrency' },
  { symbol: 'ETH', name: 'Ethereum', description: 'Smart contract platform' },
  { symbol: 'ADA', name: 'Cardano', description: 'Proof-of-stake blockchain' },
  { symbol: 'SOL', name: 'Solana', description: 'High-performance blockchain' },
  { symbol: 'DOT', name: 'Polkadot', description: 'Multi-chain protocol' },
  { symbol: 'MATIC', name: 'Polygon', description: 'Ethereum scaling solution' },
  { symbol: 'AVAX', name: 'Avalanche', description: 'Fast consensus platform' },
  { symbol: 'LINK', name: 'Chainlink', description: 'Decentralized oracle network' },
  { symbol: 'ATOM', name: 'Cosmos', description: 'Internet of blockchains' },
  { symbol: 'XRP', name: 'XRP', description: 'Digital payment protocol' },
];

export default function PortfolioOptimizer() {
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>(['BTC', 'ETH']);
  const [investmentAmount, setInvestmentAmount] = useState<string>('100000');
  const [riskTolerance, setRiskTolerance] = useState<string>('');
  const [investmentGoal, setInvestmentGoal] = useState<string>('');
  const [timePeriod, setTimePeriod] = useState<string>('1y');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>('');
  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [showQuestions, setShowQuestions] = useState(true);

  const handleSymbolToggle = (symbol: string) => {
    setSelectedSymbols(prev => 
      prev.includes(symbol) 
        ? prev.filter(s => s !== symbol)
        : [...prev, symbol]
    );
  };

  const getObjectiveFromAnswers = () => {
    if (riskTolerance === 'low' || investmentGoal === 'safety') {
      return 'min_volatility';
    } else if (riskTolerance === 'high' && investmentGoal === 'growth') {
      return 'max_sharpe';
    } else if (investmentGoal === 'balanced') {
      return 'max_sharpe';
    } else {
      return 'max_sharpe'; // default
    }
  };

  const getStrategyDescription = () => {
    const objective = getObjectiveFromAnswers();
    switch (objective) {
      case 'min_volatility':
        return 'Conservative Strategy - Minimize portfolio risk and volatility';
      case 'max_sharpe':
        return 'Balanced Strategy - Optimize risk-adjusted returns (Sharpe ratio)';
      default:
        return 'Balanced Strategy - Optimize risk-adjusted returns';
    }
  };

  const optimizePortfolio = async () => {
    if (selectedSymbols.length < 2) {
      setError('Please select at least 2 cryptocurrencies for diversification');
      return;
    }

    if (!riskTolerance || !investmentGoal) {
      setError('Please answer all questions to determine the best strategy for you');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const objective = getObjectiveFromAnswers();
      
      const response = await fetch('http://localhost:8000/api/optimize-portfolio', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbols: selectedSymbols,
          total_value: parseFloat(investmentAmount),
          objective: objective,
          period: timePeriod,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to optimize portfolio');
      }

      const data = await response.json();
      setResult(data);
      setShowQuestions(false);
    } catch (err) {
      console.error('Portfolio optimization error:', err);
      setError('Failed to optimize portfolio. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const resetForm = () => {
    setResult(null);
    setShowQuestions(true);
    setError('');
  };

  if (!showQuestions && result) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-4xl font-bold text-gray-900">Portfolio Optimization Results</h1>
              <p className="text-gray-600 mt-2">Your optimized cryptocurrency portfolio</p>
            </div>
            <Button onClick={resetForm} variant="outline">
              Create New Portfolio
            </Button>
          </div>
          <PortfolioResults result={result} />
          <BackToMain />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8">
      <div className="container mx-auto px-4 max-w-4xl">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Smart Portfolio Optimizer</h1>
          <p className="text-xl text-gray-600">
            Build an optimized cryptocurrency portfolio tailored to your goals and risk tolerance
          </p>
        </div>

        <div className="grid gap-8 md:grid-cols-1 lg:grid-cols-1">
          {/* Investment Amount */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-green-600" />
                Investment Amount
              </CardTitle>
              <CardDescription>
                How much would you like to invest in your portfolio?
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="amount">Investment Amount (USD)</Label>
                  <Input
                    id="amount"
                    type="number"
                    value={investmentAmount}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInvestmentAmount(e.target.value)}
                    placeholder="100000"
                    className="text-lg"
                  />
                </div>
                <div className="grid grid-cols-3 gap-2">
                  {[50000, 100000, 250000].map((amount) => (
                    <Button
                      key={amount}
                      variant={parseInt(investmentAmount) === amount ? "default" : "outline"}
                      onClick={() => setInvestmentAmount(amount.toString())}
                      className="text-sm"
                    >
                      ${amount.toLocaleString()}
                    </Button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Risk Tolerance */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-blue-600" />
                Risk Tolerance
              </CardTitle>
              <CardDescription>
                How comfortable are you with potential losses for higher returns?
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3">
                {[
                  { value: 'low', label: 'Conservative', desc: 'I prefer stable returns and minimal risk' },
                  { value: 'medium', label: 'Moderate', desc: 'I can accept some risk for better returns' },
                  { value: 'high', label: 'Aggressive', desc: 'I\'m comfortable with high risk for maximum returns' }
                ].map((option) => (
                  <Button
                    key={option.value}
                    variant={riskTolerance === option.value ? "default" : "outline"}
                    onClick={() => setRiskTolerance(option.value)}
                    className="h-auto p-4 text-left justify-start"
                  >
                    <div>
                      <div className="font-semibold">{option.label}</div>
                      <div className="text-sm text-muted-foreground">{option.desc}</div>
                    </div>
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Investment Goal */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5 text-purple-600" />
                Investment Goal
              </CardTitle>
              <CardDescription>
                What&apos;s your primary goal for this investment?
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3">
                {[
                  { value: 'safety', label: 'Capital Preservation', desc: 'Protect my money from major losses' },
                  { value: 'balanced', label: 'Balanced Growth', desc: 'Steady growth with reasonable risk' },
                  { value: 'growth', label: 'Maximum Growth', desc: 'Highest possible returns' }
                ].map((option) => (
                  <Button
                    key={option.value}
                    variant={investmentGoal === option.value ? "default" : "outline"}
                    onClick={() => setInvestmentGoal(option.value)}
                    className="h-auto p-4 text-left justify-start"
                  >
                    <div>
                      <div className="font-semibold">{option.label}</div>
                      <div className="text-sm text-muted-foreground">{option.desc}</div>
                    </div>
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Cryptocurrency Selection */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-orange-600" />
                Select Cryptocurrencies
              </CardTitle>
              <CardDescription>
                Choose at least 2 cryptocurrencies for your portfolio (more = better diversification)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {availableCryptos.map((crypto) => (
                  <div
                    key={crypto.symbol}
                    className={`border rounded-lg p-3 cursor-pointer transition-all ${
                      selectedSymbols.includes(crypto.symbol)
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => handleSymbolToggle(crypto.symbol)}
                  >
                    <div className="flex items-center space-x-3">
                      <Checkbox
                        checked={selectedSymbols.includes(crypto.symbol)}
                        onChange={() => handleSymbolToggle(crypto.symbol)}
                      />
                      <div>
                        <div className="font-semibold">{crypto.symbol} - {crypto.name}</div>
                        <div className="text-sm text-gray-600">{crypto.description}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 text-sm text-gray-600">
                Selected: {selectedSymbols.join(', ')} ({selectedSymbols.length} cryptocurrencies)
              </div>
            </CardContent>
          </Card>

          {/* Time Period */}
          <Card>
            <CardHeader>
              <CardTitle>Historical Data Period</CardTitle>
              <CardDescription>
                How much historical data should we use to analyze the cryptocurrencies?
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Select value={timePeriod} onValueChange={setTimePeriod}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="3mo">3 Months (Recent trends)</SelectItem>
                  <SelectItem value="6mo">6 Months (Medium term)</SelectItem>
                  <SelectItem value="1y">1 Year (Recommended)</SelectItem>
                  <SelectItem value="2y">2 Years (Long term)</SelectItem>
                </SelectContent>
              </Select>
            </CardContent>
          </Card>

          {/* Strategy Preview */}
          {riskTolerance && investmentGoal && (
            <Card className="border-green-200 bg-green-50">
              <CardHeader>
                <CardTitle className="text-green-800">Recommended Strategy</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-green-700">{getStrategyDescription()}</p>
              </CardContent>
            </Card>
          )}

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Submit Button */}
          <div className="text-center">
            <Button
              onClick={optimizePortfolio}
              disabled={isLoading || selectedSymbols.length < 2}
              size="lg"
              className="w-full md:w-auto px-8 py-3 text-lg"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Optimizing Your Portfolio...
                </>
              ) : (
                'Optimize My Portfolio'
              )}
            </Button>
          </div>
        </div>

        <BackToMain />
      </div>
    </div>
  );
}