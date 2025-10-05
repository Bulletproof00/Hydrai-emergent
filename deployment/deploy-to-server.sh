#!/bin/bash

# Lunara Analyze AI - Automated Deployment Script
# Deploys the complete application to the production server

set -e

# Configuration
SERVER_IP="217.154.71.31"
SERVER_USER="root"
SSH_KEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMTTGhgpCFBn0qiuGANvIY9g7yaT0QMO/fhvSHgUJHFN fatih@hydra-server"
APP_DIR="/opt/lunara-ai"

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

echo "🚀 Lunara Analyze AI - Deployment"
echo "=================================="
print_status "Target Server: $SERVER_IP"
print_status "Deployment Directory: $APP_DIR"

# Step 1: Create deployment package
print_status "Creating deployment package..."
cd /app
rm -f /tmp/lunara-ai-complete.tar.gz

tar --exclude="backend/__pycache__" \
    --exclude="backend/.pytest_cache" \
    --exclude="frontend/node_modules" \
    --exclude="frontend/build" \
    --exclude="*.log" \
    --exclude="*.tmp" \
    -czf /tmp/lunara-ai-complete.tar.gz \
    backend frontend deployment

print_success "Deployment package created: /tmp/lunara-ai-complete.tar.gz"

# Step 2: Test server connectivity
print_status "Testing server connectivity..."
if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no root@$SERVER_IP "echo 'Server reachable'" >/dev/null 2>&1; then
    print_success "Server connection successful"
else
    print_error "Cannot connect to server. Please check:"
    echo "1. SSH key is loaded: ssh-add ~/.ssh/your_key"
    echo "2. Server is accessible: ping $SERVER_IP"
    echo "3. SSH port 22 is open"
    exit 1
fi

# Step 3: Upload installation script
print_status "Uploading installation script..."
scp -o StrictHostKeyChecking=no deployment/install.sh root@$SERVER_IP:/tmp/
ssh root@$SERVER_IP "chmod +x /tmp/install.sh"

# Step 4: Run server preparation
print_status "Running server preparation..."
ssh root@$SERVER_IP "bash /tmp/install.sh"

# Step 5: Upload application files
print_status "Uploading application files..."
scp -o StrictHostKeyChecking=no /tmp/lunara-ai-complete.tar.gz root@$SERVER_IP:/tmp/

# Step 6: Extract and setup application
print_status "Setting up application on server..."
ssh root@$SERVER_IP << 'ENDSSH'
    cd /opt/lunara-ai
    
    # Extract application files
    tar -xzf /tmp/lunara-ai-complete.tar.gz --strip-components=1
    
    # Set proper permissions
    chown -R root:root /opt/lunara-ai
    chmod +x /opt/lunara-ai/deployment/*.sh
    
    # Copy environment file
    cp deployment/.env .env
    
    # Copy Docker configurations
    cp deployment/docker-compose.yml .
    cp -r deployment/nginx .
    cp -r deployment/monitoring .
    
    # Update backend environment
    cp deployment/.env backend/.env
    
    # Update frontend environment for production
    echo "REACT_APP_BACKEND_URL=https://217.154.71.31" > frontend/.env
    
    echo "Application files setup complete"
ENDSSH

# Step 7: Build and start services
print_status "Building and starting Docker services..."
ssh root@$SERVER_IP << 'ENDSSH'
    cd /opt/lunara-ai
    
    # Pull base images
    docker-compose pull
    
    # Build custom images
    docker-compose build --no-cache
    
    # Start services
    docker-compose up -d
    
    # Wait for services to start
    echo "Waiting for services to start..."
    sleep 30
    
    # Check service status
    docker-compose ps
ENDSSH

# Step 8: Verify deployment
print_status "Verifying deployment..."
sleep 10

# Test backend API
if curl -sf https://$SERVER_IP/api/health >/dev/null 2>&1 || curl -sf http://$SERVER_IP:8001/api/health >/dev/null 2>&1; then
    print_success "✅ Backend API is responding"
else
    print_warning "⚠️  Backend API check failed (may need SSL setup)"
fi

# Test frontend
if curl -sf https://$SERVER_IP >/dev/null 2>&1 || curl -sf http://$SERVER_IP:3000 >/dev/null 2>&1; then
    print_success "✅ Frontend is accessible"
else
    print_warning "⚠️  Frontend check failed"
fi

# Step 9: Setup system service
print_status "Setting up system service..."
ssh root@$SERVER_IP << 'ENDSSH'
    systemctl daemon-reload
    systemctl enable lunara-ai
    systemctl start lunara-ai
    echo "System service configured"
ENDSSH

# Step 10: Display final information
print_success "🎉 Deployment completed successfully!"

echo ""
echo "=== 📊 DEPLOYMENT SUMMARY ==="
echo "• Server IP: $SERVER_IP"
echo "• Application URL: https://$SERVER_IP"
echo "• API URL: https://$SERVER_IP/api/health"
echo "• Monitoring: http://$SERVER_IP:3001 (admin/Lunara2601)"
echo ""

print_warning "🔧 POST-DEPLOYMENT TASKS:"
echo "1. Replace self-signed SSL certificate with Let's Encrypt:"
echo "   ssh root@$SERVER_IP"
echo "   certbot certonly --standalone -d $SERVER_IP"
echo ""
echo "2. Test the application:"
echo "   • Open: https://$SERVER_IP"
echo "   • Login: demo@example.com / demo123"
echo "   • Check all features work"
echo ""
echo "3. Monitor logs:"
echo "   ssh root@$SERVER_IP 'cd /opt/lunara-ai && docker-compose logs -f'"
echo ""

print_success "✅ Lunara Analyze AI is now live at: https://$SERVER_IP"

# Cleanup
rm -f /tmp/lunara-ai-complete.tar.gz

echo ""
print_status "Deployment script completed. Your trading platform is ready! 🚀📈"