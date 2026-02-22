# 06 - Action Items (Priorisiert)

## Prioritaets-Matrix

```
                    HOCH IMPACT
                        │
         Sofort-Fix     │   Kernfeatures
       (Quick Wins)     │   (Strategisch)
                        │
  NIEDRIG ──────────────┼────────────── HOCH
  AUFWAND               │              AUFWAND
                        │
         Nice-to-Have   │   Langfristig
        (Spaeter)       │   (v2 Neubau)
                        │
                   NIEDRIG IMPACT
```

---

## Sofort (Heute/Morgen) - Quick Wins

| # | Action | Datei | Aufwand | Impact |
|---|--------|-------|---------|--------|
| 1 | **API-Key aus Code entfernen** | `backend/modules/ai_trading_engine.py:77` | 5 min | KRITISCH |
| 2 | **Gemini API-Key in Google Cloud rotieren** | Google AI Studio | 5 min | KRITISCH |
| 3 | **JWT-Secret Fallback entfernen** | `backend/server.py:54` | 5 min | HOCH |
| 4 | **GitHub Secret Scanning aktivieren** | Repo Settings → Security | 2 min | HOCH |
| 5 | **Duplikate in requirements.txt entfernen** | `backend/requirements.txt:145-147` | 5 min | NIEDRIG |

### Detail: Action 1 - API-Key entfernen

**Vorher:**
```python
self.api_key = os.environ.get('GEMINI_API_KEY', "AIzaSyAd8SqGySsek3Jud4HI6IkMArJtSnBcIUk")
```

**Nachher:**
```python
self.api_key = os.environ.get('GEMINI_API_KEY')
if not self.api_key:
    raise RuntimeError("GEMINI_API_KEY environment variable is required. Set it in .env")
```

### Detail: Action 3 - JWT-Secret haerten

**Vorher:**
```python
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "hydra-secret-key-2024")
```

**Nachher:**
```python
SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is required. Generate with: python3 -c \"import secrets; print(secrets.token_urlsafe(64))\"")
```

---

## Kurzfristig (Diese Woche) - Stabilisierung

| # | Action | Aufwand | Impact |
|---|--------|---------|--------|
| 6 | **Self-Coding AI AST-Validierung erweitern** | 4h | HOCH |
| 7 | **Hardcodierte Base Prices dynamisch machen** (`enhanced_smart_money.py`) | 2h | MITTEL |
| 8 | **Rate Limiting hinzufuegen** (slowapi) | 2h | MITTEL |
| 9 | **Circuit-Breaker fuer Data-Provider** (pybreaker) | 4h | MITTEL |
| 10 | **Strukturiertes JSON-Logging** | 3h | MITTEL |

---

## Mittelfristig (Naechste 2-4 Wochen) - Architektur

| # | Action | Aufwand | Impact |
|---|--------|---------|--------|
| 11 | **server.py in Router-Module aufteilen** | 2-3 Tage | HOCH |
| 12 | **Globale Variablen → Dependency Injection** | 1-2 Tage | HOCH |
| 13 | **CI/CD Pipeline (GitHub Actions)** | 1 Tag | HOCH |
| 14 | **Risk Manager implementieren** | 3-4 Tage | HOCH |
| 15 | **Echte News-API anbinden** (CryptoPanic, RSS) | 2 Tage | MITTEL |
| 16 | **FRED API vollstaendig nutzen** | 1 Tag | MITTEL |
| 17 | **LiteLLM Multi-Model Router aktivieren** | 1 Tag | MITTEL |

---

## Langfristig (v2, 8-12 Wochen) - Neubau

| # | Action | Sprint | Aufwand | Impact |
|---|--------|--------|---------|--------|
| 18 | **PostgreSQL + TimescaleDB Migration** | Sprint 1 | 1 Woche | HOCH |
| 19 | **Backtesting-Engine** | Sprint 3 | 2 Wochen | KRITISCH |
| 20 | **KI-Feedback-Schleife** | Sprint 5 | 1 Woche | HOCH |
| 21 | **Next.js Frontend Migration** | Sprint 1-6 | 4 Wochen | MITTEL |
| 22 | **Korrelation + Regime-Erkennung (HMM)** | Sprint 4 | 1 Woche | MITTEL |
| 23 | **On-Chain Daten (Glassnode/CryptoQuant)** | Sprint 4 | 1 Woche | MITTEL |
| 24 | **Self-Coding AI Sandbox (Docker)** | Sprint 5 | 3 Tage | HOCH |
| 25 | **Prometheus + Grafana Monitoring** | Sprint 6 | 3 Tage | MITTEL |

---

## Abhaengigkeiten

```
Action 1-5 (Security) ─────→ keine Abhaengigkeiten, sofort moeglich
Action 11-12 (Architektur) ─→ Basis fuer alles Weitere
Action 13 (CI/CD) ──────────→ nach Action 11-12
Action 14 (Risk Manager) ──→ nach Action 11-12
Action 18 (TimescaleDB) ───→ Basis fuer Backtesting
Action 19 (Backtesting) ───→ nach Action 14 + 18
Action 20 (Feedback Loop) ─→ nach Action 17 (LiteLLM)
Action 24 (Sandbox) ───────→ unabhaengig, kann parallel laufen
```

---

## Tracking

### Status-Legende
- ⬜ Offen
- 🔄 In Arbeit
- ✅ Erledigt
- ❌ Blockiert

### Aktueller Status (2026-02-13)

| # | Action | Status | Notizen |
|---|--------|--------|---------|
| 1 | API-Key entfernen | ⬜ | SOFORT - Sicherheitsrisiko |
| 2 | Key rotieren | ⬜ | SOFORT - Nach Action 1 |
| 3 | JWT-Secret haerten | ⬜ | SOFORT |
| 4 | Secret Scanning | ⬜ | SOFORT |
| 5 | requirements.txt bereinigen | ⬜ | Quick Win |
| 6 | AST-Validierung | ⬜ | Diese Woche |
| 7-25 | Siehe oben | ⬜ | Geplant |
