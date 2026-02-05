# 🚀 AWS Deployment Guide - Sentinel Agentic Honeypot

This guide provides step-by-step instructions to deploy your application on AWS.

## 📋 Prerequisites
- AWS Account
- Docker installed locally
- AWS CLI installed and configured
- Your OpenAI API Key

---

## 🎯 Option 1: AWS Elastic Beanstalk (Easiest)

### Step 1: Install EB CLI
```bash
pip install awsebcli
```

### Step 2: Initialize Elastic Beanstalk
```bash
cd sentinel_-ai-honeypot-simulator
eb init -p docker sentinel-honeypot --region us-east-1
```

### Step 3: Create Environment
```bash
eb create sentinel-honeypot-env
```

### Step 4: Set Environment Variables
```bash
eb setenv OPENAI_API_KEY=your-openai-key-here
eb setenv HONEYPOT_API_KEY=sentinel-master-key
eb setenv PORT=8000
```

### Step 5: Deploy
```bash
eb deploy
```

### Step 6: Open Your App
```bash
eb open
```

**Your app will be live at**: `http://sentinel-honeypot-env.eba-xxxxx.us-east-1.elasticbeanstalk.com`

---

## 🐳 Option 2: AWS ECS (Elastic Container Service)

### Step 1: Build and Push Docker Image

1. **Create ECR Repository**:
```bash
aws ecr create-repository --repository-name sentinel-honeypot --region us-east-1
```

2. **Login to ECR**:
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
```

3. **Build Docker Image**:
```bash
docker build -t sentinel-honeypot .
```

4. **Tag Image**:
```bash
docker tag sentinel-honeypot:latest YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/sentinel-honeypot:latest
```

5. **Push to ECR**:
```bash
docker push YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/sentinel-honeypot:latest
```

### Step 2: Create ECS Cluster

1. Go to **AWS Console** → **ECS** → **Create Cluster**
2. Choose **Fargate** (serverless)
3. Name: `sentinel-honeypot-cluster`
4. Click **Create**

### Step 3: Create Task Definition

1. Go to **Task Definitions** → **Create new Task Definition**
2. Choose **Fargate**
3. Configure:
   - **Task Definition Name**: `sentinel-honeypot-task`
   - **Task Role**: Create new role or use existing
   - **Task Memory**: 1GB
   - **Task CPU**: 0.5 vCPU

4. **Add Container**:
   - **Container Name**: `sentinel-honeypot`
   - **Image**: `YOUR_AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/sentinel-honeypot:latest`
   - **Port Mappings**: `8000`
   - **Environment Variables**:
     - `OPENAI_API_KEY` = `your-key-here`
     - `HONEYPOT_API_KEY` = `sentinel-master-key`
     - `PORT` = `8000`

5. Click **Create**

### Step 4: Create Service

1. Go to your cluster → **Services** → **Create**
2. Configure:
   - **Launch Type**: Fargate
   - **Task Definition**: `sentinel-honeypot-task`
   - **Service Name**: `sentinel-honeypot-service`
   - **Number of Tasks**: 1
   - **Load Balancer**: Application Load Balancer (recommended)

3. Click **Create Service**

### Step 5: Configure Load Balancer (Optional but Recommended)

1. Create **Application Load Balancer**
2. Add **Target Group** pointing to port 8000
3. Configure **Health Check**: `/` (GET request)
4. Update **Security Group** to allow HTTP (80) and HTTPS (443)

**Your app will be live at**: `http://your-load-balancer-dns.us-east-1.elb.amazonaws.com`

---

## 🖥️ Option 3: AWS EC2 (Traditional VM)

### Step 1: Launch EC2 Instance

1. Go to **EC2** → **Launch Instance**
2. Choose **Amazon Linux 2023** or **Ubuntu 22.04**
3. Instance Type: **t2.small** or **t3.small**
4. Configure Security Group:
   - Allow **SSH (22)** from your IP
   - Allow **HTTP (80)** from anywhere
   - Allow **Custom TCP (8000)** from anywhere

5. Launch and download the `.pem` key

### Step 2: Connect to EC2

```bash
ssh -i your-key.pem ec2-user@your-ec2-public-ip
```

### Step 3: Install Docker

```bash
# Update system
sudo yum update -y

# Install Docker
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Step 4: Clone Your Repository

```bash
git clone https://github.com/parthibanktech/Sentinel-Agentic-Honeypot.git
cd Sentinel-Agentic-Honeypot
```

### Step 5: Create Environment File

```bash
cat > backend/.env << EOF
OPENAI_API_KEY=your-openai-key-here
HONEYPOT_API_KEY=sentinel-master-key
PORT=8000
EOF
```

### Step 6: Build and Run

```bash
# Build Docker image
docker build -t sentinel-honeypot .

# Run container
docker run -d \
  --name sentinel-honeypot \
  -p 80:8000 \
  --env-file backend/.env \
  --restart unless-stopped \
  sentinel-honeypot
```

### Step 7: Access Your App

**Your app will be live at**: `http://your-ec2-public-ip`

---

## 🌐 Option 4: AWS Amplify (Frontend Only)

If you want to deploy just the frontend and use Render for the backend:

### Step 1: Build Frontend

```bash
npm run build
```

### Step 2: Deploy to Amplify

1. Go to **AWS Amplify** → **New App** → **Deploy without Git**
2. Drag and drop the `dist/` folder
3. Click **Save and Deploy**

### Step 3: Update Environment

Update `src/environments/environment.ts`:
```typescript
apiUrl: 'https://sentinel-agentic-honeypot.onrender.com'
```

---

## 🔒 Security Best Practices

1. **Use AWS Secrets Manager** for API keys:
```bash
aws secretsmanager create-secret \
  --name sentinel/openai-key \
  --secret-string "your-openai-key"
```

2. **Enable HTTPS** with AWS Certificate Manager
3. **Use IAM Roles** instead of hardcoded credentials
4. **Enable CloudWatch Logs** for monitoring

---

## 💰 Cost Estimation

- **Elastic Beanstalk**: ~$15-30/month (t2.small)
- **ECS Fargate**: ~$10-20/month (0.5 vCPU, 1GB RAM)
- **EC2 t2.small**: ~$17/month
- **Amplify**: ~$0.15/GB (frontend only)

---

## 🆘 Troubleshooting

### Container Won't Start
```bash
# Check logs
docker logs sentinel-honeypot

# Or in ECS
aws ecs describe-tasks --cluster sentinel-honeypot-cluster --tasks TASK_ID
```

### Port Issues
Make sure Security Group allows inbound traffic on port 8000 or 80.

### Environment Variables Not Loading
Verify with:
```bash
docker exec sentinel-honeypot env | grep OPENAI
```

---

## ✅ Verification

Test your deployment:
```bash
curl -X POST https://your-aws-url.com/api/message \
  -H "Content-Type: application/json" \
  -H "x-api-key: sentinel-master-key" \
  -d '{
    "sessionId": "test-123",
    "message": {"sender": "scammer", "text": "Your account is blocked", "timestamp": 1234567890},
    "conversationHistory": []
  }'
```

---

## 🎉 You're Live!

Your Sentinel Agentic Honeypot is now running on AWS! 🚀🛡️
