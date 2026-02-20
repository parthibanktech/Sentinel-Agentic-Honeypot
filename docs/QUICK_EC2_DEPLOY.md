# ⚡ QUICK EC2 DEPLOYMENT - 10 Minutes

## 🎯 Prerequisites
- AWS Account
- Your OpenAI API Key ready

---

## 📋 Step-by-Step (Copy & Paste)

### 1️⃣ Launch EC2 Instance (3 minutes)

1. Go to **AWS Console** → **EC2** → **Launch Instance**
2. **Quick Settings**:
   - **Name**: `sentinel-honeypot`
   - **AMI**: Amazon Linux 2023 (or Ubuntu 22.04)
   - **Instance Type**: `t2.small` or `t3.small`
   - **Key Pair**: Create new or use existing (download `.pem` file)
   
3. **Security Group** - Click "Edit" and add these rules:
   ```
   SSH (22)         - Your IP
   HTTP (80)        - 0.0.0.0/0 (Anywhere)
   Custom TCP 8000  - 0.0.0.0/0 (Anywhere)
   ```

4. Click **Launch Instance**
5. Wait 1-2 minutes for instance to start
6. Copy the **Public IPv4 address**

---

### 2️⃣ Connect to EC2 (1 minute)

**Windows (PowerShell):**
```powershell
# Navigate to where you downloaded the .pem file
cd Downloads

# Connect (replace with your details)
ssh -i "your-key.pem" ec2-user@YOUR-EC2-IP
```

**Mac/Linux:**
```bash
chmod 400 your-key.pem
ssh -i your-key.pem ec2-user@YOUR-EC2-IP
```

---

### 3️⃣ Run Deployment Script (5 minutes)

**Option A: Automated Script (Recommended)**

```bash
# Download and run the deployment script
curl -o deploy.sh https://raw.githubusercontent.com/parthibanktech/Sentinel-Agentic-Honeypot/main/ec2-quick-deploy.sh
chmod +x deploy.sh
./deploy.sh
```

When prompted:
- Enter your **OpenAI API Key**
- Enter your **Honeypot API Key** (or press Enter for default: `sentinel-master-key`)

---

**Option B: Manual Commands**

```bash
# 1. Update system
sudo yum update -y

# 2. Install Docker
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user
newgrp docker

# 3. Install Git
sudo yum install git -y

# 4. Clone repository
cd ~
git clone https://github.com/parthibanktech/Sentinel-Agentic-Honeypot.git
cd Sentinel-Agentic-Honeypot

# 5. Create environment file (replace YOUR_KEY_HERE)
cat > backend/.env << EOF
OPENAI_API_KEY=YOUR_KEY_HERE
HONEYPOT_API_KEY=sentinel-master-key
PORT=8000
EOF

# 6. Build and run
docker build -t sentinel-honeypot .
docker run -d \
  --name sentinel-honeypot \
  -p 80:8000 \
  --env-file backend/.env \
  --restart unless-stopped \
  sentinel-honeypot

# 7. Check status
docker logs sentinel-honeypot
```

---

### 4️⃣ Verify Deployment (1 minute)

**Test the API:**
```bash
curl -X POST http://YOUR-EC2-IP/api/message \
  -H "Content-Type: application/json" \
  -H "x-api-key: sentinel-master-key" \
  -d '{
    "sessionId": "test-123",
    "message": {"sender": "scammer", "text": "Your account is blocked", "timestamp": 1234567890},
    "conversationHistory": []
  }'
```

**Open in Browser:**
```
http://YOUR-EC2-IP
```

---

## 🎉 You're Live!

Your Sentinel Honeypot is now running at:
- **Frontend**: `http://YOUR-EC2-IP`
- **API**: `http://YOUR-EC2-IP/api/message`
- **API Key**: `sentinel-master-key`

---

## 🔧 Useful Commands

```bash
# View live logs
docker logs -f sentinel-honeypot

# Restart container
docker restart sentinel-honeypot

# Stop container
docker stop sentinel-honeypot

# Update code and redeploy
cd ~/Sentinel-Agentic-Honeypot
git pull
docker build -t sentinel-honeypot .
docker stop sentinel-honeypot
docker rm sentinel-honeypot
docker run -d --name sentinel-honeypot -p 80:8000 --env-file backend/.env --restart unless-stopped sentinel-honeypot
```

---

## 🆘 Troubleshooting

### Container won't start
```bash
docker logs sentinel-honeypot
```

### Port already in use
```bash
sudo lsof -i :80
sudo kill -9 <PID>
```

### Can't access from browser
- Check Security Group allows HTTP (80) from 0.0.0.0/0
- Verify instance is running: `docker ps`

---

## 💡 Pro Tips

1. **Get your EC2 IP inside the instance:**
   ```bash
   curl http://169.254.169.254/latest/meta-data/public-ipv4
   ```

2. **Keep terminal session alive:**
   ```bash
   screen  # Start screen session
   # Run your commands
   # Press Ctrl+A then D to detach
   # Reconnect with: screen -r
   ```

3. **Monitor resources:**
   ```bash
   docker stats sentinel-honeypot
   ```

---

## ⏱️ Total Time: ~10 minutes

✅ EC2 Launch: 3 min  
✅ SSH Connect: 1 min  
✅ Run Script: 5 min  
✅ Verify: 1 min  

**Good luck with your deployment! 🚀🛡️**
