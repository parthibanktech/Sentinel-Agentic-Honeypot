# --- STAGE 1: Build Angular Frontend ---
FROM node:20-alpine AS frontend-build
WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build

# --- STAGE 2: Python Backend & Final Image ---
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend from Stage 1
# Note: Angular build typically goes to dist/<project-name>
COPY --from=frontend-build /app/dist/ ./dist/

# Set environment variables
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Start command (serving the API)
# The frontend can be served by FastAPI static files or separately
CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8000"]
