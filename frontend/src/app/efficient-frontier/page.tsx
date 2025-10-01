"use client";

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Loader2, TrendingUp, Info } from 'lucide-react';
import BackToMain from '@/components/backtomain';

interface EfficientFrontierData {
  volatilities: number[];
  returns: number[];
  max_sharpe_portfolio: {
    return: number;
    volatility: number;
    sharpe_ratio: number;
  };
  min_volatility_portfolio: {
    return: number;
    volatility: number;
  };
}

const cryptoOptions = [
  { value: 'BTC,ETH', label: 'Bitcoin & Ethereum' },
  { value: 'BTC,ETH,ADA', label: 'BTC, ETH, Cardano' },
  { value: 'BTC,ETH,ADA,SOL', label: 'Top 4 Cryptos' },
  { value: 'BTC,ETH,ADA,SOL,DOT', label: 'Top 5 Cryptos' },
  { value: 'BTC,ETH,ADA,SOL,DOT,MATIC', label: 'Diversified Portfolio' },
];

export default function EfficientFrontierPage() {
  const [selectedCryptos, setSelectedCryptos] = useState('BTC,ETH,ADA');
  const [period, setPeriod] = useState('1y');
  const [isLoading, setIsLoading] = useState(false);
  const [data, setData] = useState<EfficientFrontierData | null>(null);
  const [error, setError] = useState('');

  const calculateEfficientFrontier = async () => {
    setIsLoading(true);
    setError('');

    try {
      const symbols = selectedCryptos.split(',');
      
      const response = await fetch('http://localhost:8000/api/efficient-frontier', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbols,
          period,
          num_portfolios: 50,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to calculate efficient frontier');
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      console.error('Efficient frontier error:', err);
      setError('Failed to calculate efficient frontier. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8">
      <div className="container mx-auto px-4 max-w-6xl">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Efficient Frontier Analysis</h1>
          <p className="text-xl text-gray-600">
            Visualize the optimal risk-return combinations for cryptocurrency portfolios
          </p>
        </div>

        <div className="grid gap-6 mb-8">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Configuration
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Cryptocurrency Portfolio</label>
                  <Select value={selectedCryptos} onValueChange={setSelectedCryptos}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {cryptoOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Time Period</label>
                  <Select value={period} onValueChange={setPeriod}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="3mo">3 Months</SelectItem>
                      <SelectItem value="6mo">6 Months</SelectItem>
                      <SelectItem value="1y">1 Year</SelectItem>
                      <SelectItem value="2y">2 Years</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="flex items-end">
                  <Button 
                    onClick={calculateEfficientFrontier}
                    disabled={isLoading}
                    className="w-full"
                  >
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Calculating...
                      </>
                    ) : (
                      'Calculate Frontier'
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {error && (
            <Card className="border-red-200 bg-red-50">
              <CardContent className="pt-6">
                <p className="text-red-700">{error}</p>
              </CardContent>
            </Card>
          )}

          {data && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Info className="h-5 w-5" />
                    Key Portfolio Points
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="text-center p-6 bg-green-50 rounded-lg">
                      <h3 className="font-semibold text-green-800 mb-2">Maximum Sharpe Ratio</h3>
                      <div className="space-y-1">
                        <div className="text-2xl font-bold text-green-600">
                          {data.max_sharpe_portfolio.sharpe_ratio.toFixed(2)}
                        </div>
                        <div className="text-sm text-green-700">
                          Return: {(data.max_sharpe_portfolio.return * 100).toFixed(1)}%
                        </div>
                        <div className="text-sm text-green-700">
                          Risk: {(data.max_sharpe_portfolio.volatility * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>

                    <div className="text-center p-6 bg-blue-50 rounded-lg">
                      <h3 className="font-semibold text-blue-800 mb-2">Minimum Volatility</h3>
                      <div className="space-y-1">
                        <div className="text-2xl font-bold text-blue-600">
                          {(data.min_volatility_portfolio.volatility * 100).toFixed(1)}%
                        </div>
                        <div className="text-sm text-blue-700">
                          Return: {(data.min_volatility_portfolio.return * 100).toFixed(1)}%
                        </div>
                        <div className="text-sm text-blue-700">
                          Lowest Risk Portfolio
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Efficient Frontier Visualization</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-96 flex items-center justify-center bg-gray-50 rounded-lg">
                    <div className="text-center">
                      <TrendingUp className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-600">
                        Interactive chart showing risk-return combinations
                      </p>
                      <p className="text-sm text-gray-500 mt-2">
                        {data.volatilities.length} portfolio combinations calculated
                      </p>
                    </div>
                  </div>
                  
                  <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                    <h4 className="font-semibold text-blue-800 mb-2">Understanding the Efficient Frontier</h4>
                    <ul className="text-sm text-blue-700 space-y-1">
                      <li>• Each point represents an optimal portfolio with different risk-return characteristics</li>
                      <li>• Points above the curve are impossible, points below are sub-optimal</li>
                      <li>• The maximum Sharpe ratio point offers the best risk-adjusted returns</li>
                      <li>• The minimum volatility point has the lowest risk</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>

        <BackToMain />
      </div>
    </div>
  );
}