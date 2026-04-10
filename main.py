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


# ─── Test Endpoints ───────────────────────────────────────────────────────────

@app.post("/test/set-before-phase")
async def test_set_before_phase(request: Request):
    """
    TEST ONLY — Bypass Guesty and put a phone number directly into 'before' phase
    so the cleaner can immediately send before-photos to test the AI damage detection flow.

    Body (JSON):
      { "phone": "7706249539", "unit": "Unit 505" }

    'phone' is required. 'unit' defaults to 'Unit 505 (TEST)'.
    """
    body = await request.json()
    phone = body.get("phone", "").strip()
    unit_name = body.get("unit", "Unit 505 (TEST)")

    if not phone:
        raise HTTPException(status_code=400, detail="'phone' is required")

    # Inject a fake task into state so _post_damage_report has something to reference
    fake_task_id = "test-task-001"
    task_manager._state.setdefault("tasks", {})[phone] = {
        "pending": [fake_task_id],
        "tasks_detail": {
            fake_task_id: {
                "_id": fake_task_id,
                "listingId": "",
                "listingName": unit_name,
                "title": "Turnover Cleaning TEST",
                "canStartAfter": datetime.now().isoformat(),
                "mustFinishBefore": "",
                "assigneeId": "",
                "reservationId": "",
            }
        },
        "sent_at": datetime.now().isoformat(),
    }

    # Set clean_phase to 'before'
    task_manager._state.setdefault("clean_phase", {})[phone] = {
        "phase": "before",
        "before_photos": [],
        "before_photos_b64": [],
    }
    task_manager._state["photo_counts"].pop(f"{phone}:photo_count", None)
    task_manager._save_state()

    # Normalise phone to E.164 — this must match what WhatsApp sends in webhook 'from' field
    wa_phone = phone if len(phone) >= 11 else f"1{phone}"

    # Inject a fake task using the normalised phone as key (must match webhook 'from')
    fake_task_id = "test-task-001"
    task_manager._state.setdefault("tasks", {})[wa_phone] = {
        "pending": [fake_task_id],
        "tasks_detail": {
            fake_task_id: {
                "_id": fake_task_id,
                "listingId": "",
                "listingName": unit_name,
                "title": "Turnover Cleaning TEST",
                "canStartAfter": datetime.now().isoformat(),
                "mustFinishBefore": "",
                "assigneeId": "",
                "reservationId": "",
            }
        },
        "sent_at": datetime.now().isoformat(),
    }
    task_manager._state.setdefault("clean_phase", {})[wa_phone] = {
        "phase": "before",
        "before_photos": [],
        "before_photos_b64": [],
    }
    task_manager._state["photo_counts"].pop(f"{wa_phone}:photo_count", None)
    task_manager._save_state()

    required = settings.REQUIRED_BEFORE_PHOTOS

    # Try sending — capture full WhatsApp error body if it fails
    wa_status = "sent"
    wa_error = None
    try:
        await whatsapp.send_text(
            wa_phone,
            f"🧪 *[TEST MODE]* Unit: *{unit_name}*\n\n"
            f"📸 Please send {required} BEFORE photo(s) to test the damage detection system.\n\n"
            f"Tip: try a photo with visible damage (scratch, stain, broken item) to see what the AI flags!"
        )
    except Exception as e:
        wa_status = "failed"
        # Capture full response body from WhatsApp so we can diagnose
        wa_error = str(e)
        if hasattr(e, "response"):
            try:
                wa_error = e.response.text
            except Exception:
                pass
        logger.error(f"❌ Test WhatsApp send failed: {wa_error}")

    logger.info(f"🧪 Test: {wa_phone} set to before-phase for unit '{unit_name}'. WA: {wa_status}")
    return {
        "status": "ok",
        "wa_phone": wa_phone,
        "unit": unit_name,
        "phase": "before",
        "required_before_photos": required,
        "whatsapp": wa_status,
        "whatsapp_error": wa_error,
        "next_step": f"If WA failed, check whatsapp_error for details. Otherwise send {required} before photos to the bot."
    }


# ─── Debug Endpoints ──────────────────────────────────────────────────────────

@app.get("/debug/tasks")
async def debug_tasks():
    """Show raw /v1/tasks response to verify field structure."""
    import httpx
    try:
        token = await guesty._get_access_token()
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                "https://open-api.guesty.com/v1/tasks",
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                params={"limit": 3}
            )
            raw = resp.json()
        return {
            "status_code": resp.status_code,
            "top_level_keys": list(raw.keys()) if isinstance(raw, dict) else f"list of {len(raw)}",
            "raw": raw
        }
    except Exception as e:
        return {"error": str(e)}


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
