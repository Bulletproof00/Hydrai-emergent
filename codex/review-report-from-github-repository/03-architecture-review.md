# 03 - Architecture Review

## Aktueller Zustand (v1)

### Architektur-Diagramm (Ist-Zustand)

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (React 19 + CRA)         │
│  App.js (36 KB) → alles in einer Datei              │
│  70+ Komponenten, hooks, Shadcn/ui                   │
│  i18next (5 Sprachen)                                │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP/WebSocket
┌──────────────────────▼──────────────────────────────┐
│              Backend (FastAPI)                        │
│  server.py (124 KB) → MONOLITH                       │
│  21 Module in /modules/                              │
│  Globale Variablen als State                         │
└───────┬────────────┬─────────────┬──────────────────┘
        │            │             │
   ┌────▼────┐  ┌───▼────┐  ┌────▼─────┐
   │ MongoDB │  │ Redis  │  │ Binance  │
   │ (Motor) │  │ Cache  │  │ CoinGecko│
   └─────────┘  └────────┘  │ Synthetic│
                             └──────────┘
```

### Problem 1: Monolithischer Server

**Datei:** `backend/server.py` - 124 KB, ~3.500 Zeilen

Alles in einer Datei:
- API-Routen (Trading, Market Data, AI, Auth, Analysis)
- Business Logic (Order-Ausfuehrung, Analyse, Chart-Generierung)
- Datenbank-Zugriffe (MongoDB Queries direkt in Routen)
- WebSocket-Handler
- Middleware-Konfiguration
- Globale Variablen als State-Management

**Impact:**
- Schwer testbar (alles gekoppelt)
- Merge-Konflikte bei Team-Entwicklung
- Keine Isolation von Fehlerdomaenen
- Schwer zu debuggen

### Problem 2: Globale Variablen

```python
# backend/server.py - Module-Level State
redis_client = None       # Zeile 67
enhanced_streamer = None  # Zeile 70
smart_money = None        # Zeile 73
enhanced_smart_money = None  # Zeile 74
paper_trading = None      # Zeile 77
ai_trading = None         # Zeile 80
```

**Impact:**
- Kein Lifecycle-Management
- Race Conditions bei parallelen Requests
- Nicht testbar (kein Mocking moeglich)
- Kein Dependency Injection

### Problem 3: Fehlende Schichten-Trennung

Aktuell: Route → direkt MongoDB → Response

```
Soll:  Route → Service → Repository → Database
```

Es gibt keine Service-Schicht. Business Logic ist direkt in den API-Routen.

### Problem 4: MongoDB fuer Zeitreihen

MongoDB ist keine optimale Wahl fuer OHLCV-Zeitreihen-Daten:
- Keine nativen Time-Series-Aggregationen
- Kein Continuous Aggregation (wie TimescaleDB)
- Hoher Speicherverbrauch fuer Zeitreihen
- Keine optimierten Range-Queries ueber Zeitfenster

---

## Ziel-Architektur (v2)

### Architektur-Diagramm (Soll-Zustand)

```
┌──────────────────────────────────────────────────────┐
│              Frontend (Next.js 15 + TypeScript)       │
│  App Router, SSR, TradingView Lightweight Charts      │
│  Zustand (State), Tanstack Query (Server State)       │
│  WebSocket mit Auto-Reconnect                         │
└───────────────────────┬──────────────────────────────┘
                        │ HTTP/WebSocket
┌───────────────────────▼──────────────────────────────┐
│                  API Gateway (Nginx)                   │
│  Rate Limiting, SSL Termination, Load Balancing        │
└───┬──────────┬──────────┬──────────┬─────────────────┘
    │          │          │          │
┌───▼───┐ ┌───▼───┐ ┌───▼───┐ ┌───▼───┐
│Trading│ │Market │ │  AI   │ │ Auth  │
│Service│ │ Data  │ │Service│ │Service│
│       │ │Service│ │       │ │       │
└───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘
    │         │         │         │
┌───▼─────────▼─────────▼─────────▼────┐
│        Service Layer                   │
│  Risk Manager, Strategy Registry,      │
│  Backtesting Engine, Data Pipeline     │
└───┬──────────────┬───────────────────┘
    │              │
┌───▼──────┐  ┌───▼──────┐  ┌──────────┐
│PostgreSQL│  │  Redis 7  │  │ Binance  │
│+Timescale│  │  Cache    │  │ FRED     │
│  DB      │  │  Sessions │  │ Glassnode│
└──────────┘  └──────────┘  │ CoinGecko│
                             └──────────┘
```

---

## Tech-Stack Migration

### Backend

| Aspekt | v1 (Aktuell) | v2 (Geplant) | Begruendung |
|--------|-------------|-------------|-------------|
| **Struktur** | Monolith (`server.py` 124 KB) | Modulare FastAPI Router | Testbarkeit, Wartbarkeit |
| **Datenbank** | MongoDB | PostgreSQL + TimescaleDB | Zeitreihen-optimiert |
| **Cache** | Redis (basic) | Redis 7 (Streams, Pub/Sub) | Echtzeit-Events |
| **Deps** | `pip + requirements.txt` | Poetry + `pyproject.toml` | Lockfiles, reproduzierbar |
| **AI** | Nur Gemini (hardcoded) | LiteLLM Multi-Model Router | Fallback, Kostenoptimierung |
| **Config** | `os.environ.get()` mit Fallbacks | Pydantic Settings (kein Fallback fuer Secrets) | Sicherheit |
| **Logging** | `print()` / `logging.info()` | Strukturiertes JSON-Logging | Maschinelle Auswertung |
| **Tests** | 25 Dateien, nicht in CI | pytest + CI/CD | Automatisierte Qualitaet |

### Frontend

| Aspekt | v1 (Aktuell) | v2 (Geplant) | Begruendung |
|--------|-------------|-------------|-------------|
| **Framework** | React 19 + CRA | Next.js 15 + TypeScript | SSR, App Router, Performance |
| **Charts** | Canvas-Eigenimplementierung | TradingView Lightweight Charts | Professionell, weniger Bugs |
| **State** | React State | Zustand | Leichtgewichtig, TypeScript-nativ |
| **Server State** | Axios + manuelles Caching | Tanstack Query | Caching, Revalidation |
| **Styling** | Tailwind + Shadcn/ui | Tailwind + Shadcn/ui (beibehalten) | Funktioniert gut |
| **Package Mgr** | npm/yarn | pnpm | Schneller, effizienter |

### Infrastruktur

| Aspekt | v1 (Aktuell) | v2 (Geplant) | Begruendung |
|--------|-------------|-------------|-------------|
| **CI/CD** | Nicht vorhanden | GitHub Actions | Lint, Test, Build, Deploy |
| **Monitoring** | Docker-Level | Prometheus + Grafana (App-Metriken) | Proaktives Monitoring |
| **Secret Mgmt** | `.env` mit Fallbacks | `.env` ohne Fallbacks + Secret Scanning | Sicherheit |
| **Deployment** | Supervisor + Nginx | Docker Compose + Nginx | Reproduzierbar |

---

## Vorgeschlagene Backend-Struktur (v2)

```
chainalyze-v2/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI Entry Point (schlank)
│   │   ├── config.py                  # Pydantic Settings
│   │   ├── dependencies.py            # DI Container
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
│   │   │   │   ├── order_manager.py
│   │   │   │   ├── position_manager.py
│   │   │   │   ├── risk_manager.py    # NEU
│   │   │   │   └── fee_model.py       # NEU
│   │   │   │
│   │   │   ├── strategy/
│   │   │   │   ├── base.py            # Abstrakte Strategy-Klasse
│   │   │   │   ├── registry.py
│   │   │   │   └── builtin/
│   │   │   │       ├── rsi_divergence.py
│   │   │   │       ├── smart_money_flow.py
│   │   │   │       └── correlation_regime.py
│   │   │   │
│   │   │   ├── backtesting/           # NEU
│   │   │   │   ├── engine.py
│   │   │   │   ├── simulator.py
│   │   │   │   ├── metrics.py
│   │   │   │   ├── walk_forward.py
│   │   │   │   └── optimizer.py       # Optuna
│   │   │   │
│   │   │   └── ai/
│   │   │       ├── llm_router.py      # Multi-Model (LiteLLM)
│   │   │       ├── trading_analyst.py
│   │   │       ├── feedback_loop.py   # NEU
│   │   │       ├── strategy_generator.py
│   │   │       └── sandbox.py         # Sichere Code-Ausfuehrung
│   │   │
│   │   ├── data/                      # Daten-Layer
│   │   │   ├── providers/
│   │   │   │   ├── base.py            # Abstract Provider
│   │   │   │   ├── binance.py
│   │   │   │   ├── coingecko.py
│   │   │   │   ├── fred.py
│   │   │   │   ├── glassnode.py
│   │   │   │   └── news.py
│   │   │   │
│   │   │   ├── pipeline.py            # Data Pipeline + Circuit Breaker
│   │   │   ├── cache.py               # Redis Cache
│   │   │   ├── storage.py             # DB Persistence
│   │   │   └── models.py              # Pydantic Models
│   │   │
│   │   ├── analysis/
│   │   │   ├── technical.py
│   │   │   ├── smart_money.py
│   │   │   ├── correlation.py
│   │   │   ├── sentiment.py
│   │   │   └── on_chain.py
│   │   │
│   │   └── infrastructure/
│   │       ├── security.py
│   │       ├── circuit_breaker.py
│   │       ├── logging.py
│   │       └── monitoring.py
│   │
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   │
│   └── pyproject.toml                 # Poetry
```

---

## Migrations-Strategie: Monolith → Modular

### Phase 1: Extrahierung (ohne Funktionsverlust)
1. API-Routen in separate Router-Dateien verschieben
2. Globale Variablen → Dependency Injection (`FastAPI.Depends`)
3. Business Logic in Service-Klassen extrahieren
4. Bestehende Tests anpassen

### Phase 2: Datenbank-Migration
1. TimescaleDB neben MongoDB aufsetzen
2. OHLCV-Daten in TimescaleDB migrieren
3. Continuous Aggregates fuer Zeitfenster-Abfragen
4. MongoDB fuer Sessions/User-Daten beibehalten oder ebenfalls migrieren

### Phase 3: Frontend-Migration
1. Next.js-Projekt neben CRA aufsetzen
2. Komponenten schrittweise migrieren
3. TradingView Charts als Ersatz fuer Canvas-Implementation
4. TypeScript fuer neue Komponenten

### Phase 4: Infrastruktur
1. CI/CD Pipeline aufsetzen
2. Secret Management einrichten
3. Monitoring (App-Level Metriken)
4. Staging-Environment
