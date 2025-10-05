# 🚀 Lunara Analyze AI - Server Installation Guide

## 📋 Übersicht

Diese Anleitung führt Sie durch die komplette Installation von **Lunara Analyze AI** auf Ihrem Ubuntu 22.04 Server mit Docker Compose.

### 🖥️ Server-Spezifikationen
- **Betriebssystem**: Ubuntu 22.04 LTS
- **CPU**: 2 Cores
- **RAM**: 4GB
- **Speicher**: 120GB
- **IP-Adresse**: 217.154.71.31

## 🔧 Installation

### Schritt 1: Server-Vorbereitung
```bash
# Als root-Benutzer einloggen
ssh root@217.154.71.31

# Installations-Script ausführbar machen
chmod +x install.sh

# Installation starten
./install.sh
```

### Schritt 2: Anwendung deployen
```bash
# Ins Anwendungsverzeichnis wechseln
cd /opt/lunara-ai

# Anwendungsdateien übertragen (scp oder git)
# Alternativ: tar -xzf lunara-ai-complete.tar.gz

# Services starten
docker-compose up -d
```

### Schritt 3: SSL-Zertifikat einrichten (Optional)
```bash
# Let's Encrypt Zertifikat erstellen
certbot certonly --standalone -d 217.154.71.31

# Zertifikate nach /opt/lunara-ai/ssl/ kopieren
cp /etc/letsencrypt/live/217.154.71.31/fullchain.pem ssl/
cp /etc/letsencrypt/live/217.154.71.31/privkey.pem ssl/

# Services neu starten
docker-compose restart nginx
```

## 📊 Services & Ports

| Service | Port | Beschreibung |
|---------|------|--------------|
| Frontend | 3000 | React Web App |
| Backend API | 8001 | FastAPI Server |
| MongoDB | 27017 | Datenbank (intern) |
| Redis | 6379 | Cache (intern) |
| Nginx | 80/443 | Reverse Proxy |
| Grafana | 3001 | Monitoring Dashboard |
| Prometheus | 9090 | Metriken |

## 🔍 Überwachung & Wartung

### Health Check
```bash
# System-Status prüfen
./health_check.sh

# Services anzeigen
docker-compose ps

# Logs anzeigen
docker-compose logs -f
```

### Backup & Restore
```bash
# Manuelles Backup
./backup.sh

# Backup wiederherstellen
tar -xzf backups/app_data_YYYYMMDD_HHMMSS.tar.gz -C /
```

### Service-Management
```bash
# Services starten
systemctl start lunara-ai

# Services stoppen
systemctl stop lunara-ai

# Status prüfen
systemctl status lunara-ai

# Auto-Start aktivieren
systemctl enable lunara-ai
```

## 🌐 Zugriff

### Web-Interface
- **URL**: https://217.154.71.31
- **Demo-Login**: 
  - Email: demo@example.com
  - Passwort: demo123

### Monitoring
- **Grafana**: http://217.154.71.31:3001
  - Username: admin
  - Passwort: Lunara2601

## 🛡️ Sicherheit

### Firewall-Regeln
```bash
# Status prüfen
ufw status

# Nur notwendige Ports geöffnet:
# 22 (SSH), 80 (HTTP), 443 (HTTPS)
```

### SSL/TLS
- **Selbst-signiert** (Initial): ⚠️ Browser-Warnung
- **Let's Encrypt** (Empfohlen): ✅ Vertrauenswürdig

## 📁 Verzeichnis-Struktur

```
/opt/lunara-ai/
├── docker-compose.yml     # Haupt-Konfiguration
├── .env                   # Umgebungsvariablen
├── backend/              # Backend-Code
├── frontend/             # Frontend-Code
├── nginx/                # Nginx-Konfiguration
├── ssl/                  # SSL-Zertifikate
├── logs/                 # Anwendungslogs
├── backups/              # Automatische Backups
└── monitoring/           # Prometheus-Konfiguration
```

## 🚨 Fehlerbehebung

### Häufige Probleme

1. **Services starten nicht**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

2. **Speicher-Probleme**
   ```bash
   docker system prune -a
   ```

3. **Port-Konflikte**
   ```bash
   netstat -tulpn | grep :PORT
   ```

4. **SSL-Probleme**
   ```bash
   # Selbst-signiertes Zertifikat erneuern
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout ssl/privkey.pem -out ssl/fullchain.pem \
     -subj "/CN=217.154.71.31"
   ```

## 📞 Support

### Log-Dateien
- **Docker Compose**: `docker-compose logs`
- **Nginx**: `/opt/lunara-ai/logs/nginx/`
- **System**: `/var/log/syslog`
- **Backup**: `/var/log/lunara-backup.log`

### Performance-Monitoring
```bash
# Ressourcen-Nutzung
htop

# Docker-Stats
docker stats

# Disk-Nutzung
df -h
```

---

## 🎉 Nach der Installation

Ihre **Lunara Analyze AI** Installation ist jetzt bereit!

1. ✅ **Web-App**: https://217.154.71.31
2. ✅ **API**: https://217.154.71.31/api/health
3. ✅ **Monitoring**: http://217.154.71.31:3001
4. ✅ **Automatische Backups**: Täglich um 02:00 Uhr
5. ✅ **SSL-verschlüsselt**: Sichere Verbindung

**Viel Spaß mit Ihrer Trading-Plattform!** 🚀📈