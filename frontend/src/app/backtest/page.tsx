"use client";

import { useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { ArrowLeft, TrendingUp, BarChart3, PieChart, DollarSign } from "lucide-react";
import { BentoCard, BentoGrid } from "@/components/ui/bento-grid";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import BacktestDashboard from "../../components/BacktestDashboard";
import StrategyComparison from "@/components/StrategyComparison";
import BackToMain from "../../components/backtomain";

interface PortfolioData {
  symbols: string[];
  weights: Record<string, number>;
  initial_investment: number;
}

export default function BacktestPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [portfolioData, setPortfolioData] = useState<PortfolioData | null>(null);
  const [activeTab, setActiveTab] = useState<"backtest" | "comparison">("backtest");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get portfolio data from URL params or localStorage
    const symbolsParam = searchParams.get("symbols");
    const weightsParam = searchParams.get("weights");
    const investmentParam = searchParams.get("investment");

    if (symbolsParam && weightsParam) {
      try {
        const symbols = JSON.parse(decodeURIComponent(symbolsParam));
        const weights = JSON.parse(decodeURIComponent(weightsParam));
        const investment = investmentParam ? parseFloat(investmentParam) : 100000;

        setPortfolioData({
          symbols,
          weights,
          initial_investment: investment,
        });
      } catch (error) {
        console.error("Error parsing portfolio data from URL:", error);
        // Try to get from localStorage as fallback
        const storedData = localStorage.getItem("portfolioData");
        if (storedData) {
          setPortfolioData(JSON.parse(storedData));
        }
      }
    } else {
      // Try to get from localStorage
      const storedData = localStorage.getItem("portfolioData");
      if (storedData) {
        setPortfolioData(JSON.parse(storedData));
      }
    }

    setLoading(false);
  }, [searchParams]);

  const handleGoBack = () => {
    router.back();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-xl text-muted-foreground">Loading backtesting data...</p>
        </div>
      </div>
    );
  }

  if (!portfolioData) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <div className="text-center max-w-md mx-auto p-8">
          <div className="bg-destructive/20 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
            <TrendingUp className="h-8 w-8 text-destructive" />
          </div>
          <h2 className="text-2xl font-bold text-foreground mb-4">No Portfolio Data Found</h2>
          <p className="text-muted-foreground mb-6">
            Please go back to the portfolio optimization page and create a portfolio first.
          </p>
          <Button
            onClick={() => router.push("/portfolio")}
            className="rounded-xl"
          >
            Go to Portfolio Optimizer
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="container mx-auto px-4 max-w-7xl">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
          <div className="flex items-center gap-4">
            <Button
              onClick={handleGoBack}
              variant="outline"
              className="rounded-xl"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-foreground">Portfolio Backtesting</h1>
              <p className="text-muted-foreground">Historical performance analysis and strategy comparison</p>
            </div>
          </div>
        </div>

        {/* Portfolio Summary - Bento Grid */}
        <BentoGrid className="lg:grid-rows-1 mb-8">
          {/* Assets */}
          <BentoCard
            name="Portfolio Assets"
            className="lg:col-start-1 lg:col-end-2 lg:row-start-1 lg:row-end-2 border-primary/40"
            Icon={PieChart}
            description={`${portfolioData.symbols.length} cryptocurrencies`}
            href="#"
            cta=""
            background={
              <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-transparent" />
            }
          >
            <div className="relative z-10 mt-4">
              <div className="flex flex-wrap gap-2">
                {portfolioData.symbols.map((symbol) => (
                  <Badge
                    key={symbol}
                    variant="secondary"
                    className="text-sm"
                  >
                    {symbol.replace("-USD", "")}
                  </Badge>
                ))}
              </div>
            </div>
          </BentoCard>

          {/* Initial Investment */}
          <BentoCard
            name="Initial Investment"
            className="lg:col-start-2 lg:col-end-3 lg:row-start-1 lg:row-end-2 border-green-500/40"
            Icon={DollarSign}
            description="Starting capital"
            href="#"
            cta=""
            background={
              <div className="absolute inset-0 bg-gradient-to-br from-green-500/10 to-transparent" />
            }
          >
            <div className="relative z-10 mt-4">
              <div className="text-3xl font-bold text-green-600 dark:text-green-400">
                ${portfolioData.initial_investment.toLocaleString()}
              </div>
            </div>
          </BentoCard>

          {/* Allocation */}
          <BentoCard
            name="Weight Allocation"
            className="lg:col-start-3 lg:col-end-4 lg:row-start-1 lg:row-end-2 border-blue-500/40"
            Icon={BarChart3}
            description="Portfolio distribution"
            href="#"
            cta=""
            background={
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-transparent" />
            }
          >
            <div className="relative z-10 mt-4">
              <div className="flex flex-wrap gap-2">
                {Object.entries(portfolioData.weights).map(([symbol, weight]) => (
                  <Badge
                    key={symbol}
                    className="bg-primary/20 text-primary hover:bg-primary/30"
                  >
                    {symbol.replace("-USD", "")}: {((weight as number) * 100).toFixed(1)}%
                  </Badge>
                ))}
              </div>
            </div>
          </BentoCard>
        </BentoGrid>

        {/* Tab Navigation */}
        <div className="flex flex-wrap gap-4 mb-8">
          <Button
            onClick={() => setActiveTab("backtest")}
            variant={activeTab === "backtest" ? "default" : "outline"}
            className="rounded-xl"
          >
            <BarChart3 className="mr-2 h-5 w-5" />
            Historical Performance
          </Button>
          <Button
            onClick={() => setActiveTab("comparison")}
            variant={activeTab === "comparison" ? "default" : "outline"}
            className="rounded-xl"
          >
            <PieChart className="mr-2 h-5 w-5" />
            Strategy Comparison
          </Button>
        </div>

        {/* Tab Content */}
        {activeTab === "backtest" && <BacktestDashboard portfolioData={portfolioData} />}
        {activeTab === "comparison" && <StrategyComparison portfolioData={portfolioData} />}

        <BackToMain />
      </div>
    </div>
  );
}