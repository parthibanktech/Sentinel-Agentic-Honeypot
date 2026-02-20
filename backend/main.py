import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.app.api.endpoints import router as api_router
from backend.app.core.config import HONEYPOT_API_KEY

# Initialize FastAPI
app = FastAPI(title="Sentinel Agentic Honey-Pot API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Router
app.include_router(api_router, prefix="/api")

# --- STATIC FILES ---
# Serve frontend build if it exists
dist_path = os.path.join(os.getcwd(), "dist")
static_dir = None
if os.path.exists(dist_path):
    # Find the nested project folder inside dist if Angular put it there
    project_dirs = [d for d in os.listdir(dist_path) if os.path.isdir(os.path.join(dist_path, d))]
    if project_dirs:
        static_dir = os.path.join(dist_path, project_dirs[0], "browser") if os.path.exists(os.path.join(dist_path, project_dirs[0], "browser")) else os.path.join(dist_path, project_dirs[0])
    else:
        static_dir = dist_path

if static_dir and os.path.exists(static_dir):
    print(f"Serving static files from: {static_dir}")
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    
    @app.get("/{full_path:path}")
    async def catch_all(full_path: str):
        if full_path.startswith("api"): return {"error": "API route not found"} # Don't catch API calls
        index_file = os.path.join(static_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"error": "Not Found"}
else:
    @app.get("/")
    def health_check():
        return {"status": "online", "service": "Sentinel Honey-Pot API (Modular v2.0)"}

def print_banner():
    banner = """
    ================================================================
     🛡️  SENTINEL AGENTIC HONEYPOT - Autonomous Predator Shield 🛡️
    ================================================================
     [STATUS] Core Intelligence:   GPT-4o + Ensemble ML
     [STATUS] Local Scam Model:    Voting (RF + SVM + LR)
     [STATUS] Architecture:        Modular Microservices
     [STATUS] Persona Emulator:    "Alex" (v3.1)
    ================================================================
    """
    print(banner)

if __name__ == "__main__":
    print_banner()
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Sentinel API starting on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
