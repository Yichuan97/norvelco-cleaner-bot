"""
Norvelco Cleaner Bot - Main FastAPI Application
WhatsApp-based staff management for short-term rental properties

Features:
1. Daily prioritized cleaning task dispatch via WhatsApp
2. Bad review warnings before cleaners arrive
3. Photo verification (10 photos required to complete)
4. Good review celebrations sent to cleaners
"""

import os
import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn

from scheduler import start_scheduler
from whatsapp import WhatsAppClient
from guesty import GuestyClient
from task_manager import TaskManager
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background scheduler on app startup."""
    logger.info("🚀 Norvelco Cleaner Bot starting up...")
    scheduler_task = asyncio.create_task(start_scheduler())
    yield
    scheduler_task.cancel()
    logger.info("👋 Norvelco Cleaner Bot shutting down...")


app = FastAPI(
    title="Norvelco Cleaner Bot",
    description="WhatsApp-based cleaning staff management system",
    version="1.0.0",
    lifespan=lifespan
)

# Initialize clients
whatsapp = WhatsAppClient(
    phone_number_id=settings.WHATSAPP_PHONE_NUMBER_ID,
    access_token=settings.WHATSAPP_ACCESS_TOKEN
)
guesty = GuestyClient(
    client_id=settings.GUESTY_CLIENT_ID,
    client_secret=settings.GUESTY_CLIENT_SECRET
)
task_manager = TaskManager(whatsapp=whatsapp, guesty=guesty)


# ─── WhatsApp Webhook ──────────────────────────────────────────────────────────

@app.get("/webhook")
async def verify_webhook(request: Request):
    """WhatsApp webhook verification (GET)."""
    params = dict(request.query_params)
    if (params.get("hub.mode") == "subscribe" and
            params.get("hub.verify_token") == settings.WEBHOOK_VERIFY_TOKEN):
        logger.info("✅ Webhook verified")
        return PlainTextResponse(params["hub.challenge"])
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def receive_message(request: Request):
    """Handle incoming WhatsApp messages."""
    try:
        data = await request.json()
        logger.info(f"📨 Webhook received: {data}")

        # Extract message from WhatsApp payload
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        for msg in messages:
            await task_manager.handle_message(msg)

    except Exception as e:
        logger.error(f"❌ Webhook error: {e}", exc_info=True)

    # Always return 200 to WhatsApp
    return JSONResponse({"status": "ok"})


# ─── Manual Trigger Endpoints ──────────────────────────────────────────────────

@app.post("/trigger/daily-tasks")
async def trigger_daily_tasks():
    """Manually trigger daily task dispatch (for testing)."""
    await task_manager.dispatch_daily_tasks()
    return {"status": "dispatched", "time": datetime.now().isoformat()}


@app.post("/trigger/check-reviews")
async def trigger_check_reviews():
    """Manually trigger bad review check (for testing)."""
    await task_manager.check_and_warn_bad_reviews()
    return {"status": "checked", "time": datetime.now().isoformat()}


@app.post("/trigger/celebrate-reviews")
async def trigger_celebrate_reviews():
    """Manually trigger good review celebrations (for testing)."""
    await task_manager.celebrate_good_reviews()
    return {"status": "celebrated", "time": datetime.now().isoformat()}


# ─── Debug Endpoints ──────────────────────────────────────────────────────────

@app.get("/debug/tasks")
async def debug_tasks():
    """Show raw /v1/tasks response to verify field structure."""
    tasks = await guesty.get_todays_cleaning_tasks()
    return {
        "count": len(tasks),
        "sample": tasks[:2] if tasks else [],
        "all_keys": list(tasks[0].keys()) if tasks else []
    }


# ─── Health Check ─────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "time": datetime.now().isoformat(),
        "version": "1.0.0"
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
