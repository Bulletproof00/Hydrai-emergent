# CHAiNALYZE v2 - Kompletter Neubau-Plan
## KI-gesteuerte Krypto-Trading & Analyse-Plattform

---

## Vision

Eine **modulare, professionelle KI-Trading-Plattform**, die die Lektionen aus CHAiNALYZE v1
und den Best Practices von Freqtrade, Jesse und Hummingbot vereint. Der Fokus liegt auf:

1. **Validierbare Strategien** (Backtesting-first)
2. **Echte Daten** (keine Mock-Daten)
3. **Risk Management als Kernfeature** (nicht als Nachgedanke)
4. **Saubere Architektur** (modular, testbar, erweiterbar)
5. **Security by Design** (keine Secrets im Code)

---

## Phase 1: Fundament (Core Engine)

### 1.1 Projekt-Struktur

```
chainalyze-v2/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI Entry Point (schlank)
│   │   ├── config.py                  # Pydantic Settings (env-basiert)
│   │   ├── dependencies.py            # Dependency Injection Container
│   │   │
│   │   ├── api/                       # API Layer (nur Routing)
│   │   │   ├── routes/
│   │   │   │   ├── trading.py
│   │   │   │   ├── market_data.py
│   │   │   │   ├── analysis.py
│   │   │   │   ├── ai.py
│   │   │   │   ├── backtesting.py
│   │   │   │   └── auth.py
│   │   │   └── websockets/
│   │   │       ├── price_stream.py
│   │   │       └── trade_updates.py
│   │   │
│   │   ├── core/                      # Business Logic
│   │   │   ├── trading/
│   │   │   │   ├── engine.py          # Paper + Live Trading Engine
│   │   │   │   ├── order_manager.py   # Order Lifecycle
│   │   │   │   ├── position_manager.py
│   │   │   │   ├── risk_manager.py    # Risk Management (NEU)
│   │   │   │   └── fee_model.py       # Realistisches Fee-Modell
│   │   │   │
│   │   │   ├── strategy/
│   │   │   │   ├── base.py            # Abstrakte Strategy-Klasse
│   │   │   │   ├── registry.py        # Strategy Discovery & Registry
│   │   │   │   └── builtin/           # Mitgelieferte Strategien
│   │   │   │       ├── rsi_divergence.py
│   │   │   │       ├── smart_money_flow.py
│   │   │   │       └── correlation_regime.py
│   │   │   │
│   │   │   ├── backtesting/           # Backtesting Engine (NEU)
│   │   │   │   ├── engine.py          # Core Backtester
│   │   │   │   ├── simulator.py       # Order-Fill Simulation
│   │   │   │   ├── metrics.py         # Sharpe, Sortino, Max DD, etc.
│   │   │   │   ├── walk_forward.py    # Walk-Forward Analyse
│   │   │   │   └── optimizer.py       # Hyperparameter-Optimierung (Optuna)
│   │   │   │
│   │   │   └── ai/
│   │   │       ├── llm_router.py      # Multi-Model Router (LiteLLM)
│   │   │       ├── trading_analyst.py  # KI-Marktanalyse
│   │   │       ├── feedback_loop.py   # Prediction Tracking (NEU)
│   │   │       ├── strategy_generator.py  # KI-Strategie-Generierung
│   │   │       └── sandbox.py         # Sichere Code-Ausfuehrung
│   │   │
│   │   ├── data/                      # Daten-Layer
│   │   │   ├── providers/
│   │   │   │   ├── base.py            # Abstract Provider Interface
│   │   │   │   ├── binance.py         # Binance REST + WebSocket
│   │   │   │   ├── coingecko.py       # CoinGecko Fallback
│   │   │   │   ├── fred.py            # Federal Reserve Makro-Daten
│   │   │   │   ├── glassnode.py       # On-Chain Daten
│   │   │   │   └── news.py            # News Aggregation
│   │   │   │
│   │   │   ├── pipeline.py            # Data Pipeline mit Circuit-Breaker
│   │   │   ├── cache.py               # Redis Cache Layer
│   │   │   ├── storage.py             # MongoDB Persistence
│   │   │   └── models.py              # Pydantic Data Models (OHLCV, etc.)
│   │   │
│   │   ├── analysis/                  # Analyse-Module
│   │   │   ├── technical.py           # Technische Indikatoren (ta-lib)
│   │   │   ├── smart_money.py         # Smart Money Indicators
│   │   │   ├── correlation.py         # Korrelationsanalyse mit Regime-Erkennung
│   │   │   ├── sentiment.py           # Sentiment-Analyse
│   │   │   └── on_chain.py            # On-Chain-Metriken
│   │   │
│   │   └── infrastructure/
│   │       ├── security.py            # JWT, API-Key Mgmt, Rate Limiting
│   │       ├── circuit_breaker.py     # Circuit Breaker Pattern
│   │       ├── logging.py             # Strukturiertes JSON-Logging
│   │       └── monitoring.py          # Prometheus Metrics Export
│   │
│   ├── strategies/                    # User-Strategien (Plugin-Ordner)
│   │   └── example_strategy.py
│   │
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   │
│   ├── pyproject.toml                 # Poetry fuer Dependency Management
│   ├── Dockerfile
│   └── alembic/                       # DB Migrations
│
├── frontend/
│   ├── src/
│   │   ├── app/                       # Next.js App Router
│   │   ├── components/
│   │   │   ├── trading/               # Trading UI
│   │   │   ├── charts/                # TradingView Lightweight Charts
│   │   │   ├── backtesting/           # Backtest-Ergebnisse
│   │   │   ├── ai/                    # KI-Chat & Dashboard
│   │   │   └── ui/                    # Shadcn/ui Basis-Komponenten
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── stores/                    # Zustand State Management
│   │
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml
├── .github/
│   └── workflows/
│       ├── ci.yml                     # Lint, Test, Type-Check
│       ├── security.yml               # Dependency + Secret Scanning
│       └── deploy.yml                 # Staging/Production Deploy
│
├── .env.example
└── docs/
    ├── architecture.md
    ├── strategy-guide.md
    └── api-reference.md
```

### 1.2 Technologie-Stack

| Komponente | Technologie | Begruendung |
|-----------|-------------|-------------|
| **Backend** | FastAPI + Python 3.12 | Async, schnell, Typing |
| **Frontend** | Next.js 15 + TypeScript | SSR, App Router, Performance |
| **Datenbank** | PostgreSQL + TimescaleDB | Zeitreihen-optimiert (besser als MongoDB fuer OHLCV) |
| **Cache** | Redis 7 | Echtzeit-Preise, Session-Daten |
| **Charts** | TradingView Lightweight Charts | Professionell, performant |
| **State Mgmt** | Zustand | Leichtgewichtig, TypeScript-nativ |
| **AI/LLM** | LiteLLM (Multi-Model) | Gemini, Claude, GPT-4 als Fallback |
| **ML** | scikit-learn + Optuna | Bewährt fuer Feature-Engineering + Optimierung |
| **Exchange** | CCXT | 100+ Exchanges, unified API |
| **Dependencies** | Poetry (Backend), pnpm (Frontend) | Lockfiles, reproducible builds |
| **Monitoring** | Prometheus + Grafana | Industry Standard |
| **CI/CD** | GitHub Actions | Direkt integriert |

### 1.3 Config & Security (von Tag 1)

**Datei: `backend/app/config.py`**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Keine Fallback-Werte fuer Secrets!
    database_url: str
    redis_url: str
    jwt_secret: str  # Kein Default = App startet nicht ohne

    # API Keys (optional - Features degradieren graceful)
    gemini_api_key: str | None = None
    binance_api_key: str | None = None
    glassnode_api_key: str | None = None
    fred_api_key: str | None = None

    # Trading Defaults
    initial_balance: float = 10_000.0
    max_leverage: int = 20  # Konservativer als 100x
    max_drawdown_pct: float = 0.20  # 20% Kill-Switch

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

---

## Phase 2: Data Pipeline (Echte Daten)

### 2.1 Provider-Architektur mit Circuit Breaker

```python
# Abstrakte Basis fuer alle Provider
class DataProvider(ABC):
    @abstractmethod
    async def get_ohlcv(self, symbol, timeframe, since, limit) -> list[OHLCV]: ...

    @abstractmethod
    async def get_ticker(self, symbol) -> Ticker: ...

    @abstractmethod
    async def health_check(self) -> bool: ...

# Circuit Breaker verhindert wiederholte Aufrufe an ausgefallene Provider
class DataPipeline:
    def __init__(self, providers: list[DataProvider]):
        self.providers = providers  # Sortiert nach Prioritaet
        self.breakers = {p: CircuitBreaker(fail_max=3, reset_timeout=60) for p in providers}

    async def get_ohlcv(self, symbol, timeframe, since, limit):
        for provider in self.providers:
            if self.breakers[provider].state == "open":
                continue  # Provider ist ausgefallen, ueberspringe
            try:
                return await self.breakers[provider].call(
                    provider.get_ohlcv, symbol, timeframe, since, limit
                )
            except Exception:
                continue
        raise DataUnavailableError("Alle Provider ausgefallen")
```

### 2.2 Datenquellen-Mapping

| Daten-Typ | Primaer | Fallback | Verwendung |
|-----------|---------|----------|------------|
| OHLCV + Trades | Binance (CCXT) | CoinGecko | Backtesting, Charts, Indikatoren |
| Orderbuch L2 | Binance WebSocket | - | Slippage-Modell, Liquiditaet |
| Funding Rates | Binance Futures | CoinGlass | Smart Money, Sentiment |
| Open Interest | Binance Futures | CoinGlass | Leverage-Analyse |
| Liquidationen | Binance Futures | CoinGlass | Heatmaps, Risiko |
| Makro-Daten (M2, DXY) | FRED API | yfinance | Korrelationsanalyse |
| Aktienindizes (SPX, NDX) | yfinance | Alpha Vantage | Korrelation, Regime |
| On-Chain (MVRV, SOPR) | Glassnode | CryptoQuant | Fundamentalanalyse |
| News | CryptoPanic API | RSS Feeds | Sentiment, Event-Trading |
| Social Sentiment | LunarCrush | Alternative.me (F&G) | Sentiment-Score |

### 2.3 TimescaleDB fuer Zeitreihen

Statt MongoDB fuer OHLCV-Daten: TimescaleDB (PostgreSQL-Extension) nutzen.

```sql
-- Hypertable fuer optimierte Zeitreihen-Abfragen
CREATE TABLE ohlcv (
    time        TIMESTAMPTZ NOT NULL,
    symbol      TEXT NOT NULL,
    timeframe   TEXT NOT NULL,
    open        DOUBLE PRECISION,
    high        DOUBLE PRECISION,
    low         DOUBLE PRECISION,
    close       DOUBLE PRECISION,
    volume      DOUBLE PRECISION
);

SELECT create_hypertable('ohlcv', 'time');

-- Continuous Aggregates fuer schnelle Abfragen
CREATE MATERIALIZED VIEW ohlcv_1h
WITH (timescaledb.continuous) AS
SELECT time_bucket('1 hour', time) AS bucket,
       symbol,
       first(open, time) AS open,
       max(high) AS high,
       min(low) AS low,
       last(close, time) AS close,
       sum(volume) AS volume
FROM ohlcv
WHERE timeframe = '1m'
GROUP BY bucket, symbol;
```

---

## Phase 3: Trading Engine

### 3.1 Clean Strategy API (inspiriert von Jesse/Freqtrade)

```python
from chainalyze.strategy import Strategy, Signal

class RSIDivergenceStrategy(Strategy):
    """Beispiel-Strategie: RSI Divergenz mit Smart Money Bestaetigung"""

    # Konfiguration
    name = "RSI Divergence + Smart Money"
    timeframe = "4h"
    symbols = ["BTC/USDT", "ETH/USDT"]

    # Parameter (optimierbar via Backtesting)
    rsi_period: int = 14
    rsi_oversold: float = 30
    rsi_overbought: float = 70
    min_funding_rate: float = -0.01

    def indicators(self, candles):
        """Indikatoren berechnen - wird automatisch gecacht"""
        candles["rsi"] = ta.rsi(candles.close, self.rsi_period)
        candles["ema_50"] = ta.ema(candles.close, 50)
        candles["ema_200"] = ta.ema(candles.close, 200)
        return candles

    def should_long(self, candles, context) -> Signal | None:
        """Long-Signal pruefen"""
        if (candles.rsi.iloc[-1] < self.rsi_oversold
            and candles.rsi.iloc[-2] > candles.rsi.iloc[-1]  # Bullish Divergenz
            and context.funding_rate < self.min_funding_rate  # Markt ueberverkauft
            and candles.close.iloc[-1] > candles.ema_200.iloc[-1]):  # Ueber 200 EMA
            return Signal(
                confidence=0.75,
                stop_loss_pct=0.03,   # 3% Stop Loss
                take_profit_pct=0.09,  # 9% Take Profit (3:1 R:R)
                leverage=3
            )
        return None

    def should_short(self, candles, context) -> Signal | None:
        """Short-Signal pruefen"""
        if (candles.rsi.iloc[-1] > self.rsi_overbought
            and context.funding_rate > 0.01  # Markt ueberkauft
            and candles.close.iloc[-1] < candles.ema_50.iloc[-1]):
            return Signal(
                confidence=0.65,
                stop_loss_pct=0.03,
                take_profit_pct=0.06,
                leverage=2
            )
        return None
```

### 3.2 Risk Manager (First-Class Citizen)

```python
class RiskManager:
    """Portfolio-weites Risk Management"""

    def __init__(self, settings: Settings):
        self.max_drawdown = settings.max_drawdown_pct       # z.B. 20%
        self.max_position_pct = 0.25                         # Max 25% pro Position
        self.max_correlated_exposure = 0.40                  # Max 40% korreliert
        self.daily_loss_limit = 0.05                         # Max 5% Tagesverlust
        self.kill_switch_active = False

    async def validate_order(self, order, portfolio) -> RiskDecision:
        """Jede Order durchlaeuft den Risk Manager"""
        checks = [
            self._check_drawdown(portfolio),
            self._check_position_size(order, portfolio),
            self._check_correlation_exposure(order, portfolio),
            self._check_daily_loss(portfolio),
            self._check_leverage(order),
        ]

        for check in checks:
            if not check.approved:
                return check  # Erste Ablehnung stoppt

        return RiskDecision(approved=True)

    def _check_drawdown(self, portfolio) -> RiskDecision:
        """Kill-Switch bei Max Drawdown"""
        current_dd = (portfolio.peak_equity - portfolio.equity) / portfolio.peak_equity
        if current_dd >= self.max_drawdown:
            self.kill_switch_active = True
            return RiskDecision(
                approved=False,
                reason=f"Max Drawdown erreicht: {current_dd:.1%}"
            )
        return RiskDecision(approved=True)
```

### 3.3 Realistisches Slippage-Modell

```python
class VolumeImpactSlippage:
    """Slippage basierend auf Orderbuch-Tiefe und Volatilitaet"""

    async def estimate(self, symbol, order_size_usd, side, orderbook=None):
        if orderbook:
            # Echte Orderbuch-Simulation
            return self._walk_orderbook(orderbook, order_size_usd, side)

        # Fallback: Modell basierend auf Volumen
        avg_volume = await self._get_avg_volume(symbol, "1h")
        volume_ratio = order_size_usd / avg_volume
        volatility = await self._get_current_volatility(symbol)

        # Square-root Impact Model (Standard in TradFi)
        impact = 0.1 * volatility * math.sqrt(volume_ratio)
        return min(impact, 0.02)  # Max 2% Slippage
```

---

## Phase 4: Backtesting Engine

### 4.1 Core Backtester

```python
class BacktestEngine:
    """Backtesting mit realistischer Simulation"""

    async def run(self, strategy: Strategy, config: BacktestConfig) -> BacktestResult:
        # 1. Historische Daten laden
        candles = await self.data_pipeline.get_ohlcv(
            symbol=config.symbol,
            timeframe=strategy.timeframe,
            since=config.start_date,
            until=config.end_date
        )

        # 2. Walk-Forward oder einfacher Backtest
        if config.walk_forward:
            return await self._walk_forward_test(strategy, candles, config)

        # 3. Candle-by-Candle Simulation (kein Look-Ahead!)
        portfolio = SimulatedPortfolio(config.initial_balance)

        for i in range(strategy.warmup_period, len(candles)):
            window = candles[:i+1]  # Nur vergangene Daten!

            # Indikatoren berechnen
            enriched = strategy.indicators(window.copy())

            # Kontext laden (Funding, OI, etc.)
            context = await self._load_context(window.index[-1], config.symbol)

            # Signale pruefen
            long_signal = strategy.should_long(enriched, context)
            short_signal = strategy.should_short(enriched, context)

            # Risk Manager
            if long_signal:
                risk_ok = self.risk_manager.validate_order(long_signal, portfolio)
                if risk_ok.approved:
                    await self._execute_simulated_order(portfolio, long_signal, candles.iloc[i])

            # Offene Positionen managen (SL/TP)
            await self._manage_positions(portfolio, candles.iloc[i])

        # 4. Metriken berechnen
        return self._calculate_metrics(portfolio)
```

### 4.2 Performance-Metriken

```python
class BacktestMetrics:
    total_return: float              # Gesamt-Rendite
    annualized_return: float         # Jaehrliche Rendite
    sharpe_ratio: float              # Risk-adjusted Return
    sortino_ratio: float             # Downside-Risk-adjusted Return
    max_drawdown: float              # Maximaler Drawdown
    max_drawdown_duration: timedelta # Laengste Drawdown-Phase
    win_rate: float                  # Gewinnrate
    profit_factor: float             # Brutto-Gewinn / Brutto-Verlust
    avg_trade_duration: timedelta    # Durchschnittliche Trade-Dauer
    total_trades: int                # Anzahl Trades
    expectancy: float                # Erwartungswert pro Trade
    calmar_ratio: float              # Return / Max Drawdown

    # Vergleichs-Benchmarks
    vs_buy_and_hold: float           # Outperformance gegenueber Buy&Hold
    vs_spy: float                    # Outperformance gegenueber S&P 500
```

### 4.3 Hyperparameter-Optimierung (Optuna)

```python
async def optimize_strategy(strategy_class, config):
    """Bayesian Optimization der Strategy-Parameter"""

    def objective(trial):
        params = {
            "rsi_period": trial.suggest_int("rsi_period", 7, 28),
            "rsi_oversold": trial.suggest_float("rsi_oversold", 20, 40),
            "rsi_overbought": trial.suggest_float("rsi_overbought", 60, 80),
        }

        strategy = strategy_class(**params)
        result = await backtest_engine.run(strategy, config)

        # Optimiere fuer Sharpe Ratio (nicht nur Return!)
        return result.sharpe_ratio

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=200)

    return study.best_params, study.best_value
```

---

## Phase 5: KI-System mit Feedback-Schleife

### 5.1 Multi-Model Router (LiteLLM)

```python
class LLMRouter:
    """Intelligenter Multi-Model Router mit Fallback"""

    MODELS = [
        {"model": "gemini/gemini-2.5-flash", "purpose": "primary", "cost": "low"},
        {"model": "anthropic/claude-sonnet-4-5-20250929", "purpose": "fallback", "cost": "medium"},
        {"model": "openai/gpt-4o", "purpose": "fallback", "cost": "medium"},
    ]

    async def analyze(self, prompt: str, context: dict) -> str:
        for model_config in self.MODELS:
            try:
                response = await litellm.acompletion(
                    model=model_config["model"],
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    timeout=30
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"Model {model_config['model']} failed: {e}")
                continue
        raise AllModelsFailedError()
```

### 5.2 Prediction Tracking & Feedback Loop (WICHTIGSTE NEUERUNG)

```python
class PredictionTracker:
    """Trackt jede KI-Vorhersage und misst die Genauigkeit"""

    async def record_prediction(self, prediction: Prediction):
        """Speichere KI-Vorhersage mit Timestamp und Kontext"""
        await self.db.predictions.insert({
            "id": uuid4(),
            "timestamp": now(),
            "symbol": prediction.symbol,
            "direction": prediction.direction,     # "long" / "short" / "neutral"
            "confidence": prediction.confidence,
            "target_price": prediction.target,
            "stop_price": prediction.stop,
            "timeframe": prediction.timeframe,
            "model_used": prediction.model,
            "market_context": prediction.context,   # RSI, Funding, etc. zum Zeitpunkt
            "actual_outcome": None,                 # Wird spaeter gefuellt
            "pnl": None,
        })

    async def evaluate_predictions(self):
        """Regelmaessig: Vergleiche Vorhersagen mit tatsaechlichem Ergebnis"""
        open_predictions = await self.db.predictions.find({"actual_outcome": None})

        for pred in open_predictions:
            if self._is_resolved(pred):
                outcome = await self._calculate_outcome(pred)
                await self.db.predictions.update(
                    {"id": pred["id"]},
                    {"actual_outcome": outcome, "pnl": outcome["pnl"]}
                )

        # Aggregierte Statistiken berechnen
        stats = await self._calculate_model_stats()
        # -> Precision, Recall, F1 pro Model, pro Timeframe, pro Marktregime

        return stats

    async def get_model_leaderboard(self):
        """Welches Modell/welche Strategie performt am besten?"""
        return await self.db.predictions.aggregate([
            {"$group": {
                "_id": "$model_used",
                "total": {"$sum": 1},
                "correct": {"$sum": {"$cond": ["$actual_outcome.correct", 1, 0]}},
                "avg_confidence": {"$avg": "$confidence"},
                "total_pnl": {"$sum": "$pnl"},
            }},
            {"$sort": {"total_pnl": -1}}
        ])
```

### 5.3 KI-Analyse mit strukturiertem Output

```python
class TradingAnalyst:
    """KI-Marktanalyse mit strukturiertem, validierbarem Output"""

    async def analyze_market(self, symbol: str) -> MarketAnalysis:
        # Kontext sammeln
        context = await self._build_context(symbol)

        prompt = f"""Analysiere {symbol} basierend auf folgenden Daten:

Preis: ${context.price} | 24h Change: {context.change_24h}%
RSI(14): {context.rsi} | Funding Rate: {context.funding_rate}%
Open Interest Change 24h: {context.oi_change}%
BTC-DXY Korrelation: {context.btc_dxy_corr}
Marktregime: {context.regime}

Antworte NUR im folgenden JSON-Format:
{{
  "direction": "long|short|neutral",
  "confidence": 0.0-1.0,
  "entry_zone": [min_price, max_price],
  "stop_loss": price,
  "targets": [tp1, tp2, tp3],
  "timeframe": "4h|1d|1w",
  "reasoning": "1-2 Saetze",
  "key_levels": [support1, resistance1],
  "risk_factors": ["factor1", "factor2"]
}}"""

        response = await self.llm.analyze(prompt, context)
        analysis = MarketAnalysis.model_validate_json(response)

        # Prediction tracken fuer spaetere Auswertung
        await self.tracker.record_prediction(analysis.to_prediction())

        return analysis
```

---

## Phase 6: Korrelationsanalyse mit Regime-Erkennung

### 6.1 Rolling Correlations + Regime Detection

```python
class AdvancedCorrelation:
    """Korrelationsanalyse mit Marktregime-Erkennung"""

    async def analyze(self, symbol: str = "BTC/USDT"):
        btc_prices = await self.get_daily_prices(symbol, days=365)

        results = {}
        for macro_name, macro_symbol in self.macro_assets.items():
            macro_prices = await self.get_macro_data(macro_symbol, days=365)

            # Rolling Correlations (nicht nur ein Wert!)
            results[macro_name] = {
                "rolling_30d": self._rolling_corr(btc_prices, macro_prices, 30),
                "rolling_90d": self._rolling_corr(btc_prices, macro_prices, 90),
                "rolling_365d": self._rolling_corr(btc_prices, macro_prices, 365),

                # Korrelation pro Regime
                "bull_market_corr": self._regime_corr(btc_prices, macro_prices, "bull"),
                "bear_market_corr": self._regime_corr(btc_prices, macro_prices, "bear"),
                "range_market_corr": self._regime_corr(btc_prices, macro_prices, "range"),

                # Optimaler Time-Lag
                "optimal_lag": self._find_optimal_lag(btc_prices, macro_prices),
            }

        # Aktuelles Regime bestimmen
        results["current_regime"] = self._detect_regime(btc_prices)

        return results

    def _detect_regime(self, prices) -> str:
        """Hidden Markov Model fuer Regime-Erkennung"""
        returns = prices.pct_change().dropna()
        model = hmm.GaussianHMM(n_components=3, covariance_type="full")
        model.fit(returns.values.reshape(-1, 1))

        states = model.predict(returns.values.reshape(-1, 1))
        current_state = states[-1]

        # States nach Rendite sortieren -> bull/range/bear
        state_means = [model.means_[i][0] for i in range(3)]
        sorted_states = sorted(range(3), key=lambda i: state_means[i])

        regime_map = {sorted_states[0]: "bear", sorted_states[1]: "range", sorted_states[2]: "bull"}
        return regime_map[current_state]
```

---

## Phase 7: Frontend

### 7.1 Kern-Seiten

| Seite | Funktion |
|-------|----------|
| **Dashboard** | Portfolio-Uebersicht, PnL, offene Positionen, KI-Score |
| **Trading** | Order-Eingabe, Positionen, Orderbuch, Trade-History |
| **Charts** | TradingView Charts mit Indikatoren, Liquidation Overlay |
| **Analyse** | Korrelations-Heatmap, Smart Money, Sentiment, On-Chain |
| **Backtesting** | Strategie auswaehlen, Parameter setzen, Ergebnisse visualisieren |
| **KI-Chat** | Chat mit Trading-KI, Empfehlungs-History mit Outcome-Tracking |
| **Strategien** | Strategy-Editor, Performance-Vergleich, Optimierungs-Ergebnisse |

### 7.2 Tech-Entscheidungen

- **TradingView Lightweight Charts** statt Canvas-Eigenimplementierung (professioneller, weniger Bugs)
- **Zustand** statt Redux (weniger Boilerplate)
- **Next.js** statt CRA (SSR, bessere Performance, App Router)
- **Tanstack Query** fuer Server-State (Caching, Revalidation, Optimistic Updates)
- **WebSocket via native API** mit Reconnect-Logic (kein Socket.io overhead)

---

## Phase 8: DevOps & Deployment

### 8.1 Docker Compose (Production)

```yaml
services:
  postgres:
    image: timescale/timescaledb:latest-pg16
    volumes: [pgdata:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine

  backend:
    build: ./backend
    depends_on: [postgres, redis]
    environment:
      - DATABASE_URL=postgresql://...
      - REDIS_URL=redis://redis:6379
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]

  frontend:
    build: ./frontend
    depends_on: [backend]

  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]

  prometheus:
    image: prom/prometheus
    volumes: [./prometheus.yml:/etc/prometheus/prometheus.yml]

  grafana:
    image: grafana/grafana
    depends_on: [prometheus]
```

### 8.2 CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  backend:
    steps:
      - uses: actions/checkout@v4
      - run: poetry install
      - run: poetry run ruff check .           # Linting
      - run: poetry run mypy .                  # Type Checking
      - run: poetry run pytest tests/unit       # Unit Tests
      - run: poetry run pytest tests/integration # Integration Tests
      - run: poetry run bandit -r app/          # Security Scan

  frontend:
    steps:
      - run: pnpm install
      - run: pnpm lint
      - run: pnpm type-check
      - run: pnpm test
      - run: pnpm build

  security:
    steps:
      - uses: github/codeql-action/analyze@v3
      - run: trivy fs --severity HIGH,CRITICAL .
```

---

## Implementierungs-Reihenfolge

### Sprint 1 (Woche 1-2): Fundament
- [ ] Projekt-Struktur aufsetzen (Poetry, Next.js, Docker)
- [ ] Config-System mit Pydantic Settings
- [ ] PostgreSQL + TimescaleDB Schema
- [ ] Binance Data Provider (OHLCV + WebSocket)
- [ ] Redis Cache Layer
- [ ] Basis-API (Health, Market Data)
- [ ] CI/CD Pipeline (Linting, Tests)

### Sprint 2 (Woche 3-4): Trading Engine
- [ ] Strategy Base Class + Registry
- [ ] Paper Trading Engine mit realistischem Fee/Slippage-Modell
- [ ] Risk Manager (Drawdown, Position Sizing, Kill-Switch)
- [ ] Order Manager (Market, Limit, SL, TP)
- [ ] Trading API Endpoints
- [ ] Frontend: Trading Interface + Charts (TradingView)

### Sprint 3 (Woche 5-6): Backtesting
- [ ] Backtesting Engine (Candle-by-Candle, kein Look-Ahead)
- [ ] Metriken-Berechnung (Sharpe, Sortino, Max DD, etc.)
- [ ] Walk-Forward-Analyse
- [ ] Optuna Hyperparameter-Optimierung
- [ ] 3 eingebaute Strategien (RSI, Smart Money, Correlation)
- [ ] Frontend: Backtest-Dashboard mit Ergebnis-Visualisierung

### Sprint 4 (Woche 7-8): Analyse & Daten
- [ ] Smart Money Indicators (Funding, OI, Liquidations)
- [ ] Korrelationsanalyse mit Regime-Erkennung
- [ ] FRED API Integration (M2, DXY)
- [ ] News + Sentiment Pipeline
- [ ] Data Pipeline mit Circuit Breaker
- [ ] Frontend: Analyse-Dashboard (Heatmaps, Charts)

### Sprint 5 (Woche 9-10): KI-System
- [ ] LiteLLM Multi-Model Router
- [ ] Trading Analyst (strukturierter Output)
- [ ] Prediction Tracker + Feedback Loop
- [ ] KI-Chat Interface
- [ ] Model Leaderboard
- [ ] Frontend: KI-Dashboard + Chat

### Sprint 6 (Woche 11-12): Polish & Launch
- [ ] Multi-Language Support (i18next)
- [ ] Prometheus Metrics + Grafana Dashboards
- [ ] End-to-End Tests
- [ ] Performance-Optimierung
- [ ] Security Audit
- [ ] Dokumentation (Strategy Guide, API Reference)
- [ ] Production Deployment

---

## Erfolgskriterien

Ein erfolgreicher Launch bedeutet:

1. **Backtesting liefert realistische Ergebnisse** (keine uebertriebenen Returns)
2. **Risk Management verhindert Totalverlust** (Kill-Switch funktioniert)
3. **KI-Vorhersagen werden gemessen** (Precision/Recall sichtbar)
4. **Keine Mock-Daten** (alles aus echten APIs)
5. **Zero Secrets im Code** (kein einziger API-Key hardcoded)
6. **Tests laufen gruen** (>80% Coverage Backend)
7. **Latenz < 500ms** fuer Echtzeit-Daten
8. **Clean Strategy API** (neue Strategie in < 50 Zeilen Code)
