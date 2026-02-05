# 🚀 Deployment Guide: Sentinel Agentic Honey-Pot

This guide explains how to deploy the Sentinel Agentic Honey-Pot to **Render** using **Docker** and set up the **CI/CD** pipeline.

## 1. Prerequisites
- A **GitHub Account**.
- A **Render Account**.
- An **OpenAI API Key** (starts with `sk-...`).
- A **GUVI Evaluation Endpoint** (provided in the problem statement).

---

## 2. Docker Deployment on Render (Recommended)

Render will use the included `Dockerfile` to build both the Angular frontend and the FastAPI backend into a single container.

1. **Create a New Web Service**:
   - Log in to [Render](https://dashboard.render.com/).
   - Click **New +** -> **Web Service**.
   - Connect your GitHub repository: `parthibanktech/Sentinel-Agentic-Honeypot`.

2. **Configure Service**:
   - **Name**: `sentinel-honeypot`
   - **Region**: Choose the one closest to you (e.g., Singapore or US East).
   - **Branch**: `main`
   - **Runtime**: `Docker` (Render should auto-detect this).

3. **Set Environment Variables**:
   In the **Environment** section, add the following variables:
   - `OPENAI_API_KEY`: Your OpenAI Secret Key.
   - `HONEYPOT_API_KEY`: `sentinel-master-key` (Used for x-api-key header validation).
   - `PORT`: `8000`

4. **Deploy**:
   - Click **Create Web Service**. Render will start building the Docker image.
   - Once the build is finished (Status: `Live`), your API and UI will be available at your Render URL (e.g., `https://sentinel-honeypot.onrender.com`).

---

## 3. Setting Up CI/CD (Auto-Deploy)

The project includes a GitHub Action to trigger a re-deployment on Render every time you push code to `main`.

1. **Get your Render Deploy Hook**:
   - In your Render Web Service Dashboard, go to **Settings**.
   - Scroll down to **Deploy Hook**.
   - Copy the URL (it looks like `https://api.render.com/deploy/srv-...`).

2. **Add Secret to GitHub**:
   - Go to your GitHub repository: `parthibanktech/Sentinel-Agentic-Honeypot`.
   - Click **Settings** -> **Secrets and variables** -> **Actions**.
   - Click **New repository secret**.
   - **Name**: `RENDER_DEPLOY_HOOK_URL`
   - **Value**: Paste your Render Deploy Hook URL.

3. **Test the Pipeline**:
   - Push a small change (e.g., update `README.md`).
   - Go to the **Actions** tab in GitHub to see the test run.
   - Once the test passes, it will trigger the Render deployment.

---

## 4. API Testing

Once deployed, you can test your API using the provided `backend/test_api.py` script by updating the `URL` variable to your Render URL.

**Endpoint**: `POST /api/message`
**Header**: `x-api-key: sentinel-master-key`

---

## 🛡️ Hackathon Checklist
- [ ] API accepts `sessionId`, `message`, `conversationHistory`, and `metadata`.
- [ ] AI Agent (Alex) engages with naive/polite persona.
- [ ] Scam intelligence is extracted (Bank/UPI/Links).
- [ ] Final result is automatically sent to the GUVI callback endpoint.
