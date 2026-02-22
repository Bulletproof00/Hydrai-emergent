# 04 - Feature Gap Analysis

## Uebersicht: Feature-Status

```
✅ Implementiert  ⚠️ Teilweise/Mock  ❌ Nicht implementiert  🔄 Geplant (v2)
```

| Feature | Status | Details |
|---------|--------|---------|
| Paper Trading | ✅ | $10k Konto, bis 100x Leverage, funktioniert |
| Echtzeit-Marktdaten | ✅ | 3-Tier Fallback (Binance/CoinGecko/Synthetic) |
| Smart Money Indicators | ✅ | Liquidationen, OI, Funding Rates |
| KI-Analyse (Gemini) | ✅ | Trading-Empfehlungen, Marktanalyse |
| Self-Evolving AI | ✅ | 8-Stunden-Zyklen, aber ohne echte Feedback-Schleife |
| Self-Coding AI | ✅ | Plugin-Generierung, aber unsandboxed |
| BTC-Korrelationen | ✅ | SPX, DXY, M2, Gold |
| Multi-Language | ✅ | DE, EN, TR, ES, ZH |
| Candlestick Charts | ⚠️ | Buggy, falsche Preisanzeige, Canvas-basiert |
| News & Sentiment | ⚠️ | Alpha Vantage Mock-Daten statt echte APIs |
| On-Chain-Daten | ⚠️ | Felder definiert, kein Provider angebunden |
| Liquidation Heatmaps | ⚠️ | Buttons vorhanden, Grid nicht voll funktional |
| **Backtesting** | ❌🔄 | Nicht vorhanden, als v2-Kernfeature geplant |
| **Risk Management** | ❌🔄 | Kein Drawdown-Limit, kein Kill-Switch |
| **KI-Feedback-Schleife** | ❌🔄 | Vorhersagen werden nicht gemessen |
| **Circuit-Breaker** | ❌🔄 | Bei Provider-Ausfall keine intelligente Umschaltung |
| **CI/CD** | ❌🔄 | Keine Pipeline, Tests nicht automatisiert |
| **Multi-Exchange** | ❌🔄 | Nur Binance, CCXT ermoeglicht Erweiterung |

---

## Gap 1: Backtesting-System (KRITISCH)

**Aktuell:** Nicht vorhanden. Trading-Strategien sind komplett unvalidiert.

**Warum kritisch:** Ohne Backtesting ist jede Trading-Strategie reines Raten.
Es gibt keine Moeglichkeit zu pruefen, ob eine Strategie historisch profitabel
gewesen waere.

**Geplant fuer v2:**
- Candle-by-Candle Simulation (kein Look-Ahead-Bias)
- Walk-Forward-Analyse (Train/Test-Splits)
- Hyperparameter-Optimierung via Optuna (Bayesian Optimization)
- Performance-Metriken: Sharpe, Sortino, Max Drawdown, Calmar, Expectancy
- Vergleich gegen Buy & Hold und S&P 500 Benchmark
- Monte-Carlo-Simulation fuer Risiko-Abschaetzung

**Referenz:** PLAN.md Phase 4

---

## Gap 2: Risk Management (KRITISCH)

**Aktuell:** Paper Trading erlaubt 100x Leverage ohne jegliche Risikobegrenzung.

**Fehlende Komponenten:**
- Portfolio-Level Drawdown-Limit (z.B. max 20% Verlust → Kill-Switch)
- Taegliches Verlustlimit (z.B. max 5% pro Tag)
- Maximum Position Size (z.B. max 25% des Portfolios pro Position)
- Korrelations-basiertes Exposure-Limit (max 40% in korrelierte Assets)
- Kelly-Criterion Position Sizing
- Automatischer Kill-Switch bei Ueberschreitung

**Geplant fuer v2:**
```python
class RiskManager:
    max_drawdown = 0.20          # 20% Kill-Switch
    max_position_pct = 0.25       # Max 25% pro Position
    max_correlated_exposure = 0.40 # Max 40% korreliert
    daily_loss_limit = 0.05       # Max 5% Tagesverlust

    async def validate_order(self, order, portfolio) -> RiskDecision:
        # Jede Order durchlaeuft den Risk Manager
        ...
```

**Referenz:** PLAN.md Phase 3, Section 3.2

---

## Gap 3: KI-Feedback-Schleife (HOCH)

**Aktuell:** Self-Evolving AI hat 8-Stunden-Zyklen, aber kein echtes
Performance-Tracking. Vorhersagen werden generiert, aber nie gegen das
tatsaechliche Marktergebnis validiert.

**Fehlende Komponenten:**
- Prediction Tracker: Jede KI-Empfehlung mit Timestamp + Preis speichern
- Outcome-Vergleich: Nach 1h, 4h, 24h pruefen ob Empfehlung profitabel war
- Precision/Recall pro Signal-Typ
- Model Leaderboard: Welches Modell/welche Config performt am besten?
- Automatisches Downgrading schlechter Strategien
- A/B-Testing verschiedener Modell-Konfigurationen

**Geplant fuer v2:**
```python
class PredictionTracker:
    async def record_prediction(self, prediction):
        # Speichere: timestamp, symbol, direction, confidence, target, model
        ...

    async def evaluate_predictions(self):
        # Vergleiche Vorhersagen mit tatsaechlichem Ergebnis
        # Berechne Precision, Recall, F1 pro Model/Timeframe/Regime
        ...

    async def get_model_leaderboard(self):
        # Ranking: Welches Modell/welche Strategie performt am besten?
        ...
```

**Referenz:** PLAN.md Phase 5, Section 5.2

---

## Gap 4: Echte Daten-APIs (HOCH)

**Aktuell:** News, Economic Data und Sentiment nutzen Mock-Daten.

### Aktuelle Mock-Daten-Quellen
| Daten-Typ | Aktuell | Problem |
|-----------|---------|---------|
| News | Alpha Vantage Mock | Keine echten Krypto-News |
| Economic Calendar | Hardcoded | Keine FRED/EZB-Daten |
| Sentiment | Berechnet aus Preis | Kein Social Media Sentiment |
| On-Chain | Felder definiert | Kein Provider angebunden |

### Geplante echte Datenquellen (v2)
| Daten-Typ | Primaer | Fallback |
|-----------|---------|----------|
| Makro-Daten (M2, DXY, Fed Funds) | FRED API | yfinance |
| Aktienindizes (SPX, NDX) | yfinance | Alpha Vantage |
| On-Chain (MVRV, SOPR, Exchange Flows) | Glassnode | CryptoQuant |
| Krypto-News | CryptoPanic API | RSS Feeds (CoinDesk, CoinTelegraph) |
| Social Sentiment | LunarCrush | Alternative.me (Fear & Greed Index) |
| Funding Rates / OI | Binance Futures | CoinGlass |
| Liquidationen | Binance Futures | CoinGlass |

**Hinweis:** `fredapi==0.5.2` ist bereits in requirements.txt, wird aber nur
in `correlation_analysis.py` rudimentaer genutzt.

**Referenz:** PLAN.md Phase 2 + Phase 4

---

## Gap 5: Circuit-Breaker Pattern (MITTEL)

**Aktuell:** Das 3-Tier-Fallback-System (Binance → CoinGecko → Synthetic)
funktioniert grundsaetzlich, aber:
- Bei Binance-Ausfall wird trotzdem bei **jedem** Request zuerst Binance probiert
- Das fuehrt zu unnoetigem Timeout und verzoegerter Antwort
- Kein Health-Monitoring der Provider

**Geplant fuer v2:**
```python
class DataPipeline:
    def __init__(self, providers):
        self.breakers = {
            p: CircuitBreaker(fail_max=3, reset_timeout=60)
            for p in providers
        }

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
        raise DataUnavailableError()
```

**Referenz:** PLAN.md Phase 2, Section 2.1

---

## Gap 6: Korrelationsanalyse mit Regime-Erkennung (MITTEL)

**Aktuell:** `correlation_analysis.py` berechnet statische Korrelationen.
Korrelationen aendern sich aber stark je nach Marktregime (Bull/Bear/Range).

**Fehlende Komponenten:**
- Rolling Correlations ueber verschiedene Fenster (30d, 90d, 365d)
- Hidden Markov Model fuer Regime-Detection
- Conditional Correlations (Korrelation nur in bestimmten Regimes)
- Optimaler Time-Lag-Erkennung (welches Asset fuehrt welches?)

**Geplant fuer v2:**
- HMM-basierte Regime-Erkennung (3 States: Bull/Range/Bear)
- Korrelation pro Regime berechnen
- Signale basierend auf aktuellem Regime filtern

**Referenz:** PLAN.md Phase 6

---

## Gap 7: Realistischeres Trading-Modell (MITTEL)

### Slippage
**Aktuell:** Fixer Wert `base_slippage = 0.0001`
**Geplant:** Volume-Impact-Modell basierend auf Orderbuch-Tiefe und Volatilitaet
(Square-Root Impact Model, Standard in TradFi)

### Order-Book Simulation
**Aktuell:** Paper Trading nutzt nur den letzten Preis
**Geplant:** Synthetisches Orderbuch oder Binance Orderbuch-Snapshot

### Fee-Modell
**Aktuell:** Vereinfachtes Fee-Modell
**Geplant:** Exchange-spezifische Fees (Maker/Taker, VIP-Levels)

**Referenz:** PLAN.md Phase 3, Section 3.3

---

## Gap 8: CI/CD Pipeline (MITTEL)

**Aktuell:** Keine automatisierte Pipeline. 25+ Testdateien existieren,
werden aber nur manuell ausgefuehrt.

**Geplant fuer v2:**
```yaml
# .github/workflows/ci.yml
backend:
  - poetry run ruff check .           # Linting
  - poetry run mypy .                  # Type Checking
  - poetry run pytest tests/unit       # Unit Tests
  - poetry run pytest tests/integration
  - poetry run bandit -r app/          # Security Scan

frontend:
  - pnpm lint
  - pnpm type-check
  - pnpm test
  - pnpm build

security:
  - github/codeql-action/analyze@v3
  - trivy fs --severity HIGH,CRITICAL .
```

**Referenz:** PLAN.md Phase 8, Section 8.2

---

## Gap 9: LiteLLM Multi-Model Router (NIEDRIG)

**Aktuell:** Nur Google Gemini 2.5 Flash. Bei Gemini-Ausfall keine Alternative.
`litellm==1.77.5` ist in requirements.txt vorhanden, wird aber nicht genutzt.

**Geplant fuer v2:**
```python
MODELS = [
    {"model": "gemini/gemini-2.5-flash", "purpose": "primary", "cost": "low"},
    {"model": "anthropic/claude-sonnet-4-5-20250929", "purpose": "fallback", "cost": "medium"},
    {"model": "openai/gpt-4o", "purpose": "fallback", "cost": "medium"},
]
```

**Referenz:** PLAN.md Phase 5, Section 5.1

---

## Gap 10: Hardcodierte Preise (NIEDRIG)

**Datei:** `backend/modules/enhanced_smart_money.py`

Base Prices sind hardcodiert (BTC: $62.000). Diese veralten schnell und
fuehren zu falschen Berechnungen.

**Fix:** Base Prices dynamisch aus letztem API-Call beziehen oder beim
Startup initial fetchen.
