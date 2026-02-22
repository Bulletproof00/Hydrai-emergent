# 02 - Security Audit

## Severity-Klassifikation

| Level | Beschreibung |
|-------|-------------|
| **KRITISCH** | Sofortige Ausnutzung moeglich, Datenverlust/Kompromittierung |
| **HOCH** | Ausnutzbar mit geringem Aufwand, signifikantes Risiko |
| **MITTEL** | Ausnutzbar unter bestimmten Bedingungen |
| **NIEDRIG** | Theoretisches Risiko, geringer Impact |

---

## Finding 1: Hardcodierter API-Key (KRITISCH)

**Datei:** `backend/modules/ai_trading_engine.py:77`

```python
self.api_key = os.environ.get('GEMINI_API_KEY', "AIzaSyAd8SqGySsek3Jud4HI6IkMArJtSnBcIUk")
```

**Risiko:**
- API-Key ist auf GitHub oeffentlich sichtbar
- Jeder kann den Key missbrauchen (Kosten, Rate Limits)
- Google koennte den Key automatisch sperren (GitHub Secret Scanning)
- Potenzielle Rechtsverletztung bei Missbrauch

**Fix (Sofort):**
1. Key in Google Cloud Console rotieren: https://aistudio.google.com/app/apikey
2. Fallback-Wert entfernen:
```python
self.api_key = os.environ.get('GEMINI_API_KEY')
if not self.api_key:
    raise RuntimeError("GEMINI_API_KEY environment variable is required")
```
3. `.env.example` aktualisieren:
```
GEMINI_API_KEY=your_gemini_api_key_here
```
4. GitHub Secret Scanning aktivieren (Settings → Code security)
5. git-secrets oder gitleaks als Pre-Commit-Hook

---

## Finding 2: Schwaches JWT-Secret (HOCH)

**Datei:** `backend/server.py:54`

```python
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "hydra-secret-key-2024")
```

**Risiko:**
- Das Fallback-Secret `hydra-secret-key-2024` ist trivial erratbar
- Angreifer kann sich selbst gueltige JWT-Tokens erstellen
- Vollstaendige Authentifizierungs-Umgehung moeglich

**Fix:**
```python
SECRET_KEY = os.environ["JWT_SECRET_KEY"]  # Kein Fallback! App startet nicht ohne
```

Secret generieren:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

## Finding 3: Self-Coding AI - Remote Code Execution (HOCH)

**Datei:** `backend/modules/self_coding_ai.py`

**Risiko:**
- KI generiert Python-Code, der dynamisch geladen und ausgefuehrt wird
- Import-Allowlist existiert, kann aber umgangen werden
- Kein Filesystem-Schutz, kein Network-Schutz
- Potenzielle Remote Code Execution (RCE) ueber manipulierte Prompts

**Fix (Stufenplan):**

**Phase 1 - Haertung (kurzfristig):**
- AST-basierte Validierung vor Ausfuehrung erweitern
- Blockliste fuer gefaehrliche Module: `os`, `subprocess`, `shutil`, `socket`
- Maximale Code-Laenge begrenzen
- Timeout fuer Code-Ausfuehrung setzen (max. 30s)

**Phase 2 - Sandboxing (mittelfristig):**
- Code in separatem Docker-Container ausfuehren
- Oder: `nsjail` / `bubblewrap` fuer Prozess-Isolation
- Kein Filesystem-Zugriff ausser designierten Verzeichnissen
- Kein Netzwerk-Zugriff im Sandbox
- Memory-Limit (max. 256 MB)
- CPU-Limit (max. 1 Core)

**Phase 3 - Architektur (langfristig):**
- Plugin-System mit definierter API-Oberflaeche
- Plugins als separate Microservices
- gRPC-Kommunikation zwischen Plugin und Hauptsystem

---

## Finding 4: Fehlende Rate-Limiting Konfiguration (MITTEL)

**Datei:** `backend/server.py`

Die API hat grundlegendes CORS, aber kein explizites Rate Limiting pro Endpoint.

**Fix:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/chat")
@limiter.limit("30/minute")
async def chat(request: Request):
    ...
```

---

## Finding 5: Keine Input-Validierung bei Trading-Orders (MITTEL)

**Risiko:**
- Negative Leverage-Werte
- Position-Sizes ueber Kontoguthaben
- Ungueltige Symbol-Strings

**Fix:**
```python
from pydantic import BaseModel, Field, validator

class OrderRequest(BaseModel):
    symbol: str = Field(..., regex=r"^[A-Z]+/USDT$")
    side: Literal["buy", "sell"]
    amount: float = Field(..., gt=0, le=1000000)
    leverage: int = Field(..., ge=1, le=100)

    @validator("symbol")
    def validate_symbol(cls, v):
        allowed = {"BTC/USDT", "ETH/USDT", "SOL/USDT", ...}
        if v not in allowed:
            raise ValueError(f"Symbol {v} nicht unterstuetzt")
        return v
```

---

## Finding 6: MongoDB ohne Authentifizierung (NIEDRIG in Dev, KRITISCH in Prod)

**Datei:** `.env.example`
```
MONGO_URL=mongodb://localhost:27017/chainalyze_ai
```

Keine Authentifizierung konfiguriert. In Produktionsumgebung muss MongoDB mit
Benutzername/Passwort gesichert werden.

**Fix:**
```
MONGO_URL=mongodb://chainalyze_user:SECURE_PASSWORD@localhost:27017/chainalyze_ai?authSource=admin
```

---

## Security-Checkliste fuer v2

- [ ] Kein einziger API-Key/Secret im Source Code
- [ ] Alle Secrets ueber Environment-Variablen ohne Fallback-Werte
- [ ] JWT-Secret: min. 256-bit, kryptographisch zufaellig
- [ ] Rate Limiting auf allen oeffentlichen Endpoints
- [ ] Input-Validierung fuer alle Trading-Operationen
- [ ] Self-Coding AI in Sandbox ausfuehren
- [ ] MongoDB mit Authentifizierung
- [ ] HTTPS erzwingen (HSTS Header)
- [ ] Dependency Vulnerability Scanning (Dependabot/Snyk)
- [ ] GitHub Secret Scanning aktiviert
- [ ] Pre-Commit Hooks fuer Secret-Detection (gitleaks)
- [ ] Security Headers (CSP, X-Frame-Options, etc.)
- [ ] Audit-Logging fuer alle Trading-Operationen
