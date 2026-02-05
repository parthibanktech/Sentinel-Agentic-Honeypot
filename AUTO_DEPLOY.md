# 🚀 AUTOMATED DEPLOYMENT - Zero Manual Commands

**Use CI/CD to auto-deploy with just a Git push!**

---

## ⚡ Super Fast Setup (5 Minutes)

### Step 1: Launch EC2 Instance (2 min)

1. **AWS Console**: https://console.aws.amazon.com/ec2/
2. Click **"Launch Instance"**
3. **Configure**:
   ```
   Name: sentinel-honeypot
   AMI: Amazon Linux 2023
   Instance Type: t2.small
   Key Pair: Create new → Download .pem file
   ```
4. **Security Group** - Add these ports:
   ```
   SSH (22)         - 0.0.0.0/0
   HTTP (80)        - 0.0.0.0/0
   Custom TCP 8000  - 0.0.0.0/0
   ```
5. **Launch** → Copy **Public IPv4 address**

---

### Step 2: One-Time EC2 Setup (2 min)

Connect to EC2:
```bash
ssh -i "your-key.pem" ec2-user@YOUR-EC2-IP
```

Run this **ONE-TIME setup** (copy-paste all):
```bash
# Install Docker & Git
sudo yum update -y
sudo yum install docker git -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Clone repo (first time only)
cd ~
git clone https://github.com/parthibanktech/Sentinel-Agentic-Honeypot.git

# Done! Exit
exit
```

---

### Step 3: Configure GitHub Secrets (1 min)

Go to: **GitHub Repo → Settings → Secrets and variables → Actions**

Add these **5 secrets**:

| Secret Name | Value |
|------------|-------|
| `EC2_SSH_PRIVATE_KEY` | Content of your `.pem` file (entire file) |
| `EC2_HOST` | Your EC2 Public IP (e.g., `54.123.45.67`) |
| `EC2_USER` | `ec2-user` |
| `OPENAI_API_KEY` | Your OpenAI API key |
| `HONEYPOT_API_KEY` | `sentinel-master-key` |

---

### Step 4: Deploy! (30 seconds)

**Option A: Push to GitHub**
```bash
# Any change triggers deployment
git commit --allow-empty -m "Deploy to EC2"
git push origin main
```

**Option B: Manual Trigger**
1. Go to **GitHub → Actions** tab
2. Click **"Deploy to EC2"**
3. Click **"Run workflow"**

---

## 🎉 That's It!

GitHub Actions will:
1. ✅ SSH into your EC2
2. ✅ Pull latest code
3. ✅ Build Docker image
4. ✅ Deploy automatically
5. ✅ Restart the app

**Watch it live**: GitHub → Actions tab

---

## 📊 Your API Endpoint

After deployment completes (~2-3 min):

```
API Endpoint: http://YOUR-EC2-IP/api/message
API Key: sentinel-master-key
Frontend: http://YOUR-EC2-IP
```

---

## 🧪 Test Your API

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

## 🔄 Future Deployments

Just push to GitHub - **that's it!**

```bash
# Make changes
git add .
git commit -m "Update feature"
git push origin main

# Auto-deploys in 2-3 minutes! 🚀
```

---

## 🆘 Troubleshooting

### Deployment fails in GitHub Actions

**Check logs**: GitHub → Actions → Click on failed workflow

**Common issues**:
1. Wrong EC2 IP in secrets
2. Missing `.pem` file content in `EC2_SSH_PRIVATE_KEY`
3. Security Group doesn't allow SSH from 0.0.0.0/0

### Can't access API

**SSH to EC2 and check**:
```bash
ssh -i your-key.pem ec2-user@YOUR-EC2-IP
docker ps  # Should show sentinel-honeypot
docker logs sentinel-honeypot  # Check for errors
```

---

## ⏱️ Total Time: 5 Minutes

✅ EC2 Launch: 2 min  
✅ One-time setup: 2 min  
✅ GitHub Secrets: 1 min  
✅ Deploy: 30 sec (+ 2-3 min auto-deploy)

**No manual Docker commands needed! 🎉**
