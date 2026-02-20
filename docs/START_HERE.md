# ⚡ QUICK START - Deploy to EC2 NOW

**Time Remaining**: ~18 minutes until 10:30 PM! Let's go! 🚀

---

## 🎯 Choose Your Deployment Method

### ⭐ Option 1: Automated CI/CD (5 minutes) - RECOMMENDED
**Zero manual Docker commands!** GitHub Actions does everything.  
👉 **Follow: AUTO_DEPLOY.md**

### Option 2: Manual Deployment (8 minutes)
Full control with copy-paste commands.  
👉 **Follow: DEPLOYMENT.md**

---

## 🚀 MANUAL DEPLOYMENT (8 Minutes)

### Step 1: Launch EC2 Instance (2 min)

1. **Go to**: https://console.aws.amazon.com/ec2/
2. Click **"Launch Instance"**
3. **Configure**:
   - **Name**: `sentinel-honeypot`
   - **AMI**: Ubuntu Server 24.04 LTS (or Amazon Linux 2023)
   - **Instance Type**: t3.small or t2.small
   - **Key Pair**: Create new
     - Name: `sentinel-key`
     - Type: RSA
     - Format: .pem
     - **Download and save the .pem file!**
   
4. **Network Settings - Security Group**:
   Click "Edit" and add these **3 rules**:
   
   | Type | Port | Source | Description |
   |------|------|--------|-------------|
   | SSH | 22 | 0.0.0.0/0 | SSH access |
   | HTTP | 80 | 0.0.0.0/0 | Web access |
   | Custom TCP | 8000 | 0.0.0.0/0 | API access |

5. Click **"Launch Instance"**
6. Wait 1-2 minutes, then **copy the Public IPv4 address**

---

### Step 2: Connect to EC2 (1 min)

**Windows (PowerShell):**
```powershell
# Navigate to where you saved the .pem file
cd Downloads

# For Ubuntu (if you chose Ubuntu Server 24.04)
ssh -i "sentinel-key.pem" ubuntu@YOUR-EC2-IP

# For Amazon Linux (if you chose Amazon Linux 2023)
ssh -i "sentinel-key.pem" ec2-user@YOUR-EC2-IP
```

**Mac/Linux:**
```bash
chmod 400 sentinel-key.pem

# For Ubuntu
ssh -i sentinel-key.pem ubuntu@YOUR-EC2-IP

# For Amazon Linux
ssh -i sentinel-key.pem ec2-user@YOUR-EC2-IP
```

Type `yes` when asked about authenticity.

---

### Step 3: Deploy Application (5 min)

**For Ubuntu Server 24.04:**
```bash
# Install Docker & Git
sudo apt-get update -y
sudo apt-get install -y docker.io git
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ubuntu
newgrp docker

# Clone repository
cd ~
git clone https://github.com/parthibanktech/Sentinel-Agentic-Honeypot.git
cd Sentinel-Agentic-Honeypot

# Create environment file (REPLACE YOUR_OPENAI_KEY_HERE!)
cat > backend/.env << 'EOF'
OPENAI_API_KEY=YOUR_OPENAI_KEY_HERE
HONEYPOT_API_KEY=sentinel-master-key
PORT=8000
EOF

# Build & run (takes 2-3 minutes)
docker build -t sentinel-honeypot .
docker run -d --name sentinel-honeypot -p 80:8000 --env-file backend/.env --restart unless-stopped sentinel-honeypot

# Check status
docker ps
docker logs sentinel-honeypot
```

**For Amazon Linux 2023:**
```bash
# Install Docker & Git
sudo yum update -y
sudo yum install docker git -y
sudo service docker start
sudo usermod -a -G docker ec2-user
newgrp docker

# Clone repository
cd ~
git clone https://github.com/parthibanktech/Sentinel-Agentic-Honeypot.git
cd Sentinel-Agentic-Honeypot

# Create environment file (REPLACE YOUR_OPENAI_KEY_HERE!)
cat > backend/.env << 'EOF'
OPENAI_API_KEY=YOUR_OPENAI_KEY_HERE
HONEYPOT_API_KEY=sentinel-master-key
PORT=8000
EOF

# Build & run (takes 2-3 minutes)
docker build -t sentinel-honeypot .
docker run -d --name sentinel-honeypot -p 80:8000 --env-file backend/.env --restart unless-stopped sentinel-honeypot

# Check status
docker ps
docker logs sentinel-honeypot
```

---

### Step 4: Get Your API Endpoint

```bash
# Get your EC2 public IP
curl http://169.254.169.254/latest/meta-data/public-ipv4
```

**Your endpoints:**
```
API: http://YOUR-EC2-IP/api/message
Frontend: http://YOUR-EC2-IP
API Key: sentinel-master-key
```

---

## 🧪 Test Your Deployment

**From your local machine:**
```bash
curl -X POST http://YOUR-EC2-IP/api/message \
  -H "Content-Type: application/json" \
  -H "x-api-key: sentinel-master-key" \
  -d '{
    "sessionId": "test-123",
    "message": {
      "sender": "scammer",
      "text": "Your account is blocked",
      "timestamp": 1738777200
    },
    "conversationHistory": []
  }'
```

---

## 📝 Submit to Evaluator

```
API Endpoint: http://YOUR-EC2-IP/api/message
API Key: sentinel-master-key
Frontend URL: http://YOUR-EC2-IP
GitHub Repo: https://github.com/parthibanktech/Sentinel-Agentic-Honeypot
```

---

## 📚 Other Guides

- **AUTO_DEPLOY.md** - Automated CI/CD deployment
- **DEPLOYMENT.md** - Detailed manual deployment
- **QUICK_REF.md** - Ultra-quick reference
- **CI_CD_SETUP.md** - CI/CD pipeline setup

---

## ✅ You're Ready!

Follow the steps above and you'll be live in 8 minutes!

**Good luck! 🎉🚀**
