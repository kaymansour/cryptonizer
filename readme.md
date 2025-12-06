# Cryptocurrency Portfolio Optimizer with AI-Powered Trading

A sophisticated portfolio optimization and backtesting platform that combines **Modern Portfolio Theory (MPT)** with **LSTM neural networks** to create, analyze, and backtest cryptocurrency investment strategies.

## 🚀 Key Features

### Portfolio Optimization
- **Modern Portfolio Theory (MPT)**: Optimize portfolios using the Efficient Frontier to maximize risk-adjusted returns
- **AI-Enhanced Optimization**: Integrate LSTM price predictions (60% ML + 40% historical data) for forward-looking portfolio allocation
- **Dual Strategy Support**:
  - **Maximum Sharpe Ratio**: Optimize for best risk-adjusted returns
  - **Minimum Volatility**: Conservative approach focused on stability
- **10+ Cryptocurrencies**: Support for BTC, ETH, BNB, ADA, SOL, DOT, AVAX, LINK, ATOM, XRP, and TRX
- **Flexible Time Horizons**: Analyze portfolios over 3 months, 6 months, 1 year, or 2 years

### AI-Powered Trading & Backtesting
- **LSTM Neural Networks**: Attention-based LSTM models trained on historical price data and technical indicators
- **Multi-Strategy Backtesting**: Compare ML-driven trading against Buy & Hold, RSI, and MACD strategies
- **Advanced Risk Management**:
  - Stop-loss and take-profit automation
  - Trailing stops for profit protection
  - Position sizing limits
  - Trade cooldown periods
- **Real-time Predictions**: 4-hour and daily timeframe predictions for all supported cryptocurrencies

### Personalized Investment Profiles
Configure your portfolio based on:
- **Trading Frequency**: Passive, Moderate, or Active
- **Loss Tolerance**: Conservative (10%), Moderate (20%), or Aggressive (30%+)
- **Profit Taking Strategy**: Quick (3-5%), Balanced (5-10%), or Patient (10%+)
- **Investment Horizon**: Short-term (1-3 months), Medium-term (3-12 months), or Long-term (1+ years)

### Portfolio Management
- **Save & Track**: Store optimized portfolios and backtest results with user authentication (Clerk)
- **Historical Analysis**: View detailed performance metrics, trade history, and portfolio evolution
- **Visual Analytics**: Interactive charts showing portfolio value, drawdown, strategy comparisons, and asset allocation

## 🛠️ Tech Stack

### Frontend
- **Next.js 15** with TypeScript
- **React 18** with Server & Client Components
- **Tailwind CSS** for styling
- **Shadcn/ui** component library
- **Recharts** for data visualization
- **Clerk** for authentication

### Backend
- **Python 3.11+** with FastAPI
- **TensorFlow/Keras** for LSTM models
- **PyPortfolioOpt** for Modern Portfolio Theory optimization
- **Pandas & NumPy** for data processing
- **SQLite** for data persistence
- **yfinance** for historical cryptocurrency data

### Machine Learning
- **Attention-based LSTM** architecture
- **60-day lookback window** with technical indicators (RSI, MACD, Bollinger Bands, Volume)
- **Ensemble predictions** combining multiple models
- **Real-time inference** with cached scalers

## 📦 Installation

### Prerequisites
- **Node.js 18+** and npm
- **Python 3.11+**
- **Git**

### 1. Clone the Repository
```bash
git clone https://github.com/kaymansour/senior.git
cd senior
```

### 2. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Return to project root
cd ..
```

### 3. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Return to project root
cd ..
```

### 4. Environment Configuration

Create a `.env.local` file in the `frontend` directory:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_key
CLERK_SECRET_KEY=your_clerk_secret
```

## 🚀 Running the Application

### Start the Backend Server
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at `http://localhost:8000`

### Start the Frontend Development Server
```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Start the Backend Development Server
```bash
cd /home/ayoub/senior/backend && source venv/bin/activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📊 Usage Guide

### 1. Create an Optimized Portfolio
1. Navigate to the **Portfolio Optimizer** page
2. Select 2+ cryptocurrencies from the available options
3. Set your investment amount
4. Configure your risk tolerance and investment goals
5. Choose analysis period and enable AI enhancement (optional)
6. Click **Optimize My Portfolio**

### 2. View AI Predictions
- Switch to the **AI Predictions** tab to see LSTM price forecasts
- View predicted price movements, confidence levels, and trend indicators
- Predictions are updated in real-time using the latest market data

### 3. Backtest Your Strategy
1. Navigate to the **Historical Backtest** tab
2. Configure backtest parameters:
   - Time period (3 months to 2 years)
   - Candle interval (4-hour or daily)
   - ML signal threshold and risk management settings
3. Run the backtest and compare against benchmark strategies
4. Analyze trade history, performance metrics, and portfolio evolution

### 4. Save & Manage Portfolios
- Click **Save Portfolio** to store your optimized allocation
- Access saved portfolios and backtests from the **Saved Data** page
- Delete or review historical results at any time

## 🔑 API Endpoints

### Portfolio Optimization
- `POST /api/optimize-portfolio` - Traditional MPT optimization
- `POST /api/optimize-portfolio-lstm` - AI-enhanced optimization

### Backtesting
- `POST /api/backtest` - Historical backtest with multiple strategies
- `POST /api/backtest/ml` - ML-powered trading backtest
- `POST /api/backtest/compare-strategies` - Compare different trading strategies

### Predictions
- `POST /api/predict` - Get LSTM price predictions for a symbol
- `POST /api/predict/batch` - Batch predictions for multiple symbols

### Portfolio Management
- `GET /api/saved-portfolios` - Fetch user's saved portfolios
- `POST /api/saved-portfolios` - Save a new portfolio
- `DELETE /api/saved-portfolios/{id}` - Delete a portfolio

### ML Backtest Results
- `GET /api/ml-backtest-results` - Fetch user's backtest results
- `POST /api/ml-backtest-results` - Save backtest results
- `DELETE /api/ml-backtest-results/{id}` - Delete backtest results

## 🧪 Model Training

Pre-trained LSTM models are included in the `backend/models` directory. To retrain models:

```bash
cd backend
python models/hybrid_predictor.py
```

Models are trained on:
- Historical price data (OHLCV)
- Technical indicators (RSI, MACD, Bollinger Bands)
- Volume analysis
- 60-day lookback windows

## 📈 Performance Metrics

The system tracks comprehensive metrics including:
- **Returns**: Total, annualized, and risk-adjusted returns
- **Risk Metrics**: Volatility, Sharpe ratio, maximum drawdown, Value at Risk
- **Trading Stats**: Win rate, total trades, average win/loss, profit factor
- **Strategy Comparison**: Side-by-side performance against benchmarks

## 🔒 Security & Authentication

- User authentication via **Clerk**
- Secure API endpoints with user ID verification
- Data isolation per user in SQLite database
- No API keys required for CoinGecko integration

## 📝 Notes

- The system uses **yfinance** for historical cryptocurrency data
- CoinGecko API is used for metadata (no API key required)
- LSTM models support both 4-hour and daily timeframes
- Portfolio weights are constrained: 5% minimum, 60% maximum per asset

## 🤝 Contributing

This is a senior project developed for educational purposes. For questions or suggestions, please open an issue on GitHub.

---

**Developed by**: Ayoub and Kawthar  
**Repository**: [github.com/kaymansour/senior](https://github.com/kaymansour/senior)

