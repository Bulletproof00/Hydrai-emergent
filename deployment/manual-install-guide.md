# 🚀 Lunara Analyze AI - Manuelle Installation

Da die automatische SSH-Verbindung nicht funktioniert, folgen Sie dieser Schritt-für-Schritt-Anleitung:

## 📋 Schritt 1: Dateien auf den Server übertragen

### Option A: SCP (Empfohlen)
```bash
# Auf Ihrem lokalen Computer:
scp -r /pfad/zu/deployment/ root@217.154.71.31:/tmp/
```

### Option B: Manueller Upload
1. Laden Sie alle Dateien aus dem `/app/deployment/` Verzeichnis herunter
2. Übertragen Sie sie per SFTP/SCP auf Ihren Server nach `/tmp/deployment/`

## 📋 Schritt 2: SSH-Verbindung zum Server
```bash
ssh root@217.154.71.31
# Passwort: Lunara2601
```

## 📋 Schritt 3: Installation ausführen

Nachdem Sie sich auf dem Server eingeloggt haben:

```bash
# Ins temp Verzeichnis wechseln
cd /tmp

# Falls Dateien als Archiv übertragen:
# tar -xzf lunara-ai-complete.tar.gz

# Installations-Script ausführbar machen
chmod +x deployment/install.sh

# Server-Installation starten
./deployment/install.sh
```

## 📋 Schritt 4: Anwendung einrichten

Nach der System-Installation:

```bash
# Anwendungsverzeichnis erstellen und wechseln
mkdir -p /opt/lunara-ai
cd /opt/lunara-ai

# Deployment-Dateien kopieren
cp -r /tmp/deployment/* .

# Anwendungsdateien aus dem Archiv extrahieren (falls vorhanden)
if [ -f /tmp/lunara-ai-complete.tar.gz ]; then
    tar -xzf /tmp/lunara-ai-complete.tar.gz --strip-components=1
fi

# Umgebungsvariablen einrichten
cp deployment/.env .env

# Docker Compose Konfiguration kopieren
cp deployment/docker-compose.yml .

# Nginx Konfiguration kopieren
cp -r deployment/nginx .
cp -r deployment/monitoring .

# Backend Umgebung einrichten
cp .env backend/.env

# Frontend Umgebung für Produktion einrichten
echo "REACT_APP_BACKEND_URL=https://217.154.71.31" > frontend/.env
```

## 📋 Schritt 5: Services starten

```bash
# Docker Images pullen und bauen
docker-compose pull
docker-compose build --no-cache

# Services starten
docker-compose up -d

# Warten auf Service-Start (30 Sekunden)
sleep 30

# Service-Status prüfen
docker-compose ps
```

## 📋 Schritt 6: Installation verifizieren

```bash
# Health Check ausführen
./health_check.sh

# API testen
curl -f http://localhost:8001/api/health

# Frontend testen
curl -f http://localhost:3000/health
```

## 📋 Schritt 7: System-Service aktivieren

```bash
# System-Service aktivieren
systemctl daemon-reload
systemctl enable lunara-ai
systemctl start lunara-ai

# Status prüfen
systemctl status lunara-ai
```

## 🌐 Zugriff auf die Anwendung

Nach erfolgreicher Installation:

- **Web-App**: https://217.154.71.31
- **API**: https://217.154.71.31/api/health
- **Monitoring**: http://217.154.71.31:3001 (admin/Lunara2601)

### Demo-Login:
- **Email**: demo@example.com
- **Passwort**: demo123

## 🔧 Fehlerbehebung

### Services prüfen:
```bash
docker-compose logs -f
```

### Service neu starten:
```bash
docker-compose restart
```

### Speicher freigeben:
```bash
docker system prune -a
```

### Firewall prüfen:
```bash
ufw status
```

## 🔒 SSL-Zertifikat einrichten (Optional)

Für produktive Nutzung Let's Encrypt einrichten:

```bash
# Let's Encrypt Zertifikat erstellen
certbot certonly --standalone -d 217.154.71.31

# Zertifikate kopieren
cp /etc/letsencrypt/live/217.154.71.31/fullchain.pem ssl/
cp /etc/letsencrypt/live/217.154.71.31/privkey.pem ssl/

# Nginx neu starten
docker-compose restart nginx
```

---

## ✅ Installation abgeschlossen!

Ihre **Lunara Analyze AI** Trading-Plattform ist jetzt live! 🎉

Bei Problemen schauen Sie in die Logs: `docker-compose logs -f`