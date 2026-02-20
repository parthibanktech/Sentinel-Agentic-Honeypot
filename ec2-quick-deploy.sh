#!/bin/bash
# 🚀 EC2 Quick Deployment Script for Sentinel Honeypot
# Run this script on your EC2 instance after SSH connection

set -e  # Exit on any error

echo "🚀 Starting Sentinel Honeypot Deployment..."

# Step 1: Update system
echo "📦 Updating system packages..."
sudo yum update -y || sudo apt-get update -y

# Step 2: Install Docker
echo "🐳 Installing Docker..."
if command -v yum &> /dev/null; then
    # Amazon Linux
    sudo yum install docker -y
    sudo service docker start
    sudo usermod -a -G docker ec2-user
    newgrp docker
elif command -v apt-get &> /dev/null; then
    # Ubuntu
    sudo apt-get install -y docker.io
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -a -G docker ubuntu
    newgrp docker
fi

# Step 3: Install Git (if not present)
echo "📥 Installing Git..."
sudo yum install git -y || sudo apt-get install -y git

# Step 4: Clone repository
echo "📂 Cloning repository..."
cd ~
if [ -d "Sentinel-Agentic-Honeypot" ]; then
    echo "Repository already exists, pulling latest changes..."
    cd Sentinel-Agentic-Honeypot
    git pull
else
    git clone https://github.com/parthibanktech/Sentinel-Agentic-Honeypot.git
    cd Sentinel-Agentic-Honeypot
fi

# Step 5: Create environment file
echo "🔐 Setting up environment variables..."
read -p "Enter your OpenAI API Key: " OPENAI_KEY
read -p "Enter your Honeypot API Key (default: sentinel-master-key): " HONEYPOT_KEY
HONEYPOT_KEY=${HONEYPOT_KEY:-sentinel-master-key}

cat > backend/.env << EOF
OPENAI_API_KEY=${OPENAI_KEY}
HONEYPOT_API_KEY=${HONEYPOT_KEY}
PORT=8000
EOF

echo "✅ Environment file created!"

# Step 6: Build and Run with Docker Compose
echo "🏗️ Building and Starting with Docker Compose..."
docker compose up -d --build

# Step 7: Wait for container to start
echo "⏳ Waiting for container to start..."
sleep 5

# Step 8: Check status
echo "📊 Container Status:"
docker compose ps

# Step 11: Show logs
echo "📝 Recent logs:"
docker logs --tail 20 sentinel-honeypot

# Get EC2 public IP
EC2_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)

echo ""
echo "✅ =========================================="
echo "✅  DEPLOYMENT SUCCESSFUL! 🎉"
echo "✅ =========================================="
echo ""
echo "🌐 Your app is live at: http://${EC2_IP}"
echo "📡 API Endpoint: http://${EC2_IP}/api/message"
echo "🔑 API Key: ${HONEYPOT_KEY}"
echo ""
echo "📊 Useful Commands:"
echo "  - View logs: docker logs -f sentinel-honeypot"
echo "  - Restart: docker restart sentinel-honeypot"
echo "  - Stop: docker stop sentinel-honeypot"
echo "  - Rebuild: docker build -t sentinel-honeypot . && docker restart sentinel-honeypot"
echo ""
