#!/bin/bash

# 🚀 Lunara Analyze AI - Quick Installation Script
# Run this script on your Ubuntu 22.04 server as root

set -e

echo "🚀 Lunara Analyze AI - Quick Installation"
echo "========================================"
echo "Server: $(hostname -I | awk '{print $1}')"
echo "Date: $(date)"
echo

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root"
   echo "Usage: sudo ./quick-install.sh"
   exit 1
fi

print_status "Starting system preparation..."

# Update system
print_status "Updating system packages..."
apt update && apt upgrade -y
apt install -y curl wget git unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release

# Install Docker
print_status "Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable docker
    systemctl start docker
    print_success "Docker installed"
else
    print_success "Docker already installed"
fi

# Install Docker Compose
print_status "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    print_success "Docker Compose installed"
fi

# Setup firewall
print_status "Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 3000/tcp
ufw allow 8001/tcp
ufw --force enable
print_success "Firewall configured"

# Create app directory
print_status "Creating application directory..."
mkdir -p /opt/lunara-ai
cd /opt/lunara-ai

# Create SSL directory and generate self-signed certificate
print_status "Setting up SSL..."
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/privkey.pem \
    -out ssl/fullchain.pem \
    -subj "/C=DE/ST=Germany/L=City/O=LunaraAI/CN=217.154.71.31"

print_success "✅ Server preparation completed!"
print_warning "Next steps:"
echo "1. Extract lunara-ai-complete-package.tar.gz to /opt/lunara-ai/"
echo "2. Run: docker-compose up -d"
echo "3. Access: https://217.154.71.31"

echo -e "\n🎉 Quick installation completed!"
echo "Your server is ready for Lunara Analyze AI deployment!"