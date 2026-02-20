# 🚀 ULTRA-QUICK REFERENCE - Deploy in 5 Minutes

**Time**: 22:07 PM | **Deadline**: 10:30 PM | **You have**: ~23 minutes ⏰

---

## ⚡ FASTEST METHOD: Automated CI/CD

### 1. Launch EC2 (2 min)
- AWS Console → EC2 → Launch Instance
- **AMI**: Amazon Linux 2023 OR Ubuntu Server 22.04
- **Type**: t2.small
- **Security**: Ports 22, 80, 8000 from 0.0.0.0/0
- Download `.pem` key → Copy Public IP

### 2. One-Time Setup (2 min)
**Amazon Linux:**
```bash
ssh -i key.pem ec2-user@YOUR-IP
sudo yum update -y && sudo yum install docker git -y
sudo service docker start && sudo usermod -a -G docker ec2-user
cd ~ && git clone https://github.com/parthibanktech/Sentinel-Agentic-Honeypot.git
exit
```

**Ubuntu:**
```bash
ssh -i key.pem ubuntu@YOUR-IP
sudo apt-get update -y && sudo apt-get install -y docker.io git
sudo systemctl start docker && sudo usermod -a -G docker ubuntu
cd ~ && git clone https://github.com/parthibanktech/Sentinel-Agentic-Honeypot.git
exit
```

### 3. GitHub Secrets (1 min)
GitHub → Settings → Secrets → Actions → Add:
- `EC2_SSH_PRIVATE_KEY` = .pem file content
- `EC2_HOST` = Your EC2 IP
- `EC2_USER` = `ec2-user` or `ubuntu`
- `OPENAI_API_KEY` = Your key
- `HONEYPOT_API_KEY` = `sentinel-master-key`

### 4. Deploy! (30 sec)
```bash
git commit --allow-empty -m "Deploy"
git push origin main
```

**GitHub Actions auto-deploys in 2-3 min!**

---

## 📝 Submit to Evaluator

```
API: http://YOUR-EC2-IP/api/message
Key: sentinel-master-key
Frontend: http://YOUR-EC2-IP
GitHub: https://github.com/parthibanktech/Sentinel-Agentic-Honeypot
```

---

## 📚 Full Guides

- **AUTO_DEPLOY.md** - Automated CI/CD (recommended)
- **DEPLOYMENT.md** - Manual deployment
- **START_HERE.md** - Navigation guide

---

**GO! You got this! 🚀**
