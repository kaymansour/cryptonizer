# Saved Portfolios Feature

This feature allows users to save their optimized portfolio configurations along with their investment preferences.

## Database Schema

### Tables

#### 1. `portfolios`
Stores optimized portfolio configurations.

**Columns:**
- `id` (INTEGER PRIMARY KEY): Auto-incrementing portfolio ID
- `clerk_id` (TEXT NOT NULL): Foreign key to users table
- `name` (TEXT NOT NULL): User-defined portfolio name
- `symbols` (TEXT NOT NULL): JSON array of cryptocurrency symbols
- `weights` (TEXT NOT NULL): JSON object of symbol→weight mappings
- `total_value` (REAL NOT NULL): Total portfolio value in USD
- `expected_return` (REAL): Expected annual return (decimal)
- `volatility` (REAL): Portfolio volatility/risk (decimal)
- `sharpe_ratio` (REAL): Sharpe ratio
- `objective` (TEXT): Optimization objective (max_sharpe, min_volatility, etc.)
- `period` (TEXT): Historical data period (1y, 2y, etc.)
- `allocation` (TEXT): JSON object of discrete allocation results
- `created_at` (TIMESTAMP): Portfolio creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

**Foreign Keys:**
- `clerk_id` → `users.clerk_id` (CASCADE DELETE)

**Indexes:**
- `idx_portfolios_clerk_id` on `clerk_id`
- `idx_portfolios_created_at` on `created_at DESC`

#### 2. `investment_preferences`
Stores ML configuration and investment strategy preferences for each portfolio.

**Columns:**
- `id` (INTEGER PRIMARY KEY): Auto-incrementing preference ID
- `portfolio_id` (INTEGER NOT NULL): Foreign key to portfolios table
- `trading_frequency` (TEXT): passive/moderate/active
- `loss_tolerance` (TEXT): low/medium/high
- `profit_taking` (TEXT): quick/balanced/patient
- `investment_horizon` (TEXT): short/medium/long
- `signal_threshold` (REAL DEFAULT 2.0): ML signal threshold
- `max_position_size` (REAL DEFAULT 0.6): Maximum position size
- `rsi_oversold` (REAL DEFAULT 25): RSI oversold level
- `rsi_overbought` (REAL DEFAULT 60): RSI overbought level
- `stop_loss_pct` (REAL DEFAULT 0.03): Stop loss percentage
- `trailing_stop_pct` (REAL DEFAULT 0.05): Trailing stop percentage
- `trade_cooldown_periods` (INTEGER DEFAULT 6): Cooldown periods between trades
- `take_profit_levels` (TEXT): JSON array of take profit levels
- `interval` (TEXT DEFAULT '4h'): Trading interval (1h/4h)
- `use_trend_filter` (INTEGER DEFAULT 1): Whether to use trend filtering
- `use_rsi_filter` (INTEGER DEFAULT 1): Whether to use RSI filtering
- `use_volume_filter` (INTEGER DEFAULT 1): Whether to use volume filtering
- `created_at` (TIMESTAMP): Preferences creation timestamp
- `updated_at` (TIMESTAMP): Last update timestamp

**Foreign Keys:**
- `portfolio_id` → `portfolios.id` (CASCADE DELETE)

**Indexes:**
- `idx_investment_preferences_portfolio_id` on `portfolio_id`

## API Endpoints

### Save Portfolio
**POST** `/api/saved-portfolios`

Save a new portfolio configuration.

**Headers:**
- `X-Clerk-User-Id`: User's Clerk ID (required)

**Request Body:**
```json
{
  "name": "My Crypto Portfolio",
  "symbols": ["BTC", "ETH", "SOL"],
  "weights": {
    "BTC": 0.5,
    "ETH": 0.3,
    "SOL": 0.2
  },
  "total_value": 100000,
  "expected_return": 0.25,
  "volatility": 0.35,
  "sharpe_ratio": 1.5,
  "objective": "max_sharpe",
  "period": "1y",
  "allocation": {
    "BTC": 50,
    "ETH": 30,
    "SOL": 20
  },
  "trading_frequency": "moderate",
  "loss_tolerance": "medium",
  "profit_taking": "balanced",
  "investment_horizon": "medium",
  "ml_config": {
    "signal_threshold": 2.0,
    "max_position_size": 0.6,
    "rsi_oversold": 25,
    "rsi_overbought": 60,
    "stop_loss_pct": 0.03,
    "trailing_stop_pct": 0.05,
    "trade_cooldown_periods": 6,
    "take_profit_levels": [0.03, 0.05, 0.08],
    "interval": "4h"
  }
}
```

**Response:**
```json
{
  "success": true,
  "portfolio_id": 123,
  "message": "Portfolio 'My Crypto Portfolio' saved successfully"
}
```

### Get User Portfolios
**GET** `/api/saved-portfolios?limit=50&offset=0`

Retrieve all portfolios for the authenticated user.

**Headers:**
- `X-Clerk-User-Id`: User's Clerk ID (required)

**Query Parameters:**
- `limit` (optional, default: 50): Maximum number of portfolios to return
- `offset` (optional, default: 0): Offset for pagination

**Response:**
```json
{
  "success": true,
  "portfolios": [
    {
      "id": 123,
      "clerk_id": "user_xxx",
      "name": "My Crypto Portfolio",
      "symbols": ["BTC", "ETH", "SOL"],
      "weights": {"BTC": 0.5, "ETH": 0.3, "SOL": 0.2},
      "total_value": 100000,
      "expected_return": 0.25,
      "volatility": 0.35,
      "sharpe_ratio": 1.5,
      "objective": "max_sharpe",
      "period": "1y",
      "allocation": {...},
      "created_at": "2025-12-01T10:00:00",
      "updated_at": "2025-12-01T10:00:00",
      "preferences": {
        "trading_frequency": "moderate",
        "loss_tolerance": "medium",
        ...
      }
    }
  ],
  "total_count": 5,
  "limit": 50,
  "offset": 0
}
```

### Get Portfolio by ID
**GET** `/api/saved-portfolios/{portfolio_id}`

Retrieve a specific portfolio.

**Headers:**
- `X-Clerk-User-Id`: User's Clerk ID (required)

**Response:**
```json
{
  "success": true,
  "portfolio": {
    "id": 123,
    "name": "My Crypto Portfolio",
    ...
    "preferences": {...}
  }
}
```

### Update Portfolio Name
**PATCH** `/api/saved-portfolios/{portfolio_id}/name`

Update a portfolio's name.

**Headers:**
- `X-Clerk-User-Id`: User's Clerk ID (required)

**Request Body:**
```json
{
  "name": "Updated Portfolio Name"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Portfolio name updated successfully"
}
```

### Delete Portfolio
**DELETE** `/api/saved-portfolios/{portfolio_id}`

Delete a portfolio (cascade deletes preferences).

**Headers:**
- `X-Clerk-User-Id`: User's Clerk ID (required)

**Response:**
```json
{
  "success": true,
  "message": "Portfolio deleted successfully"
}
```

## Frontend Integration

### Saving a Portfolio

Add a "Save Portfolio" button in the portfolio optimization results page:

```typescript
const handleSavePortfolio = async () => {
  const portfolioData = {
    name: portfolioName, // From user input
    symbols: result.symbols,
    weights: result.portfolio.weights,
    total_value: result.allocation.total_value,
    expected_return: result.portfolio.expected_return,
    volatility: result.portfolio.volatility,
    sharpe_ratio: result.portfolio.sharpe_ratio,
    objective: result.portfolio.objective,
    period: result.period,
    allocation: result.allocation.allocation,
    trading_frequency: tradingFrequency,
    loss_tolerance: lossTolerance,
    profit_taking: profitTaking,
    investment_horizon: investmentHorizon,
    ml_config: mlConfig
  };

  const response = await fetch("http://localhost:8000/api/saved-portfolios", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Clerk-User-Id": user.id // From Clerk auth
    },
    body: JSON.stringify(portfolioData)
  });

  const data = await response.json();
  if (data.success) {
    // Show success message
    console.log(`Portfolio saved with ID: ${data.portfolio_id}`);
  }
};
```

## Database Files

- **Models**: `/backend/database/models/`
  - `portfolios.py` - Portfolio table model and CRUD operations
  - `investment_preferences.py` - Preferences table model and CRUD operations
  
- **Routes**: `/backend/api/routes/`
  - `saved_portfolios.py` - API endpoints for portfolio management

- **Database**: `/backend/database/`
  - `crypto_portfolio.db` - SQLite database file (auto-created)
