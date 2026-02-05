# ⚡ QUICK START - Deploy to EC2 NOW (Before 10:30 PM)

**Current Time**: You have ~28 minutes! Let's go! 🚀

---

## 🎯 Choose Your Method

### Option 1: Automated CI/CD (5 minutes) ⭐ RECOMMENDED - ZERO MANUAL COMMANDS

Follow **AUTO_DEPLOY.md** - GitHub Actions does everything automatically!

### Option 2: Manual Deployment (10 minutes)

Follow **DEPLOYMENT.md** - Copy-paste commands if you prefer manual control

---

## 🚀 FASTEST PATH (10 Minutes)

### Step 1: Launch EC2 (3 min)
1. Go to: https://console.aws.amazon.com/ec2/
2. Click "Launch Instance"
3. Settings:
   - Name: `sentinel-honeypot`
   - AMI: **Amazon Linux 2023** or **Ubuntu Server 22.04**
   - Type: t2.small
   - Key: Create new → Download `.pem`
   - Security: Allow ports 22, 80, 8000 from 0.0.0.0/0
4. Launch & copy Public IP

### Step 2: Connect (1 min)

**Amazon Linux:**
```powershell
ssh -i "your-key.pem" ec2-user@YOUR-EC2-IP
```

**Ubuntu:**
```powershell
ssh -i "your-key.pem" ubuntu@YOUR-EC2-IP
```

### Step 3: Deploy (5 min)

**For Amazon Linux:**
```bash
# Update & install Docker
sudo yum update -y
sudo yum install docker git -y
sudo service docker start
sudo usermod -a -G docker ec2-user
newgrp docker
```

**For Ubuntu:**
```bash
# Update & install Docker
sudo apt-get update -y
sudo apt-get install -y docker.io git
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ubuntu
newgrp docker
```

**Then (both systems):**
```bash

# Clone & setup
cd ~
git clone https://github.com/parthibanktech/Sentinel-Agentic-Honeypot.git
cd Sentinel-Agentic-Honeypot

# Add your OpenAI key
cat > backend/.env << 'EOF'
OPENAI_API_KEY=YOUR_KEY_HERE
HONEYPOT_API_KEY=sentinel-master-key
PORT=8000
EOF

# Build & run
docker build -t sentinel-honeypot .
docker run -d --name sentinel-honeypot -p 80:8000 --env-file backend/.env --restart unless-stopped sentinel-honeypot
```

### Step 4: Test (1 min)
```bash
# Get your IP
curl http://169.254.169.254/latest/meta-data/public-ipv4

# Test API
curl -X POST http://YOUR-EC2-IP/api/message \
  -H "Content-Type: application/json" \
  -H "x-api-key: sentinel-master-key" \
  -d '{"sessionId":"test","message":{"sender":"scammer","text":"Your account is blocked","timestamp":123},"conversationHistory":[]}'
```

---

## 📝 Submit to Evaluator

```
API Endpoint: http://YOUR-EC2-IP/api/message
API Key: sentinel-master-key
Frontend: http://YOUR-EC2-IP
GitHub: https://github.com/parthibanktech/Sentinel-Agentic-Honeypot
```

---

## 📚 Full Documentation

- **DEPLOYMENT.md** - Complete deployment guide with API docs
- **CI_CD_SETUP.md** - Automated deployment with GitHub Actions
- **AWS_DEPLOYMENT.md** - All AWS deployment options
- **QUICK_EC2_DEPLOY.md** - Alternative quick guide

---

## ✅ You're Ready!

Everything is committed and pushed to GitHub. Just follow the steps above!

**Good luck! 🎉**
