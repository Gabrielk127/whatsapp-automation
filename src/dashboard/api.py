"""FastAPI backend for WhatsApp Automation Dashboard."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

# Import MongoDB repository
from src.repositories.mongo_repository import mongo_repo
from src.utils.log_manager import LogManager

app = FastAPI(title="WhatsApp Automation Dashboard API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

log_manager = LogManager()

# Database connection flag
DB_CONNECTED = False

# Serve static files - serve index.html directly
dashboard_dir = Path(__file__).parent


@app.get("/")
async def root():
    """Serve dashboard HTML."""
    html_path = dashboard_dir / "index.html"
    if html_path.exists():
        with open(html_path, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    return {"error": "Dashboard not found"}


@app.get("/styles.css")
async def get_styles():
    """Serve CSS file."""
    css_path = dashboard_dir / "styles.css"
    if css_path.exists():
        with open(css_path, 'r', encoding='utf-8') as f:
            from fastapi.responses import Response
            return Response(content=f.read(), media_type="text/css")
    return {"error": "CSS not found"}


@app.get("/app.js")
async def get_app_js():
    """Serve JavaScript file."""
    js_path = dashboard_dir / "app.js"
    if js_path.exists():
        with open(js_path, 'r', encoding='utf-8') as f:
            from fastapi.responses import Response
            return Response(content=f.read(), media_type="application/javascript")
    return {"error": "JS not found"}


@app.get("/favicon.ico")
async def get_favicon():
    """Serve favicon."""
    favicon_path = Path(__file__).parent.parent / "assets" / "favicon.ico"
    print(f"DEBUG: Looking for favicon at: {favicon_path}")
    print(f"DEBUG: File exists: {favicon_path.exists()}")
    if favicon_path.exists():
        return FileResponse(favicon_path, media_type="image/x-icon")
    return {"error": f"Favicon not found at {favicon_path}"}


@app.get("/api/metrics/current")
async def get_current_metrics() -> Dict[str, Any]:
    """
    Get current session metrics from whatsapp_automation collection.
    """
    if not DB_CONNECTED:
        return {}
    
    try:
        stats = mongo_repo.get_session_stats()
        if stats:
            return {
                "total_contacts": stats.get("total_contacts", 0),
                "phones_found": stats.get("total_phones_found", 0),
                "phones_sent": stats.get("total_phones_sent", 0),
                "success_count": stats.get("success_count", 0),
                "error_count": stats.get("error_count", 0),
                "partial_count": stats.get("partial_count", 0),
            }
        return {}
    except Exception as e:
        print(f"Error fetching current metrics: {e}")
        return {}


@app.get("/api/metrics/history")
async def get_metrics_history(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get contact history (replaces old session history).
    """
    if not DB_CONNECTED:
        return []
    
    try:
        contacts = mongo_repo.get_recent_contacts(limit=limit)
        return [
            {
                "name": c.get("name"),
                "status": c.get("status"),
                "phones_found": c.get("phones_found"),
                "phones_sent": c.get("phones_sent"),
                "timestamp": c.get("timestamp").isoformat() if c.get("timestamp") else None,
            }
            for c in contacts
        ]
    except Exception as e:
        print(f"Error fetching metrics history: {e}")
        return []


@app.get("/api/stats/by-condominio")
async def get_stats_by_condominio() -> List[Dict[str, Any]]:
    """
    Get stats grouped by condominium for comparison.
    """
    if not DB_CONNECTED:
        return []
    
    try:
        return mongo_repo.get_stats_by_condominio()
    except Exception as e:
        print(f"Error fetching stats by condominio: {e}")
        return []


@app.get("/api/funnel")
async def get_funnel_stats() -> Dict[str, int]:
    """
    Get funnel statistics.
    """
    if not DB_CONNECTED:
        return {}
    
    try:
        return mongo_repo.get_funnel_stats()
    except Exception as e:
        print(f"Error fetching funnel stats: {e}")
        return {}


@app.get("/api/stats/daily")
async def get_daily_stats(days: int = 7) -> List[Dict[str, Any]]:
    """
    Get daily message volume stats.
    """
    if not DB_CONNECTED:
        return []
    
    try:
        return mongo_repo.get_daily_stats(days=days)
    except Exception as e:
        print(f"Error fetching daily stats: {e}")
        return []


@app.get("/api/eta")
async def get_eta() -> Dict[str, Any]:
    """
    Get real-time ETA metrics.
    """
    if not DB_CONNECTED:
        return {}
    
    try:
        return mongo_repo.get_realtime_metrics()
    except Exception as e:
        print(f"Error fetching ETA: {e}")
        return {}


@app.get("/api/contacts/recent")
async def get_recent_contacts(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get recent contacts from whatsapp_automation collection.
    """
    if not DB_CONNECTED:
        return []
    
    try:
        contacts = mongo_repo.get_recent_contacts(limit=limit)
        return [
            {
                "name": c.get("name"),
                "status": c.get("status"),
                "phones_found": c.get("phones_found"),
                "phones_sent": c.get("phones_sent"),
                "phones": c.get("phones", []),
                "timestamp": c.get("timestamp").isoformat() if c.get("timestamp") else None,
            }
            for c in contacts
        ]
    except Exception as e:
        print(f"Error fetching contacts: {e}")
        return []


@app.get("/api/logs/recent")
async def get_recent_logs(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get recent logs from logs collection.
    """
    if not DB_CONNECTED:
        return []
    
    try:
        logs = mongo_repo.get_recent_logs(limit=limit)
        return [
            {
                "level": log.get("level"),
                "message": log.get("message"),
                "time": log.get("timestamp").isoformat() if log.get("timestamp") else None,
                "context": log.get("context", {}),
            }
            for log in logs
        ]
    except Exception as e:
        print(f"Error fetching logs: {e}")
        return []


@app.get("/api/stats/summary")
async def get_stats_summary() -> Dict[str, Any]:
    """
    Get aggregate statistics.
    """
    if not DB_CONNECTED:
        return {}
    
    try:
        return mongo_repo.get_session_stats()
    except Exception as e:
        print(f"Error fetching stats summary: {e}")
        return {}


@app.on_event("startup")
async def startup_event():
    """Connect to database on startup."""
    global DB_CONNECTED
    
    try:
        if mongo_repo.connect():
            DB_CONNECTED = True
            print("✅ Dashboard API connected to MongoDB")
        else:
            print("⚠️ Dashboard API failed to connect to MongoDB")
            print("   Dashboard will run without database features")
    except Exception as e:
        print(f"⚠️ Dashboard API failed to connect to database: {e}")
        print("   Dashboard will run without database features")


@app.on_event("shutdown")
async def shutdown_event():
    """Disconnect from database on shutdown."""
    # MongoDB via PyMongo doesn't need explicit disconnect
    print("✅ Dashboard API shutdown complete")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
