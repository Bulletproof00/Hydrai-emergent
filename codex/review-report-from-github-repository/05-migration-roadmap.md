# 05 - Migration Roadmap (v1 → v2)

## Ueberblick

```
v1 (Aktuell)                          v2 (Ziel)
─────────────                         ────────
CRA + React 19                   →    Next.js 15 + TypeScript
server.py Monolith (124 KB)      →    Modulare FastAPI Router
MongoDB                           →    PostgreSQL + TimescaleDB
pip + requirements.txt            →    Poetry + pyproject.toml
Nur Gemini                        →    LiteLLM Multi-Model
Kein Backtesting                  →    Backtesting Engine + Optuna
Kein Risk Management              →    Risk Manager + Kill-Switch
Keine CI/CD                       →    GitHub Actions Pipeline
Mock News/Sentiment               →    Echte APIs (FRED, Glassnode, CryptoPanic)
Canvas Charts                     →    TradingView Lightweight Charts
```

**Geschaetzte Gesamtdauer:** 12 Wochen (6 Sprints a 2 Wochen)

---

## Sprint 1 (Woche 1-2): Fundament

**Ziel:** Projekt-Struktur, Config, Datenbank, erste API-Endpoints

### Tasks
- [ ] Neue Projekt-Struktur aufsetzen (Poetry, pyproject.toml)
- [ ] Config-System mit Pydantic Settings (keine Fallbacks fuer Secrets)
- [ ] PostgreSQL + TimescaleDB Schema aufsetzen
  - OHLCV Hypertable
  - Continuous Aggregates fuer 1h, 4h, 1d
- [ ] Binance Data Provider (OHLCV + WebSocket) migrieren
- [ ] CoinGecko Fallback Provider
- [ ] Redis 7 Cache Layer
- [ ] Circuit-Breaker Pattern fuer Data Pipeline (`pybreaker`)
- [ ] Basis-API: `/health`, `/api/market-data`
- [ ] CI/CD Pipeline (GitHub Actions): Lint (ruff), Type-Check (mypy), Tests (pytest)
- [ ] `.env.example` ohne Secrets, Secret Scanning aktivieren

### Meilenstein
API laeuft, Echtzeit-Preise kommen ueber Circuit-Breaker-Pipeline,
TimescaleDB speichert OHLCV-Daten.

---

## Sprint 2 (Woche 3-4): Trading Engine

**Ziel:** Paper Trading mit Risk Management und realistischer Simulation

### Tasks
- [ ] Abstract Strategy Base Class + Registry
- [ ] Paper Trading Engine mit realistischem Fee/Slippage-Modell
  - Volume-Impact Slippage (Square-Root Model)
  - Exchange-spezifische Fees (Maker/Taker)
- [ ] Risk Manager (First-Class Citizen)
  - Max Drawdown (20% Kill-Switch)
  - Max Position Size (25% pro Position)
  - Max Correlated Exposure (40%)
  - Daily Loss Limit (5%)
  - Kelly-Criterion Position Sizing
- [ ] Order Manager (Market, Limit, Stop-Loss, Take-Profit)
- [ ] Position Manager (Lifecycle, PnL-Tracking)
- [ ] Trading API Endpoints
- [ ] Frontend: Trading Interface mit TradingView Lightweight Charts

### Meilenstein
Paper Trading funktioniert mit Risk Management, realistische Slippage,
Stop-Loss/Take-Profit werden korrekt ausgefuehrt.

---

## Sprint 3 (Woche 5-6): Backtesting

**Ziel:** Historische Strategie-Validierung mit professionellen Metriken

### Tasks
- [ ] Backtesting Engine (Candle-by-Candle, kein Look-Ahead-Bias)
- [ ] Order-Fill-Simulator (realistische Fills basierend auf Slippage-Modell)
- [ ] Metriken-Berechnung
  - Sharpe Ratio, Sortino Ratio
  - Max Drawdown + Drawdown-Duration
  - Win Rate, Profit Factor
  - Expectancy, Calmar Ratio
  - vs. Buy & Hold, vs. S&P 500
- [ ] Walk-Forward-Analyse (Train/Test-Splits)
- [ ] Optuna Hyperparameter-Optimierung (Bayesian)
- [ ] 3 eingebaute Strategien
  - RSI Divergenz + Smart Money Bestaetigung
  - Smart Money Flow (OI + Funding + Liquidationen)
  - Correlation Regime (BTC-DXY-M2 basiert)
- [ ] Frontend: Backtest-Dashboard mit Ergebnis-Visualisierung

### Meilenstein
Backtesting laeuft, Walk-Forward-Analyse zeigt realistische Ergebnisse,
Optuna findet optimale Parameter.

---

## Sprint 4 (Woche 7-8): Daten & Analyse

**Ziel:** Echte Daten-APIs statt Mock-Daten, erweiterte Analyse

### Tasks
- [ ] FRED API Integration (M2, DXY, Fed Funds Rate, Inflation)
- [ ] Glassnode/CryptoQuant Integration (MVRV, SOPR, Exchange Flows)
- [ ] CryptoPanic API fuer Krypto-News
- [ ] LunarCrush fuer Social Sentiment
- [ ] Alternative.me (Fear & Greed Index)
- [ ] Smart Money Indicators erweitern
  - Whale Alert Integration
  - Miner Outflow Tracking
- [ ] Korrelationsanalyse mit Regime-Erkennung
  - Rolling Correlations (30d, 90d, 365d)
  - Hidden Markov Model (Bull/Range/Bear)
  - Conditional Correlations pro Regime
  - Optimaler Time-Lag
- [ ] Data Pipeline mit Circuit Breaker fuer alle neuen Provider
- [ ] Frontend: Analyse-Dashboard (Heatmaps, Regime-Anzeige, Sentiment)

### Meilenstein
Alle Daten kommen aus echten APIs, Regime-Erkennung funktioniert,
Korrelationen werden pro Regime berechnet.

---

## Sprint 5 (Woche 9-10): KI-System

**Ziel:** Multi-Model Router, Feedback-Schleife, messbares KI-System

### Tasks
- [ ] LiteLLM Multi-Model Router
  - Primaer: Gemini 2.5 Flash (kostenguenstig)
  - Fallback 1: Claude Sonnet (qualitativ)
  - Fallback 2: GPT-4o
  - Automatisches Failover + Cost-Tracking
- [ ] Trading Analyst mit strukturiertem JSON-Output
  - Validierung ueber Pydantic Models
  - Confidence Scores, Entry/Exit Zones, Risk Factors
- [ ] Prediction Tracker + Feedback Loop
  - Jede Vorhersage mit Timestamp speichern
  - Outcome-Vergleich nach 1h, 4h, 24h
  - Precision/Recall pro Model, Timeframe, Regime
  - Model Leaderboard
- [ ] Temperature-Strategie
  - Exploration (neue Strategien): temperature=0.7
  - Exploitation (Live-Trading): temperature=0.1
- [ ] Self-Coding AI Sandbox
  - Docker-basierte Isolation
  - Filesystem/Network-Beschraenkungen
  - AST-Validierung + Timeout
- [ ] Frontend: KI-Dashboard + Chat mit Outcome-Tracking

### Meilenstein
KI-Vorhersagen werden gemessen, Model Leaderboard zeigt welches Modell
am besten performt, Self-Coding AI laeuft in Sandbox.

---

## Sprint 6 (Woche 11-12): Polish & Launch

**Ziel:** Produktionsreife, Performance, Dokumentation

### Tasks
- [ ] Multi-Language Support migrieren (i18next → Next.js i18n)
- [ ] Prometheus Metrics aus der App exportieren
  - Request Latency, Error Rates
  - Trading Metriken (Orders/min, PnL)
  - AI Metriken (Response Time, Accuracy)
- [ ] Grafana Dashboards aufsetzen
- [ ] End-to-End Tests (Playwright)
- [ ] Performance-Optimierung
  - TimescaleDB Query-Tuning
  - Redis Caching-Strategie
  - Frontend Bundle Size
- [ ] Security Audit (final)
  - Penetration Testing
  - Dependency Vulnerability Scan
  - Secret Scanning
- [ ] Dokumentation
  - Strategy Guide (wie neue Strategien schreiben)
  - API Reference (OpenAPI/Swagger)
  - Deployment Guide
- [ ] Production Deployment
  - Docker Compose optimieren
  - Health Checks
  - Graceful Shutdown
  - Backup-Strategie

### Meilenstein
Produktions-Release. Alle Tests gruen, Monitoring laeuft,
Dokumentation vollstaendig.

---

## Erfolgskriterien

| # | Kriterium | Messung |
|---|-----------|---------|
| 1 | Backtesting liefert realistische Ergebnisse | Keine uebertriebenen Returns (>100% p.a. = Warnung) |
| 2 | Risk Management verhindert Totalverlust | Kill-Switch wird bei 20% Drawdown ausgeloest |
| 3 | KI-Vorhersagen werden gemessen | Precision/Recall sichtbar im Dashboard |
| 4 | Keine Mock-Daten | Alle Daten aus echten APIs |
| 5 | Zero Secrets im Code | Kein API-Key hardcoded |
| 6 | Tests laufen gruen | >80% Coverage Backend |
| 7 | Latenz < 500ms | Echtzeit-Daten innerhalb 500ms |
| 8 | Clean Strategy API | Neue Strategie in < 50 Zeilen Code |
| 9 | CI/CD Pipeline gruen | Jeder PR wird automatisch getestet |
| 10 | Monitoring funktioniert | Alerts bei Anomalien |

---

## Risiken und Mitigationen

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| TimescaleDB Migration bricht Daten | Mittel | Hoch | Parallelbetrieb, Daten-Validation |
| Glassnode API zu teuer | Hoch | Mittel | CryptoQuant als Alternative, Free Tier nutzen |
| Next.js Migration dauert zu lange | Mittel | Mittel | Schrittweise Migration, nicht Big-Bang |
| Backtesting zeigt Overfitting | Hoch | Hoch | Walk-Forward Analyse, Out-of-Sample Tests |
| LLM-API Kosten steigen | Mittel | Mittel | Cost Tracking, lokale Modelle als Fallback |
