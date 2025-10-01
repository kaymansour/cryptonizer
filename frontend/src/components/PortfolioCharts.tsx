"use client";

import { useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PieChart, TrendingUp, BarChart3 } from 'lucide-react';

interface OptimizationResult {
  portfolio: {
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

interface PortfolioChartsProps {
  result: OptimizationResult;
}

// Simple Chart Component without external dependencies
const PieChartComponent = ({ data }: { data: Array<{ name: string; value: number; color: string }> }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(centerX, centerY) - 10;

    let currentAngle = -Math.PI / 2; // Start from top

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw pie slices
    data.forEach((slice) => {
      const sliceAngle = (slice.value / 100) * 2 * Math.PI;

      // Draw slice
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
      ctx.closePath();
      ctx.fillStyle = slice.color;
      ctx.fill();
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Add label if slice is large enough
      if (slice.value > 5) {
        const labelAngle = currentAngle + sliceAngle / 2;
        const labelX = centerX + Math.cos(labelAngle) * (radius * 0.7);
        const labelY = centerY + Math.sin(labelAngle) * (radius * 0.7);

        ctx.fillStyle = '#fff';
        ctx.font = 'bold 12px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(`${slice.value.toFixed(1)}%`, labelX, labelY);
      }

      currentAngle += sliceAngle;
    });
  }, [data]);

  return <canvas ref={canvasRef} width={300} height={300} className="mx-auto" />;
};

const LineChartComponent = ({ data }: { data: Array<{ x: number; y: number }> }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const padding = 40;
    const width = canvas.width - 2 * padding;
    const height = canvas.height - 2 * padding;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (data.length === 0) return;

    // Find min/max values
    const xValues = data.map(d => d.x);
    const yValues = data.map(d => d.y);
    const minX = Math.min(...xValues);
    const maxX = Math.max(...xValues);
    const minY = Math.min(...yValues);
    const maxY = Math.max(...yValues);

    // Draw axes
    ctx.strokeStyle = '#ccc';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, padding + height);
    ctx.lineTo(padding + width, padding + height);
    ctx.stroke();

    // Draw line
    ctx.strokeStyle = '#3b82f6';
    ctx.lineWidth = 2;
    ctx.beginPath();

    data.forEach((point, index) => {
      const x = padding + ((point.x - minX) / (maxX - minX)) * width;
      const y = padding + height - ((point.y - minY) / (maxY - minY)) * height;

      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.stroke();

    // Draw points
    ctx.fillStyle = '#3b82f6';
    data.forEach((point) => {
      const x = padding + ((point.x - minX) / (maxX - minX)) * width;
      const y = padding + height - ((point.y - minY) / (maxY - minY)) * height;
      
      ctx.beginPath();
      ctx.arc(x, y, 3, 0, 2 * Math.PI);
      ctx.fill();
    });

    // Add labels
    ctx.fillStyle = '#666';
    ctx.font = '12px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('Risk (Volatility)', canvas.width / 2, canvas.height - 10);
    
    ctx.save();
    ctx.translate(15, canvas.height / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText('Expected Return', 0, 0);
    ctx.restore();
  }, [data]);

  return <canvas ref={canvasRef} width={400} height={300} className="mx-auto" />;
};

export default function PortfolioCharts({ result }: PortfolioChartsProps) {
  // Prepare pie chart data
  const pieData = Object.entries(result.portfolio.weights)
    .filter(([, weight]) => (weight as number) > 0.001)
    .map(([symbol, weight], index) => ({
      name: symbol,
      value: (weight as number) * 100,
      color: `hsl(${index * 360 / Object.keys(result.portfolio.weights).length}, 70%, 50%)`
    }));

  // Prepare efficient frontier data
  const frontierData = result.efficient_frontier.volatilities.map((vol, index) => ({
    x: vol * 100,
    y: result.efficient_frontier.returns[index] * 100
  }));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Portfolio Allocation Pie Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <PieChart className="h-5 w-5" />
            Portfolio Allocation
          </CardTitle>
        </CardHeader>
        <CardContent>
          <PieChartComponent data={pieData} />
          <div className="mt-4 space-y-2">
            {pieData.map((item) => (
              <div key={item.name} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div 
                    className="w-4 h-4 rounded-full" 
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="font-medium">{item.name}</span>
                </div>
                <span className="text-sm text-gray-600">{item.value.toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Efficient Frontier */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Efficient Frontier
          </CardTitle>
        </CardHeader>
        <CardContent>
          <LineChartComponent data={frontierData} />
          <div className="mt-4 text-sm text-gray-600">
            <p>This chart shows the optimal risk-return combinations available.</p>
            <p className="mt-1">Your portfolio is represented by the optimal point on this curve.</p>
          </div>
        </CardContent>
      </Card>

      {/* Performance Metrics Bar Chart */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Portfolio Performance Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg border">
              <div className="text-2xl font-bold text-green-600">
                {(result.portfolio.expected_return * 100).toFixed(1)}%
              </div>
              <div className="text-sm font-medium text-green-800">Expected Return</div>
              <div className="text-xs text-green-600 mt-1">Annual</div>
            </div>
            
            <div className="text-center p-4 bg-blue-50 rounded-lg border">
              <div className="text-2xl font-bold text-blue-600">
                {(result.portfolio.volatility * 100).toFixed(1)}%
              </div>
              <div className="text-sm font-medium text-blue-800">Volatility</div>
              <div className="text-xs text-blue-600 mt-1">Risk Measure</div>
            </div>
            
            <div className="text-center p-4 bg-purple-50 rounded-lg border">
              <div className="text-2xl font-bold text-purple-600">
                {result.portfolio.sharpe_ratio.toFixed(2)}
              </div>
              <div className="text-sm font-medium text-purple-800">Sharpe Ratio</div>
              <div className="text-xs text-purple-600 mt-1">Risk-Adjusted</div>
            </div>
            
            <div className="text-center p-4 bg-orange-50 rounded-lg border">
              <div className="text-2xl font-bold text-orange-600">
                {(Math.abs(result.metrics.max_drawdown) * 100).toFixed(1)}%
              </div>
              <div className="text-sm font-medium text-orange-800">Max Drawdown</div>
              <div className="text-xs text-orange-600 mt-1">Worst Loss</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}