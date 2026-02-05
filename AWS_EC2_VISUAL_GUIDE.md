# 🖥️ AWS EC2 Setup - Visual Guide

## 📸 Step-by-Step Configuration

### 1️⃣ AMI Selection ✅
**You're already here!**
- **AMI**: Ubuntu Server 24.04 LTS (HVM), EBS General Purpose (SSD)
- **Architecture**: 64-bit (x86)
- ✅ This is perfect!

---

### 2️⃣ Key Pair (Current Step)

**What you see now:**
- Dialog box: "Create key pair"

**What to enter:**
1. **Key pair name**: `sentinel-key` (or any name you like)
2. **Key pair type**: RSA ✅ (already selected)
3. **Private key file format**: .pem ✅ (already selected)
4. Click **"Create key pair"**
5. **IMPORTANT**: The `.pem` file will download automatically - **SAVE IT!**

---

### 3️⃣ Instance Type

After creating the key pair, you'll see:
- **Instance type**: Select **t3.small** (recommended) or **t2.small**
  - Family: t3
  - vCPUs: 2
  - Memory: 2 GiB
  - This is perfect for the honeypot!

---

### 4️⃣ Network Settings (CRITICAL!)

Scroll down to **Network settings** section:

Click **"Edit"** button, then add these **3 inbound security group rules**:

#### Rule 1: SSH
- **Type**: SSH
- **Protocol**: TCP
- **Port**: 22
- **Source**: 0.0.0.0/0 (Anywhere IPv4)
- **Description**: SSH access

#### Rule 2: HTTP
- **Type**: HTTP
- **Protocol**: TCP
- **Port**: 80
- **Source**: 0.0.0.0/0 (Anywhere IPv4)
- **Description**: Web access

#### Rule 3: Custom TCP (API)
- **Type**: Custom TCP
- **Protocol**: TCP
- **Port**: 8000
- **Source**: 0.0.0.0/0 (Anywhere IPv4)
- **Description**: API access

---

### 5️⃣ Storage

**Default is fine!**
- 8 GiB gp3 (General Purpose SSD)
- No changes needed

---

### 6️⃣ Summary Panel (Right Side)

You should see:
- **Number of instances**: 1
- **Software Image (AMI)**: Ubuntu Server 24.04 LTS
- **Virtual server type (Instance type)**: t3-small (or t2-small)
- **Firewall (security group)**: New security group
- **Storage (volumes)**: 1 volume(s) - 8 GiB

---

### 7️⃣ Launch!

1. Review everything
2. Click **"Launch instance"** (orange button at bottom right)
3. Wait for "Successfully initiated launch of instance" message
4. Click **"View all instances"**

---

### 8️⃣ Get Your Public IP

After 1-2 minutes:
1. Go to **Instances** (left sidebar)
2. Select your instance (checkbox)
3. Look at the **Details** tab below
4. Find **Public IPv4 address** - **COPY THIS!**
   - Example: `54.123.45.67`

---

## ✅ Checklist

Before launching, verify:
- ✅ AMI: Ubuntu Server 24.04 LTS
- ✅ Instance type: t3.small or t2.small
- ✅ Key pair: Created and downloaded `.pem` file
- ✅ Security group: 3 rules (SSH 22, HTTP 80, Custom TCP 8000)
- ✅ All sources: 0.0.0.0/0

---

## 🚀 Next Steps

After EC2 is running:
1. Copy the **Public IPv4 address**
2. Open **START_HERE.md**
3. Follow **Step 2: Connect to EC2**
4. Use: `ssh -i "sentinel-key.pem" ubuntu@YOUR-EC2-IP`

---

## 💡 Quick Tips

- **Can't find Public IP?** Make sure instance state is "Running" (green)
- **Connection refused?** Wait 1-2 minutes after launch
- **Permission denied?** Run `chmod 400 sentinel-key.pem` first (Mac/Linux)

---

**You're doing great! Keep going! 🚀**
