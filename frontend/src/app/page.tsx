"use client";

import { useRouter } from "next/navigation";
import { TrendingUp, Shield, Zap, BarChart3, Brain, Target } from "lucide-react";
import { AnimatedBeamMultipleOutputDemo } from "@/components/AnimatedBeam";
import { InteractiveHoverButton } from "@/components/ui/interactive-hover-button"

export default function LandingPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Hero Section */}
      <section className="container mx-auto px-6 py-8 lg:py-10">
        <div className="max-w-4xl mx-auto text-center">
          {/* Main Heading */}
          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight leading-tight mb-6">
            Optimize Your
            <span className="block bg-linear-to-r from-primary via-purple-500 to-pink-500 bg-clip-text text-transparent">
              Crypto Portfolio
            </span>
            with AI
          </h1>

          {/* Description */}
          <p className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed mb-4">
            Cryptonizer combines advanced LSTM neural networks with modern portfolio theory
            to help you make smarter investment decisions. Get AI powered predictions,
            optimize your allocations, and backtest strategies all in one place.
          </p>

          <AnimatedBeamMultipleOutputDemo className="-mt-8" />

          {/* CTA Button */}
          <div className="mt-4">
            <InteractiveHoverButton
              onClick={() => {
                const featuresSection = document.getElementById('features');
                featuresSection?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="text-lg px-8 py-3"
            >
              Discover
            </InteractiveHoverButton>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="container mx-auto px-6 py-16 lg:py-24">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl sm:text-4xl font-bold text-center mb-12">
            Powerful Features
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1: AI Predictions */}
            <div className="bg-card border border-border rounded-2xl p-6 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mb-4">
                <Brain className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">AI-Powered Predictions</h3>
              <p className="text-muted-foreground">
                Advanced LSTM neural networks analyze market trends to predict future price movements
                with high accuracy.
              </p>
            </div>

            {/* Feature 2: Portfolio Optimization */}
            <div className="bg-card border border-border rounded-2xl p-6 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mb-4">
                <Target className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Portfolio Optimization</h3>
              <p className="text-muted-foreground">
                Maximize returns while minimizing risk using modern portfolio theory and
                efficient frontier analysis.
              </p>
            </div>

            {/* Feature 3: Backtesting */}
            <div className="bg-card border border-border rounded-2xl p-6 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mb-4">
                <BarChart3 className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Strategy Backtesting</h3>
              <p className="text-muted-foreground">
                Test your trading strategies against historical data to validate performance
                before investing real capital.
              </p>
            </div>

            {/* Feature 4: Real-time Data */}
            <div className="bg-card border border-border rounded-2xl p-6 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mb-4">
                <Zap className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Real-time Market Data</h3>
              <p className="text-muted-foreground">
                Access live cryptocurrency prices, market trends, and performance metrics
                updated in real-time.
              </p>
            </div>

            {/* Feature 5: Risk Analytics */}
            <div className="bg-card border border-border rounded-2xl p-6 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mb-4">
                <Shield className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Risk Analytics</h3>
              <p className="text-muted-foreground">
                Comprehensive risk assessment with Sharpe ratios, volatility analysis,
                and correlation matrices.
              </p>
            </div>

            {/* Feature 6: Market Insights */}
            <div className="bg-card border border-border rounded-2xl p-6 hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mb-4">
                <TrendingUp className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Market Insights</h3>
              <p className="text-muted-foreground">
                Identify top gainers, losers, and trending cryptocurrencies with detailed
                charts and analytics.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-6 py-16 lg:py-24">
        <div className="max-w-4xl mx-auto bg-linear-to-r from-primary/10 via-purple-500/10 to-pink-500/10 border border-primary/20 rounded-3xl p-12 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            Ready to Optimize Your Portfolio?
          </h2>
          <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
            Join the platform using AI and make smarter crypto investment decisions.
            Start optimizing your portfolio today.
          </p>
          <InteractiveHoverButton
            onClick={() => router.push("/dashboard")}
            className="text-lg px-8 py-6 rounded-xl"
          >
            Get Started Now
          </InteractiveHoverButton>
        </div>
      </section>
    </div>
  );
}
