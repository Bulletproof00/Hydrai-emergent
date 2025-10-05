#!/bin/bash

# Lunara Analyze AI - Complete Server Installation Script
# For Ubuntu 22.04 with Docker Compose

set -e  # Exit on any error

echo "🚀 Starting Lunara Analyze AI Installation..."
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

print_status "System: $(lsb_release -d | cut -f2)"
print_status "Architecture: $(uname -m)"
print_status "Memory: $(free -h | awk 'NR==2{print $2}')"
print_status "Disk Space: $(df -h / | awk 'NR==2{print $4}' | head -1) available"

# Step 1: Update System
print_status "Updating system packages..."
apt update && apt upgrade -y
apt install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release

# Step 2: Install Docker
print_status "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable docker
    systemctl start docker
    print_success "Docker installed successfully"
else
    print_success "Docker already installed"
fi

# Step 3: Install Docker Compose (standalone)
print_status "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    print_success "Docker Compose installed successfully"
else
    print_success "Docker Compose already installed"
fi

# Step 4: Setup firewall
print_status "Configuring UFW firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 3000/tcp  # Frontend
ufw allow 8001/tcp  # Backend API
ufw --force enable
print_success "Firewall configured"

# Step 5: Create application directory
print_status "Creating application directory..."
mkdir -p /opt/lunara-ai
cd /opt/lunara-ai

# Step 6: Create necessary directories
print_status "Creating directory structure..."
mkdir -p {ssl,logs,backups,data/mongodb,data/redis,monitoring}
chown -R root:root /opt/lunara-ai
chmod -R 755 /opt/lunara-ai

# Step 7: Generate SSL certificate (Let's Encrypt)
print_status "Setting up SSL certificate..."
apt install -y certbot

# Create temporary self-signed certificate for initial setup
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/privkey.pem \
    -out ssl/fullchain.pem \
    -subj "/C=DE/ST=Germany/L=City/O=LunaraAI/CN=217.154.71.31"
print_warning "Self-signed certificate created. Replace with Let's Encrypt after installation."

# Step 8: Create monitoring configuration
print_status "Setting up monitoring..."
cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'lunara-backend'
    static_configs:
      - targets: ['backend:8001']
  
  - job_name: 'lunara-frontend'
    static_configs:
      - targets: ['frontend:3000']
  
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']
EOF

# Step 9: Create systemd service
print_status "Creating systemd service..."
cat > /etc/systemd/system/lunara-ai.service << EOF
[Unit]
Description=Lunara Analyze AI
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/lunara-ai
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable lunara-ai

# Step 10: Create backup script
print_status "Setting up backup system..."
cat > /opt/lunara-ai/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/lunara-ai/backups"
mkdir -p $BACKUP_DIR

echo "Creating backup: lunara_backup_$DATE"

# Backup MongoDB
docker exec lunara-mongodb mongodump --out /tmp/backup_$DATE
docker cp lunara-mongodb:/tmp/backup_$DATE $BACKUP_DIR/mongodb_$DATE

# Backup application data
tar -czf $BACKUP_DIR/app_data_$DATE.tar.gz /opt/lunara-ai/data

# Keep only last 7 backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "mongodb_*" -mtime +7 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_DIR"
EOF

chmod +x /opt/lunara-ai/backup.sh

# Setup daily backup cron
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/lunara-ai/backup.sh >> /var/log/lunara-backup.log 2>&1") | crontab -

# Step 11: Create health check script
cat > /opt/lunara-ai/health_check.sh << 'EOF'
#!/bin/bash
echo "=== Lunara Analyze AI Health Check ==="
echo "Date: $(date)"
echo

# Check Docker services
echo "Docker Services:"
docker-compose ps

echo -e "\n=== Service Health ==="
# Check MongoDB
if docker exec lunara-mongodb mongosh --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
    echo "✅ MongoDB: Healthy"
else
    echo "❌ MongoDB: Unhealthy"
fi

# Check Backend
if curl -sf http://localhost:8001/api/health >/dev/null 2>&1; then
    echo "✅ Backend API: Healthy"
else
    echo "❌ Backend API: Unhealthy"
fi

# Check Frontend
if curl -sf http://localhost:3000/health >/dev/null 2>&1; then
    echo "✅ Frontend: Healthy"
else
    echo "❌ Frontend: Unhealthy"
fi

echo -e "\n=== System Resources ==="
echo "Memory: $(free -h | awk 'NR==2{printf "%.1f%% used", $3/$2*100}')"
echo "Disk: $(df -h / | awk 'NR==2{print $5 " used"}')"
echo "Load: $(uptime | awk -F'load average:' '{print $2}')"
EOF

chmod +x /opt/lunara-ai/health_check.sh

print_success "✅ Lunara Analyze AI installation preparation completed!"
print_status "Next steps:"
echo "1. Upload your application files to /opt/lunara-ai/"
echo "2. Run 'docker-compose up -d' to start services"
echo "3. Access your app at: https://217.154.71.31"
echo "4. Monitor with: /opt/lunara-ai/health_check.sh"
echo "5. Logs: docker-compose logs -f"

print_warning "Don't forget to:"
echo "• Replace self-signed SSL with Let's Encrypt"
echo "• Update DNS records if using domain"
echo "• Configure regular backups"
echo "• Set up monitoring alerts"

echo -e "\n🎉 Installation script completed successfully!"