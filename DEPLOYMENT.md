# 🚀 Deployment Guide - Get Your API Live in 10 Minutes

This guide will help you deploy the Sentinel Honeypot API to EC2 and get your **API endpoint** for the evaluator.

---

## 🎯 What You'll Get

After deployment, you'll have:
- ✅ **API Endpoint**: `http://YOUR-EC2-IP/api/message`
- ✅ **Frontend**: `http://YOUR-EC2-IP`
- ✅ **API Key**: `sentinel-master-key`

---

## 📋 Quick Deployment Steps

### 1️⃣ Launch EC2 Instance (3 minutes)

1. **Go to AWS Console**: https://console.aws.amazon.com/ec2/
2. Click **"Launch Instance"**

3. **Configure Instance**:
   ```
   Name: sentinel-honeypot
   AMI: Amazon Linux 2023 (or Ubuntu 22.04)
   Instance Type: t2.small (or t3.small)
   ```

4. **Create/Select Key Pair**:
   - Click "Create new key pair"
   - Name: `sentinel-key`
   - Type: RSA
   - Format: `.pem`
   - **Download and save the .pem file!**

5. **Configure Security Group** (IMPORTANT):
   Click "Edit" next to Network Settings and add these rules:
   ```
   Type            Port    Source          Description
   ─────────────────────────────────────────────────────
   SSH             22      0.0.0.0/0       SSH access
   HTTP            80      0.0.0.0/0       Web access
   Custom TCP      8000    0.0.0.0/0       API access
   ```

6. Click **"Launch Instance"**

7. **Wait 1-2 minutes** for instance to start

8. **Copy the Public IPv4 Address**:
   - Go to Instances → Select your instance
   - Copy the **Public IPv4 address** (e.g., `54.123.45.67`)

---

### 2️⃣ Connect to EC2 (1 minute)

**Windows (PowerShell):**
```powershell
# Navigate to where you saved the .pem file
cd Downloads

# Amazon Linux
ssh -i "sentinel-key.pem" ec2-user@YOUR-EC2-IP

# Ubuntu
ssh -i "sentinel-key.pem" ubuntu@YOUR-EC2-IP
```

**Mac/Linux:**
```bash
chmod 400 sentinel-key.pem

# Amazon Linux
ssh -i sentinel-key.pem ec2-user@YOUR-EC2-IP

# Ubuntu
ssh -i sentinel-key.pem ubuntu@YOUR-EC2-IP
```

Type `yes` when asked about authenticity.

---

### 3️⃣ Deploy the Application (5 minutes)

Once connected to EC2, **copy and paste these commands**:

**For Amazon Linux:**
```bash
# 1. Update system
sudo yum update -y

# 2. Install Docker
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# 3. Install Git
sudo yum install git -y

# 4. Activate Docker permissions
newgrp docker
```

**For Ubuntu:**
```bash
# 1. Update system
sudo apt-get update -y

# 2. Install Docker
sudo apt-get install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ubuntu

# 3. Install Git
sudo apt-get install -y git

# 4. Activate Docker permissions
newgrp docker
```

**Then (both systems):**
```bash
# 5. Clone repository
cd ~
git clone https://github.com/parthibanktech/Sentinel-Agentic-Honeypot.git
cd Sentinel-Agentic-Honeypot

# 6. Create environment file
# IMPORTANT: Replace YOUR_OPENAI_KEY with your actual OpenAI API key
cat > backend/.env << 'EOF'
OPENAI_API_KEY=YOUR_OPENAI_KEY_HERE
HONEYPOT_API_KEY=sentinel-master-key
PORT=8000
EOF

# 7. Build Docker image (takes 2-3 minutes)
docker build -t sentinel-honeypot .

# 8. Run the application
docker run -d \
  --name sentinel-honeypot \
  -p 80:8000 \
  --env-file backend/.env \
  --restart unless-stopped \
  sentinel-honeypot

# 9. Check status
docker ps
docker logs sentinel-honeypot
```

---

### 4️⃣ Get Your API Endpoint (1 minute)

Your API is now live! Here's what to share with the evaluator:

**Get your EC2 IP:**
```bash
curl http://169.254.169.254/latest/meta-data/public-ipv4
```

**Your API Details:**
```
API Endpoint: http://YOUR-EC2-IP/api/message
API Key: sentinel-master-key
Method: POST
```

---

## 🧪 Test Your API

**From your local machine** (replace YOUR-EC2-IP):

```bash
curl -X POST http://YOUR-EC2-IP/api/message \
  -H "Content-Type: application/json" \
  -H "x-api-key: sentinel-master-key" \
  -d '{
    "sessionId": "test-session-123",
    "message": {
      "sender": "scammer",
      "text": "Your account has been suspended. Click here to verify.",
      "timestamp": 1738777200
    },
    "conversationHistory": []
  }'
```

**Expected Response:**
```json
{
  "sessionId": "test-session-123",
  "response": {
    "sender": "agent",
    "text": "Oh no! What happened? I didn't do anything wrong...",
    "timestamp": 1738777205
  },
  "scamDetected": true,
  "confidence": 0.95,
  "extractedIntel": {
    "scamType": "Account Suspension Phishing",
    "tactics": ["urgency", "fear"],
    "indicators": ["suspicious link", "account verification"]
  }
}
```

---

## 📝 API Documentation for Evaluator

### Endpoint
```
POST http://YOUR-EC2-IP/api/message
```

### Headers
```
Content-Type: application/json
x-api-key: sentinel-master-key
```

### Request Body
```json
{
  "sessionId": "string",
  "message": {
    "sender": "scammer",
    "text": "string",
    "timestamp": 1234567890
  },
  "conversationHistory": [
    {
      "sender": "string",
      "text": "string",
      "timestamp": 1234567890
    }
  ]
}
```

### Response
```json
{
  "sessionId": "string",
  "response": {
    "sender": "agent",
    "text": "string",
    "timestamp": 1234567890
  },
  "scamDetected": true,
  "confidence": 0.95,
  "extractedIntel": {
    "scamType": "string",
    "tactics": ["string"],
    "indicators": ["string"]
  }
}
```

---

## 🔧 Useful Commands

### View application logs:
```bash
ssh -i sentinel-key.pem ec2-user@YOUR-EC2-IP
docker logs -f sentinel-honeypot
```

### Restart application:
```bash
docker restart sentinel-honeypot
```

### Update code and redeploy:
```bash
cd ~/Sentinel-Agentic-Honeypot
git pull
docker build -t sentinel-honeypot .
docker stop sentinel-honeypot
docker rm sentinel-honeypot
docker run -d --name sentinel-honeypot -p 80:8000 --env-file backend/.env --restart unless-stopped sentinel-honeypot
```

### Check if app is running:
```bash
docker ps | grep sentinel-honeypot
```

---

## 🆘 Troubleshooting

### Can't access the API from browser/curl

**Check 1: Is the container running?**
```bash
docker ps
```
Should show `sentinel-honeypot` container.

**Check 2: Check logs for errors**
```bash
docker logs sentinel-honeypot
```

**Check 3: Verify Security Group**
- Go to EC2 Console → Instances → Your instance
- Click "Security" tab
- Verify inbound rules allow:
  - Port 80 from 0.0.0.0/0
  - Port 8000 from 0.0.0.0/0

**Check 4: Test locally on EC2**
```bash
curl http://localhost:8000/api/message \
  -H "Content-Type: application/json" \
  -H "x-api-key: sentinel-master-key" \
  -d '{"sessionId":"test","message":{"sender":"scammer","text":"test","timestamp":123},"conversationHistory":[]}'
```

### OpenAI API errors

**Check environment variable:**
```bash
docker exec sentinel-honeypot env | grep OPENAI
```

**Update API key:**
```bash
cd ~/Sentinel-Agentic-Honeypot
nano backend/.env  # Edit and save
docker restart sentinel-honeypot
```

### Port 80 already in use

```bash
sudo lsof -i :80
sudo kill -9 <PID>
docker restart sentinel-honeypot
```

---

## 📊 What to Submit to Evaluator

```
API Endpoint: http://YOUR-EC2-IP/api/message
API Key: sentinel-master-key
Frontend URL: http://YOUR-EC2-IP
GitHub Repo: https://github.com/parthibanktech/Sentinel-Agentic-Honeypot
```

---

## 🎉 You're Live!

Your Sentinel Honeypot API is now deployed and ready for evaluation!

**Total Time**: ~10 minutes  
**Cost**: ~$0.02/hour (~$15/month for t2.small)

---

## 💡 Optional: Set Up Auto-Deploy with CI/CD

Want automatic deployments when you push to GitHub? See **CI_CD_SETUP.md** for instructions.

---

## 📞 Need Help?

- Check logs: `docker logs sentinel-honeypot`
- Restart app: `docker restart sentinel-honeypot`
- Check status: `docker ps`
- View this guide: https://github.com/parthibanktech/Sentinel-Agentic-Honeypot/blob/main/DEPLOYMENT.md
