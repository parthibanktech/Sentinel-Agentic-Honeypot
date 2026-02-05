# 🚀 CI/CD Setup Guide - Auto Deploy to EC2

This guide will help you set up **automated deployment** to EC2 using GitHub Actions. Every time you push to `main`, your app will automatically deploy!

---

## ⚡ Quick Setup (5 Steps)

### 1️⃣ Launch EC2 Instance (One-time setup)

1. Go to **AWS Console** → **EC2** → **Launch Instance**
2. **Settings**:
   - **Name**: `sentinel-honeypot`
   - **AMI**: Amazon Linux 2023
   - **Instance Type**: `t2.small` or `t3.small`
   - **Key Pair**: Create new (download `.pem` file - you'll need this!)
   
3. **Security Group**:
   ```
   SSH (22)         - 0.0.0.0/0 (for GitHub Actions)
   HTTP (80)        - 0.0.0.0/0 (for public access)
   Custom TCP 8000  - 0.0.0.0/0 (for API)
   ```

4. **Launch** and copy the **Public IPv4 address**

---

### 2️⃣ Initial EC2 Setup (One-time, 5 minutes)

SSH into your EC2 instance:

```bash
ssh -i your-key.pem ec2-user@YOUR-EC2-IP
```

Run the initial setup:

```bash
# Update system
sudo yum update -y

# Install Docker
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Git
sudo yum install git -y

# Clone repository (first time only)
cd ~
git clone https://github.com/parthibanktech/Sentinel-Agentic-Honeypot.git
cd Sentinel-Agentic-Honeypot

# Create initial environment file
cat > backend/.env << EOF
OPENAI_API_KEY=your-key-here
HONEYPOT_API_KEY=sentinel-master-key
PORT=8000
EOF

# Build and run initial deployment
docker build -t sentinel-honeypot .
docker run -d \
  --name sentinel-honeypot \
  -p 80:8000 \
  --env-file backend/.env \
  --restart unless-stopped \
  sentinel-honeypot
```

**Important**: Log out and log back in for Docker permissions to take effect:
```bash
exit
ssh -i your-key.pem ec2-user@YOUR-EC2-IP
```

---

### 3️⃣ Configure GitHub Secrets

Go to your GitHub repository:
**Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these **4 secrets**:

#### Secret 1: `EC2_SSH_PRIVATE_KEY`
```
# Content of your .pem file
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
(entire content of your .pem file)
...
-----END RSA PRIVATE KEY-----
```

#### Secret 2: `EC2_HOST`
```
YOUR-EC2-PUBLIC-IP
# Example: 54.123.45.67
```

#### Secret 3: `EC2_USER`
```
ec2-user
# Or 'ubuntu' if you used Ubuntu AMI
```

#### Secret 4: `OPENAI_API_KEY`
```
sk-proj-...your-openai-key...
```

#### Secret 5: `HONEYPOT_API_KEY`
```
sentinel-master-key
# Or your custom API key
```

---

### 4️⃣ Enable GitHub Actions

1. Go to your repository → **Actions** tab
2. If disabled, click **"I understand my workflows, go ahead and enable them"**
3. You should see the workflow: **"Deploy to EC2"**

---

### 5️⃣ Test Deployment

**Option A: Push to GitHub**
```bash
# Make any change
echo "# Test" >> README.md
git add .
git commit -m "Test CI/CD deployment"
git push origin main
```

**Option B: Manual Trigger**
1. Go to **Actions** tab
2. Click **"Deploy to EC2"** workflow
3. Click **"Run workflow"** → **"Run workflow"**

---

## 📊 Monitor Deployment

1. Go to **Actions** tab in GitHub
2. Click on the running workflow
3. Watch the deployment logs in real-time
4. ✅ Should complete in ~2-3 minutes

---

## 🎉 You're Done!

Now every time you push to `main`:
1. ✅ GitHub Actions triggers automatically
2. ✅ Connects to your EC2 instance
3. ✅ Pulls latest code
4. ✅ Rebuilds Docker container
5. ✅ Restarts the application
6. ✅ Your app is live with latest changes!

**Your app**: `http://YOUR-EC2-IP`

---

## 🔧 Useful Commands

### Check deployment status on EC2:
```bash
ssh -i your-key.pem ec2-user@YOUR-EC2-IP

# View running containers
docker ps

# View logs
docker logs -f sentinel-honeypot

# Restart manually
docker restart sentinel-honeypot
```

### Update environment variables:
```bash
ssh -i your-key.pem ec2-user@YOUR-EC2-IP
cd ~/Sentinel-Agentic-Honeypot
nano backend/.env  # Edit the file
docker restart sentinel-honeypot  # Restart to apply changes
```

---

## 🆘 Troubleshooting

### Deployment fails with "Permission denied"
- Make sure you added the **entire** `.pem` file content to `EC2_SSH_PRIVATE_KEY`
- Include the `-----BEGIN RSA PRIVATE KEY-----` and `-----END RSA PRIVATE KEY-----` lines

### Can't SSH to EC2
- Check Security Group allows SSH (22) from `0.0.0.0/0`
- Verify EC2 instance is running

### Docker permission denied
```bash
# On EC2, run:
sudo usermod -a -G docker ec2-user
# Then log out and log back in
```

### Container won't start
```bash
# Check logs
docker logs sentinel-honeypot

# Check environment variables
docker exec sentinel-honeypot env | grep OPENAI
```

---

## 🔄 Workflow Diagram

```
┌─────────────────┐
│  Push to main   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GitHub Actions  │
│   Triggered     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SSH to EC2     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Pull latest    │
│      code       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Build Docker   │
│     image       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Restart app    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ✅ Live!       │
└─────────────────┘
```

---

## 💡 Pro Tips

1. **Use Elastic IP** (optional but recommended):
   - Prevents IP changes when EC2 restarts
   - Go to EC2 → Elastic IPs → Allocate → Associate with instance

2. **Set up CloudWatch Logs**:
   - Monitor your application logs in AWS Console
   - Set up alerts for errors

3. **Add health checks**:
   - GitHub Actions can verify deployment success
   - Add a curl test to the workflow

4. **Branch protection**:
   - Require PR reviews before merging to main
   - Prevents accidental deployments

---

## ⏱️ Total Setup Time: ~15 minutes

✅ EC2 Launch: 3 min  
✅ Initial Setup: 5 min  
✅ GitHub Secrets: 3 min  
✅ Test Deploy: 3 min  

**Now you have fully automated CI/CD! 🎉**
