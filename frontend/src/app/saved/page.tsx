"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useUser } from "@clerk/nextjs";
import {
  Briefcase,
  Brain,
  Trash2,
  Calendar,
  TrendingUp,
  TrendingDown,
  ArrowLeft,
  Loader2,
  FolderOpen,
  BarChart3,
  Percent,
  DollarSign,
  Activity,
  Clock,
  ChevronDown,
  Settings
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { getUserPortfolios, deletePortfolio, getUserMLBacktestResults, deleteMLBacktestResult } from "@/lib/api";

interface SavedPortfolio {
  id: number;
  name: string;
  symbols: string[];
  weights: Record<string, number>;
  total_value: number;
  expected_return?: number;
  volatility?: number;
  sharpe_ratio?: number;
  objective?: string;
  period?: string;
  created_at: string;
  preferences?: {
    trading_frequency?: string;
    loss_tolerance?: string;
    profit_taking?: string;
    investment_horizon?: string;
    signal_threshold?: number;
    max_position_size?: number;
    rsi_oversold?: number;
    rsi_overbought?: number;
    stop_loss_pct?: number;
    trailing_stop_pct?: number;
    trade_cooldown_periods?: number;
    interval?: string;
    use_trend_filter?: number;
    use_rsi_filter?: number;
    use_volume_filter?: number;
  } | null;
}

interface SavedMLBacktest {
  id: number;
  name: string;
  symbols: string[];
  weights: Record<string, number>;
  initial_investment: number;
  final_value?: number;
  total_return?: number;
  annualized_return?: number;
  sharpe_ratio?: number;
  max_drawdown?: number;
  total_trades?: number;
  win_rate?: number;
  interval?: string;
  signal_threshold?: number;
  max_position_size?: number;
  min_confidence?: number;
  rsi_oversold?: number;
  rsi_overbought?: number;
  stop_loss_pct?: number;
  trailing_stop_pct?: number;
  trade_cooldown_periods?: number;
  use_trend_filter?: number;
  use_rsi_filter?: number;
  use_volume_filter?: number;
  backtest_period?: string;
  created_at: string;
}

export default function SavedPage() {
  const router = useRouter();
  const { user, isSignedIn, isLoaded } = useUser();
  const [activeTab, setActiveTab] = useState<"portfolios" | "backtests">("portfolios");
  const [portfolios, setPortfolios] = useState<SavedPortfolio[]>([]);
  const [backtests, setBacktests] = useState<SavedMLBacktest[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [error, setError] = useState<string>("");
  const [expandedPortfolios, setExpandedPortfolios] = useState<Set<number>>(new Set());
  const [expandedBacktests, setExpandedBacktests] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (isLoaded && isSignedIn && user) {
      fetchData();
    } else if (isLoaded && !isSignedIn) {
      setLoading(false);
    }
  }, [isLoaded, isSignedIn, user]);

  const fetchData = async () => {
    if (!user) return;

    setLoading(true);
    setError("");

    try {
      const [portfolioRes, backtestRes] = await Promise.all([
        getUserPortfolios(user.id),
        getUserMLBacktestResults(user.id),
      ]);

      setPortfolios(portfolioRes.portfolios || []);
      setBacktests(backtestRes.results || []);
    } catch (err) {
      console.error("Error fetching data:", err);
      setError("Failed to load saved data. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePortfolio = async (portfolioId: number) => {
    if (!user) return;

    setDeleting(portfolioId);
    try {
      await deletePortfolio(portfolioId, user.id);
      setPortfolios(prev => prev.filter(p => p.id !== portfolioId));
    } catch (err) {
      console.error("Error deleting portfolio:", err);
      setError("Failed to delete portfolio.");
    } finally {
      setDeleting(null);
    }
  };

  const handleDeleteBacktest = async (backtestId: number) => {
    if (!user) return;

    setDeleting(backtestId);
    try {
      await deleteMLBacktestResult(backtestId, user.id);
      setBacktests(prev => prev.filter(b => b.id !== backtestId));
    } catch (err) {
      console.error("Error deleting backtest:", err);
      setError("Failed to delete backtest result.");
    } finally {
      setDeleting(null);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatCurrency = (value: number | undefined | null) => {
    if (value === undefined || value === null) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercentage = (value: number | undefined | null, isAlreadyPercentage: boolean = false) => {
    if (value === undefined || value === null) return 'N/A';
    const percentValue = isAlreadyPercentage ? value : value * 100;
    const sign = percentValue >= 0 ? '+' : '';
    return `${sign}${percentValue.toFixed(2)}%`;
  };

  const togglePortfolioExpanded = (id: number) => {
    setExpandedPortfolios(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const toggleBacktestExpanded = (id: number) => {
    setExpandedBacktests(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  // Not signed in state
  if (isLoaded && !isSignedIn) {
    return (
      <div className="min-h-screen bg-background py-8">
        <div className="container mx-auto px-4 max-w-4xl">
          <div className="text-center py-16">
            <FolderOpen className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-foreground mb-2">Sign In Required</h2>
            <p className="text-muted-foreground mb-6">
              Please sign in to view your saved portfolios and backtest results.
            </p>
            <Button onClick={() => router.push("/portfolio")} variant="outline" className="rounded-xl">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Portfolio Optimizer
            </Button>
          </div>
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
              onClick={() => router.push("/portfolio")}
              variant="outline"
              className="rounded-xl"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-foreground">My Saved Data</h1>
              <p className="text-muted-foreground">View and manage your portfolios and backtest results</p>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex flex-wrap gap-4 mb-8">
          <Button
            onClick={() => setActiveTab("portfolios")}
            variant={activeTab === "portfolios" ? "default" : "outline"}
            className="rounded-xl"
          >
            <Briefcase className="mr-2 h-5 w-5" />
            Portfolios ({portfolios.length})
          </Button>
          <Button
            onClick={() => setActiveTab("backtests")}
            variant={activeTab === "backtests" ? "default" : "outline"}
            className="rounded-xl"
          >
            <Brain className="mr-2 h-5 w-5" />
            ML Backtests ({backtests.length})
          </Button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-destructive/20 backdrop-blur-xl p-4 rounded-2xl border border-destructive/40 mb-6">
            <p className="text-destructive-foreground">{error}</p>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <span className="ml-3 text-muted-foreground">Loading your saved data...</span>
          </div>
        )}

        {/* Portfolios Tab */}
        {!loading && activeTab === "portfolios" && (
          <div className="space-y-4">
            {portfolios.length === 0 ? (
              <div className="text-center py-16 bg-card/50 rounded-2xl border border-border">
                <Briefcase className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-foreground mb-2">No Saved Portfolios</h3>
                <p className="text-muted-foreground mb-4">
                  Create and save your first optimized portfolio.
                </p>
                <Button onClick={() => router.push("/portfolio")} className="rounded-xl">
                  Create Portfolio
                </Button>
              </div>
            ) : (
              <div className="grid gap-4">
                {portfolios.map((portfolio) => (
                  <div
                    key={portfolio.id}
                    className="bg-card/50 backdrop-blur-xl rounded-2xl border border-border p-6 hover:border-primary/40 transition-all"
                  >
                    <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                      {/* Left side - Info */}
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3">
                          <Briefcase className="h-5 w-5 text-primary" />
                          <h3 className="text-lg font-semibold text-foreground">{portfolio.name}</h3>
                          {portfolio.objective && (
                            <Badge variant="secondary" className="text-xs">
                              {portfolio.objective === 'max_sharpe' ? 'Max Sharpe' : 'Min Volatility'}
                            </Badge>
                          )}
                        </div>

                        {/* Assets */}
                        <div className="flex flex-wrap gap-2 mb-3">
                          {portfolio.symbols.map((symbol) => (
                            <Badge key={symbol} variant="outline" className="text-xs">
                              {symbol.replace("-USD", "")}
                            </Badge>
                          ))}
                        </div>

                        {/* Metrics */}
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                          <div className="flex items-center gap-2">
                            <DollarSign className="h-4 w-4 text-muted-foreground" />
                            <span className="text-muted-foreground">Value:</span>
                            <span className="font-medium text-foreground">{formatCurrency(portfolio.total_value)}</span>
                          </div>
                          {portfolio.expected_return !== undefined && (
                            <div className="flex items-center gap-2">
                              <TrendingUp className="h-4 w-4 text-muted-foreground" />
                              <span className="text-muted-foreground">Return:</span>
                              <span className={`font-medium ${(portfolio.expected_return || 0) >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                                {formatPercentage(portfolio.expected_return)}
                              </span>
                            </div>
                          )}
                          {portfolio.sharpe_ratio !== undefined && (
                            <div className="flex items-center gap-2">
                              <BarChart3 className="h-4 w-4 text-muted-foreground" />
                              <span className="text-muted-foreground">Sharpe:</span>
                              <span className="font-medium text-foreground">{portfolio.sharpe_ratio?.toFixed(3)}</span>
                            </div>
                          )}
                          <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4 text-muted-foreground" />
                            <span className="text-muted-foreground">{formatDate(portfolio.created_at)}</span>
                          </div>
                        </div>

                        {/* Preferences Toggle */}
                        {portfolio.preferences && (
                          <div className="mt-4">
                            <button
                              onClick={() => togglePortfolioExpanded(portfolio.id)}
                              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
                            >
                              <Settings className="h-4 w-4" />
                              <span>Investment Preferences</span>
                              <ChevronDown className={`h-4 w-4 transition-transform ${expandedPortfolios.has(portfolio.id) ? 'rotate-180' : ''}`} />
                            </button>

                            {expandedPortfolios.has(portfolio.id) && (
                              <div className="mt-3 p-4 bg-muted/30 rounded-xl border border-border/50">
                                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
                                  {portfolio.preferences.trading_frequency && (
                                    <div>
                                      <span className="text-muted-foreground">Trading Frequency:</span>
                                      <p className="font-medium text-foreground capitalize">{portfolio.preferences.trading_frequency}</p>
                                    </div>
                                  )}
                                  {portfolio.preferences.loss_tolerance && (
                                    <div>
                                      <span className="text-muted-foreground">Loss Tolerance:</span>
                                      <p className="font-medium text-foreground capitalize">{portfolio.preferences.loss_tolerance}</p>
                                    </div>
                                  )}
                                  {portfolio.preferences.profit_taking && (
                                    <div>
                                      <span className="text-muted-foreground">Profit Taking:</span>
                                      <p className="font-medium text-foreground capitalize">{portfolio.preferences.profit_taking}</p>
                                    </div>
                                  )}
                                  {portfolio.preferences.investment_horizon && (
                                    <div>
                                      <span className="text-muted-foreground">Horizon:</span>
                                      <p className="font-medium text-foreground capitalize">{portfolio.preferences.investment_horizon}</p>
                                    </div>
                                  )}
                                  {portfolio.preferences.interval && (
                                    <div>
                                      <span className="text-muted-foreground">Interval:</span>
                                      <p className="font-medium text-foreground">{portfolio.preferences.interval}</p>
                                    </div>
                                  )}
                                  {portfolio.preferences.signal_threshold !== undefined && (
                                    <div>
                                      <span className="text-muted-foreground">Signal Threshold:</span>
                                      <p className="font-medium text-foreground">{portfolio.preferences.signal_threshold.toFixed(2)}</p>
                                    </div>
                                  )}
                                  {portfolio.preferences.max_position_size !== undefined && (
                                    <div>
                                      <span className="text-muted-foreground">Max Position:</span>
                                      <p className="font-medium text-foreground">{(portfolio.preferences.max_position_size * 100).toFixed(0)}%</p>
                                    </div>
                                  )}
                                  {portfolio.preferences.stop_loss_pct !== undefined && (
                                    <div>
                                      <span className="text-muted-foreground">Stop Loss:</span>
                                      <p className="font-medium text-foreground">{(portfolio.preferences.stop_loss_pct * 100).toFixed(1)}%</p>
                                    </div>
                                  )}
                                  {portfolio.preferences.trailing_stop_pct !== undefined && (
                                    <div>
                                      <span className="text-muted-foreground">Trailing Stop:</span>
                                      <p className="font-medium text-foreground">{(portfolio.preferences.trailing_stop_pct * 100).toFixed(1)}%</p>
                                    </div>
                                  )}
                                  {portfolio.preferences.rsi_oversold !== undefined && (
                                    <div>
                                      <span className="text-muted-foreground">RSI Oversold:</span>
                                      <p className="font-medium text-foreground">{portfolio.preferences.rsi_oversold}</p>
                                    </div>
                                  )}
                                  {portfolio.preferences.rsi_overbought !== undefined && (
                                    <div>
                                      <span className="text-muted-foreground">RSI Overbought:</span>
                                      <p className="font-medium text-foreground">{portfolio.preferences.rsi_overbought}</p>
                                    </div>
                                  )}
                                  {portfolio.preferences.trade_cooldown_periods !== undefined && (
                                    <div>
                                      <span className="text-muted-foreground">Cooldown:</span>
                                      <p className="font-medium text-foreground">{portfolio.preferences.trade_cooldown_periods} periods</p>
                                    </div>
                                  )}
                                </div>
                                {/* <div className="mt-3 pt-3 border-t border-border/50 flex gap-4 text-xs">
                                  <span className="text-muted-foreground">Filters:</span>
                                  {portfolio.preferences.use_trend_filter ? (
                                    <span className="text-emerald-500">✓ Trend</span>
                                  ) : (
                                    <span className="text-muted-foreground">✗ Trend</span>
                                  )}
                                  {portfolio.preferences.use_rsi_filter ? (
                                    <span className="text-emerald-500">✓ RSI</span>
                                  ) : (
                                    <span className="text-muted-foreground">✗ RSI</span>
                                  )}
                                  {portfolio.preferences.use_volume_filter ? (
                                    <span className="text-emerald-500">✓ Volume</span>
                                  ) : (
                                    <span className="text-muted-foreground">✗ Volume</span>
                                  )}
                                </div> */}
                              </div>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Right side - Actions */}
                      <div className="flex items-center gap-2">
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button
                              variant="outline"
                              size="sm"
                              className="rounded-xl text-destructive hover:bg-destructive/10"
                              disabled={deleting === portfolio.id}
                            >
                              {deleting === portfolio.id ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Trash2 className="h-4 w-4" />
                              )}
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Delete Portfolio</AlertDialogTitle>
                              <AlertDialogDescription>
                                Are you sure you want to delete &quot;{portfolio.name}&quot;? This action cannot be undone.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Cancel</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() => handleDeletePortfolio(portfolio.id)}
                                className="bg-destructive hover:bg-destructive/90"
                              >
                                Delete
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Backtests Tab */}
        {!loading && activeTab === "backtests" && (
          <div className="space-y-4">
            {backtests.length === 0 ? (
              <div className="text-center py-16 bg-card/50 rounded-2xl border border-border">
                <Brain className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-foreground mb-2">No Saved Backtests</h3>
                <p className="text-muted-foreground mb-4">
                  Run an ML backtest and save the results to see them here.
                </p>
                <Button onClick={() => router.push("/portfolio")} className="rounded-xl">
                  Create Portfolio & Backtest
                </Button>
              </div>
            ) : (
              <div className="grid gap-4">
                {backtests.map((backtest) => (
                  <div
                    key={backtest.id}
                    className="bg-card/50 backdrop-blur-xl rounded-2xl border border-border p-6 hover:border-primary/40 transition-all"
                  >
                    <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                      {/* Left side - Info */}
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3">
                          <Brain className="h-5 w-5 text-purple-500" />
                          <h3 className="text-lg font-semibold text-foreground">{backtest.name}</h3>
                          {backtest.backtest_period && (
                            <Badge variant="secondary" className="text-xs">
                              {backtest.backtest_period}
                            </Badge>
                          )}
                          {backtest.interval && (
                            <Badge variant="outline" className="text-xs">
                              {backtest.interval}
                            </Badge>
                          )}
                        </div>

                        {/* Assets */}
                        <div className="flex flex-wrap gap-2 mb-3">
                          {backtest.symbols.map((symbol) => (
                            <Badge key={symbol} variant="outline" className="text-xs">
                              {symbol.replace("-USD", "")}
                            </Badge>
                          ))}
                        </div>

                        {/* Metrics */}
                        <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 text-sm">
                          <div className="flex items-center gap-2">
                            <DollarSign className="h-4 w-4 text-muted-foreground" />
                            <span className="text-muted-foreground">Initial:</span>
                            <span className="font-medium text-foreground">{formatCurrency(backtest.initial_investment)}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            {(backtest.total_return || 0) >= 0 ? (
                              <TrendingUp className="h-4 w-4 text-emerald-500" />
                            ) : (
                              <TrendingDown className="h-4 w-4 text-red-500" />
                            )}
                            <span className="text-muted-foreground">Return:</span>
                            <span className={`font-medium ${(backtest.total_return || 0) >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                              {formatPercentage(backtest.total_return, true)}
                            </span>
                          </div>
                          {backtest.total_trades !== undefined && (
                            <div className="flex items-center gap-2">
                              <Activity className="h-4 w-4 text-muted-foreground" />
                              <span className="text-muted-foreground">Trades:</span>
                              <span className="font-medium text-foreground">{backtest.total_trades}</span>
                            </div>
                          )}
                          {backtest.win_rate !== undefined && (
                            <div className="flex items-center gap-2">
                              <Percent className="h-4 w-4 text-muted-foreground" />
                              <span className="text-muted-foreground">Win Rate:</span>
                              <span className="font-medium text-foreground">{backtest.win_rate?.toFixed(1)}%</span>
                            </div>
                          )}
                          <div className="flex items-center gap-2">
                            <Clock className="h-4 w-4 text-muted-foreground" />
                            <span className="text-muted-foreground">{formatDate(backtest.created_at)}</span>
                          </div>
                        </div>

                        {/* Final Value */}
                        {backtest.final_value && (
                          <div className="mt-3 pt-3 border-t border-border flex items-center gap-4">
                            <span className="text-sm text-muted-foreground">Final Value:</span>
                            <span className={`text-lg font-bold ${(backtest.total_return || 0) >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                              {formatCurrency(backtest.final_value)}
                            </span>
                            {backtest.sharpe_ratio !== undefined && (
                              <>
                                <span className="text-sm text-muted-foreground ml-4">Sharpe:</span>
                                <span className="font-medium text-foreground">{backtest.sharpe_ratio?.toFixed(3)}</span>
                              </>
                            )}
                            {backtest.max_drawdown !== undefined && (
                              <>
                                <span className="text-sm text-muted-foreground ml-4">Max Drawdown:</span>
                                <span className="font-medium text-red-500">{backtest.max_drawdown?.toFixed(2)}%</span>
                              </>
                            )}
                          </div>
                        )}

                        {/* ML Configuration Toggle */}
                        <div className="mt-4">
                          <button
                            onClick={() => toggleBacktestExpanded(backtest.id)}
                            className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
                          >
                            <Settings className="h-4 w-4" />
                            <span>ML Configuration</span>
                            <ChevronDown className={`h-4 w-4 transition-transform ${expandedBacktests.has(backtest.id) ? 'rotate-180' : ''}`} />
                          </button>

                          {expandedBacktests.has(backtest.id) && (
                            <div className="mt-3 p-4 bg-muted/30 rounded-xl border border-border/50">
                              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
                                {backtest.signal_threshold !== undefined && (
                                  <div>
                                    <span className="text-muted-foreground">Signal Threshold:</span>
                                    <p className="font-medium text-foreground">{backtest.signal_threshold.toFixed(2)}</p>
                                  </div>
                                )}
                                {backtest.max_position_size !== undefined && (
                                  <div>
                                    <span className="text-muted-foreground">Max Position:</span>
                                    <p className="font-medium text-foreground">{(backtest.max_position_size * 100).toFixed(0)}%</p>
                                  </div>
                                )}
                                {/* {backtest.min_confidence !== undefined && (
                                  <div>
                                    <span className="text-muted-foreground">Min Confidence:</span>
                                    <p className="font-medium text-foreground">{(backtest.min_confidence * 100).toFixed(1)}%</p>
                                  </div>
                                )} */}
                                {backtest.stop_loss_pct !== undefined && (
                                  <div>
                                    <span className="text-muted-foreground">Stop Loss:</span>
                                    <p className="font-medium text-foreground">{(backtest.stop_loss_pct * 100).toFixed(1)}%</p>
                                  </div>
                                )}
                                {backtest.trailing_stop_pct !== undefined && (
                                  <div>
                                    <span className="text-muted-foreground">Trailing Stop:</span>
                                    <p className="font-medium text-foreground">{(backtest.trailing_stop_pct * 100).toFixed(1)}%</p>
                                  </div>
                                )}
                                {backtest.rsi_oversold !== undefined && (
                                  <div>
                                    <span className="text-muted-foreground">RSI Oversold:</span>
                                    <p className="font-medium text-foreground">{backtest.rsi_oversold}</p>
                                  </div>
                                )}
                                {backtest.rsi_overbought !== undefined && (
                                  <div>
                                    <span className="text-muted-foreground">RSI Overbought:</span>
                                    <p className="font-medium text-foreground">{backtest.rsi_overbought}</p>
                                  </div>
                                )}
                                {backtest.trade_cooldown_periods !== undefined && (
                                  <div>
                                    <span className="text-muted-foreground">Cooldown:</span>
                                    <p className="font-medium text-foreground">{backtest.trade_cooldown_periods} periods</p>
                                  </div>
                                )}
                                {backtest.interval && (
                                  <div>
                                    <span className="text-muted-foreground">Interval:</span>
                                    <p className="font-medium text-foreground">{backtest.interval}</p>
                                  </div>
                                )}
                              </div>
                              {/* <div className="mt-3 pt-3 border-t border-border/50 flex gap-4 text-xs">
                                <span className="text-muted-foreground">Filters:</span>
                                {backtest.use_trend_filter ? (
                                  <span className="text-emerald-500">✓ Trend</span>
                                ) : (
                                  <span className="text-muted-foreground">✗ Trend</span>
                                )}
                                {backtest.use_rsi_filter ? (
                                  <span className="text-emerald-500">✓ RSI</span>
                                ) : (
                                  <span className="text-muted-foreground">✗ RSI</span>
                                )}
                                {backtest.use_volume_filter ? (
                                  <span className="text-emerald-500">✓ Volume</span>
                                ) : (
                                  <span className="text-muted-foreground">✗ Volume</span>
                                )}
                              </div> */}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Right side - Actions */}
                      <div className="flex items-center gap-2">
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button
                              variant="outline"
                              size="sm"
                              className="rounded-xl text-destructive hover:bg-destructive/10"
                              disabled={deleting === backtest.id}
                            >
                              {deleting === backtest.id ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Trash2 className="h-4 w-4" />
                              )}
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Delete Backtest Result</AlertDialogTitle>
                              <AlertDialogDescription>
                                Are you sure you want to delete &quot;{backtest.name}&quot;? This action cannot be undone.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Cancel</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() => handleDeleteBacktest(backtest.id)}
                                className="bg-destructive hover:bg-destructive/90"
                              >
                                Delete
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
