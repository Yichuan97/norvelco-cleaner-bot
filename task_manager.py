"""
Task Manager — core business logic.

Handles:
- Daily task dispatch (8 AM)
- Incoming message routing (photos, completions, replies)
- Before-cleaning photo collection + AI damage detection
- Bad review warnings (7:30 AM)
- Good review celebrations (6 PM)
- Photo counting / task completion verification
"""

import base64
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx

from whatsapp import WhatsAppClient, extract_message_data
from guesty import GuestyClient
from config import settings
from staff_config import get_cleaner_phone, get_cleaner_name, get_listing_nickname, get_cleaner_names_by_phone

logger = logging.getLogger(__name__)

# Simple JSON file storage (replace with Redis/DB for production)
STATE_FILE = Path("task_state.json")


class TaskManager:
    def __init__(self, whatsapp: WhatsAppClient, guesty: GuestyClient):
        self.wa = whatsapp
        self.guesty = guesty
        self._state = self._load_state()

    # ─── State Persistence ─────────────────────────────────────────────────────

    def _load_state(self) -> dict:
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text())
            except Exception:
                pass
        return {
            "tasks": {},
            "photo_counts": {},
            "completed": [],
            "clean_phase": {},   # phone → {phase, before_photos, before_photos_b64}
        }

    def _save_state(self):
        STATE_FILE.write_text(json.dumps(self._state, indent=2, default=str))

    # ─── Daily Task Dispatch ───────────────────────────────────────────────────

    async def dispatch_daily_tasks(self):
        """
        Called at 8 AM every day.
        Fetches today's 'Turnover Cleaning' tasks from the Guesty Tasks view
        and sends each cleaner their task list via WhatsApp, grouped by assignee.
        """
        logger.info("🏠 Dispatching daily cleaning tasks...")

        tasks = await self.guesty.get_todays_cleaning_tasks()
        if not tasks:
            logger.info("No cleaning tasks today, nothing to dispatch.")
            return

        # Group tasks by assignee phone
        cleaner_tasks: dict[str, list] = {}
        unassigned = []
        for task in tasks:
            assignee_id = task.get("assigneeId", "")
            phone = get_cleaner_phone(assignee_id)
            if phone:
                cleaner_tasks.setdefault(phone, []).append(task)
            else:
                unassigned.append(task)

        if unassigned:
            logger.warning(
                f"⚠️  {len(unassigned)} tasks have no cleaner phone configured: "
                + ", ".join(t.get("assigneeFullName", "?") or "Unassigned" for t in unassigned[:5])
            )

        for cleaner_phone, cleaner_task_list in cleaner_tasks.items():
            await self._send_task_list(cleaner_phone, cleaner_task_list)

        logger.info(f"✅ Dispatched tasks to {len(cleaner_tasks)} cleaners")

    async def _send_task_list(self, phone: str, tasks: list[dict]):
        """
        Send today's task list to one cleaner via WhatsApp.
        Splits into chunks of 10. Initializes the before-clean photo phase.
        """
        today = datetime.now().strftime("%A, %B %d")
        CHUNK = 10

        # Store task state
        task_ids = [t.get("_id", "") for t in tasks]
        self._state["tasks"][phone] = {
            "pending": task_ids,
            "tasks_detail": {t.get("_id", ""): t for t in tasks},
            "sent_at": datetime.now().isoformat()
        }

        # Initialize before-clean phase (reset each day at dispatch time)
        self._state.setdefault("clean_phase", {})[phone] = {
            "phase": "before",          # before | cleaning | after
            "before_photos": [],        # WhatsApp media IDs collected so far
            "before_photos_b64": [],    # Corresponding base64-encoded bytes (for AI analysis)
        }
        self._state["photo_counts"].pop(f"{phone}:photo_count", None)  # reset after-photo counter
        self._save_state()

        for chunk_start in range(0, len(tasks), CHUNK):
            chunk = tasks[chunk_start:chunk_start + CHUNK]
            chunk_num = chunk_start // CHUNK + 1
            total_chunks = (len(tasks) + CHUNK - 1) // CHUNK

            if total_chunks > 1:
                header = f"🧹 *Tasks for {today} (Part {chunk_num}/{total_chunks})*\n"
            else:
                header = f"🧹 *Good morning! Here are your tasks for {today}*\n"

            lines = [header]

            for i, task in enumerate(chunk, 1):
                overall_rank = chunk_start + i

                listing_id  = task.get("listingId", "")
                unit_name   = get_listing_nickname(listing_id)
                can_start   = task.get("canStartAfter") or task.get("startTime") or ""
                must_finish = task.get("mustFinishBefore", "")

                checkout_time = self._format_time(can_start)
                deadline_time = self._format_time(must_finish)

                priority_label = "🔴 URGENT" if overall_rank == 1 and len(tasks) > 1 else f"#{overall_rank}"
                lines.append(f"{priority_label} *{unit_name}*")
                lines.append(f"   🚪 Ready after: {checkout_time}")
                if deadline_time:
                    lines.append(f"   ⏰ Finish by: {deadline_time}")
                lines.append("")

            # Only show instructions on the last chunk
            if chunk_start + CHUNK >= len(tasks):
                lines.append(
                    f"📸 *When you arrive at each unit:*\n"
                    f"  1️⃣ Send {settings.REQUIRED_BEFORE_PHOTOS} BEFORE photos to document condition\n"
                    f"  2️⃣ Clean the unit\n"
                    f"  3️⃣ Send DONE [unit] (e.g. DONE 505)\n"
                    f"  4️⃣ Send {settings.REQUIRED_PHOTOS_PER_TASK} AFTER photos to complete\n"
                )

            message = "\n".join(lines)

            try:
                await self.wa.send_text(phone, message)
                logger.info(f"📤 Sent tasks {chunk_start+1}-{chunk_start+len(chunk)} of {len(tasks)} to {phone}")
            except Exception as e:
                logger.error(f"❌ Failed to send task chunk to {phone}: {e}")

    @staticmethod
    def _format_time(iso_str: str) -> str:
        """Parse ISO datetime string → human time like '10:00 AM'. Returns '' if empty."""
        if not iso_str:
            return ""
        try:
            dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
            # Convert UTC → Eastern (approximate: -4 during daylight saving)
            eastern_hour = (dt.hour - 4) % 24
            period = "AM" if eastern_hour < 12 else "PM"
            display_hour = eastern_hour % 12 or 12
            return f"{display_hour}:{dt.minute:02d} {period}"
        except Exception:
            return iso_str[11:16]  # fallback: just "HH:MM"

    # ─── Incoming Message Handler ──────────────────────────────────────────────

    async def handle_message(self, raw_message: dict):
        """Route an incoming WhatsApp message to the right handler."""
        msg = extract_message_data(raw_message)
        phone = msg["from"]
        logger.info(f"📨 Message from {phone}: type={msg['type']}")

        if msg["type"] == "image":
            # Route based on which cleaning phase the cleaner is in
            phase = self._state.get("clean_phase", {}).get(phone, {}).get("phase", "after")
            if phase == "before":
                await self._handle_before_photo(msg)
            else:
                await self._handle_after_photo(msg)

        elif msg["type"] == "text":
            await self._handle_text(msg)

        elif msg["type"] == "interactive":
            await self._handle_button(msg)

    # ─── Before-Clean Photo Collection ────────────────────────────────────────

    async def _handle_before_photo(self, msg: dict):
        """
        Cleaner sent a BEFORE-clean photo.
        Collect until we have enough, then run AI damage analysis.
        """
        phone = msg["from"]
        media_id = msg["image_id"]

        # Acknowledge immediately
        await self.wa.send_reaction(phone, msg["message_id"], "📸")

        # Download the photo bytes right away (URL expires quickly)
        img_bytes = await self._download_whatsapp_image(media_id)

        # Store media ID and bytes
        phase_state = self._state.setdefault("clean_phase", {}).setdefault(phone, {
            "phase": "before", "before_photos": [], "before_photos_b64": []
        })
        phase_state["before_photos"].append(media_id)
        if img_bytes:
            phase_state["before_photos_b64"].append(base64.b64encode(img_bytes).decode())

        count = len(phase_state["before_photos"])
        required = settings.REQUIRED_BEFORE_PHOTOS
        self._save_state()

        if count < required:
            await self.wa.send_text(
                phone,
                f"📷 Before photo {count}/{required} received."
            )
        else:
            # All before photos collected — analyze
            await self.wa.send_text(phone, "⏳ Checking photos for any issues... just a moment.")
            await self._analyze_and_report(phone, phase_state)

            # Move to cleaning phase regardless of outcome
            phase_state["phase"] = "cleaning"
            self._save_state()

    async def _download_whatsapp_image(self, media_id: str) -> Optional[bytes]:
        """Download image bytes from WhatsApp CDN."""
        try:
            url = await self.wa.get_media_url(media_id)
            if url:
                return await self.wa.download_media(url)
        except Exception as e:
            logger.error(f"Failed to download image {media_id}: {e}")
        return None

    async def _analyze_and_report(self, phone: str, phase_state: dict):
        """
        Run AI damage analysis on before-clean photos.
        Notify cleaner and (if damage found) report to property-automation for Lark approval.
        """
        from damage_detector import analyze_photos

        # Decode base64 bytes back to raw bytes
        images = [
            base64.b64decode(b64)
            for b64 in phase_state.get("before_photos_b64", [])
        ]

        if not images:
            await self.wa.send_text(
                phone,
                "⚠️ Couldn't download your before photos for analysis.\n"
                "You can proceed — manager will review when possible."
            )
            return

        result = await analyze_photos(images, settings.ANTHROPIC_API_KEY)
        recommended = result.get("recommended_action", "none")
        description = result.get("description", "")
        severity = result.get("severity", "none")

        if not result.get("has_damage") or recommended == "none":
            await self.wa.send_text(
                phone,
                "✅ *Before photos received!* Unit looks clean — no issues detected.\n\n"
                "Great! Go ahead and start cleaning. 🧹\n"
                "Send *DONE [unit]* when finished, then your after photos."
            )

        elif recommended == "document_and_proceed":
            await self.wa.send_text(
                phone,
                f"📋 *Minor issue noted:* {description}\n\n"
                "Photos have been documented. You can proceed with cleaning. ✅\n"
                "Manager has been notified."
            )
            await self._post_damage_report(phone, result, images)

        else:
            # manager_approval_required
            severity_emoji = "⚠️" if severity == "moderate" else "🚨"
            await self.wa.send_text(
                phone,
                f"{severity_emoji} *Damage detected:*\n{description}\n\n"
                "📋 Manager has been notified and will review shortly.\n"
                "Please *wait for approval* before proceeding with cleaning."
            )
            await self._post_damage_report(phone, result, images)

    async def _post_damage_report(self, phone: str, analysis: dict, images: list[bytes]):
        """POST the damage report to property-automation for Lark manager approval."""
        if not settings.PROPERTY_AUTOMATION_URL:
            logger.warning("PROPERTY_AUTOMATION_URL not configured — skipping damage report")
            return

        # Look up current task for this cleaner
        task_info = self._state.get("tasks", {}).get(phone, {})
        pending_ids = task_info.get("pending", [])
        tasks_detail = task_info.get("tasks_detail", {})
        current_task = tasks_detail.get(pending_ids[0], {}) if pending_ids else {}

        listing_id = current_task.get("listingId", "")
        unit_name = get_listing_nickname(listing_id) if listing_id else "Unknown Unit"
        cleaner_names = get_cleaner_names_by_phone(phone)
        cleaner_name = " / ".join(cleaner_names) if cleaner_names else "Cleaner"

        payload = {
            "api_key": settings.INTERNAL_API_KEY,
            "unit_name": unit_name,
            "listing_id": listing_id,
            "cleaner_name": cleaner_name,
            "cleaner_phone": phone,
            "damage_description": analysis.get("description", ""),
            "damage_categories": analysis.get("categories", []),
            "severity": analysis.get("severity", "unknown"),
            "recommended_action": analysis.get("recommended_action", ""),
            "photos_base64": [base64.b64encode(img).decode() for img in images],
            "reservation_id": current_task.get("reservationId", ""),
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{settings.PROPERTY_AUTOMATION_URL.rstrip('/')}/damage-report",
                    json=payload
                )
                resp.raise_for_status()
                logger.info(f"✅ Damage report sent to ops for {unit_name}")
        except Exception as e:
            logger.error(f"❌ Failed to send damage report to property-automation: {e}")

    # ─── After-Clean Photo Collection ─────────────────────────────────────────

    async def _handle_after_photo(self, msg: dict):
        """
        Cleaner sent an AFTER-clean photo.
        Count it. When they reach the required number, mark task complete.
        """
        phone = msg["from"]

        count_key = f"{phone}:photo_count"
        current_count = self._state["photo_counts"].get(count_key, 0) + 1
        self._state["photo_counts"][count_key] = current_count
        self._save_state()

        await self.wa.send_reaction(phone, msg["message_id"], "📸")

        remaining = settings.REQUIRED_PHOTOS_PER_TASK - current_count

        if remaining > 0:
            if current_count % 3 == 0:  # Only notify every 3 photos to reduce noise
                await self.wa.send_text(
                    phone,
                    f"✅ After photo {current_count}/{settings.REQUIRED_PHOTOS_PER_TASK}. "
                    f"Need {remaining} more."
                )
        else:
            await self._complete_task(phone, current_count)
            # Reset for next unit
            self._state["photo_counts"][count_key] = 0
            # Set phase back to "before" for the next pending task
            if self._state.get("clean_phase", {}).get(phone):
                self._state["clean_phase"][phone] = {
                    "phase": "before",
                    "before_photos": [],
                    "before_photos_b64": [],
                }
            self._save_state()

    async def _complete_task(self, phone: str, photo_count: int):
        """Mark a cleaning task as complete after enough after-clean photos received."""
        await self.wa.send_text(
            phone,
            f"🎉 *Perfect! All {photo_count} after photos received.*\n\n"
            f"✅ This property is marked *COMPLETE*!\n\n"
            f"Great work! If you have more properties today, keep it up! 💪"
        )

        phone_tasks = self._state["tasks"].get(phone, {})
        pending = phone_tasks.get("pending", [])
        if pending:
            completed_id = pending.pop(0)
            self._state["completed"].append({
                "task_id": completed_id,
                "phone": phone,
                "completed_at": datetime.now().isoformat(),
                "photos": photo_count
            })
            self._state["tasks"][phone]["pending"] = pending
            self._save_state()

        logger.info(f"✅ Task completed by {phone} with {photo_count} after-photos")

    # ─── Text Message Handler ──────────────────────────────────────────────────

    async def _handle_text(self, msg: dict):
        """Handle text replies from cleaners."""
        phone = msg["from"]
        text = msg["text"].strip().upper()

        if text.startswith("DONE"):
            # "DONE [property]" — cleaner says they're done cleaning, ready for after photos
            property_hint = msg["text"][4:].strip()

            # Transition phase: cleaning → after
            phase_state = self._state.get("clean_phase", {}).get(phone, {})
            if phase_state.get("phase") in ("before", "cleaning"):
                self._state.setdefault("clean_phase", {})[phone] = {
                    "phase": "after",
                    "before_photos": phase_state.get("before_photos", []),
                    "before_photos_b64": [],  # Don't need these anymore
                }
                self._save_state()

            await self.wa.send_text(
                phone,
                f"👍 Got it! Now send your {settings.REQUIRED_PHOTOS_PER_TASK} "
                f"after photos for *{property_hint or 'this unit'}* to mark it complete. 📸"
            )

        elif text in ("HELP", "?"):
            await self.wa.send_text(
                phone,
                "📋 *How it works:*\n"
                f"1. Arrive → send {settings.REQUIRED_BEFORE_PHOTOS} BEFORE photos\n"
                "2. Clean the unit\n"
                "3. Reply *DONE [unit]* (e.g. DONE 505)\n"
                f"4. Send {settings.REQUIRED_PHOTOS_PER_TASK} AFTER photos to complete\n\n"
                "Reply *TASKS* to see today's list again."
            )

        elif text == "TASKS":
            await self._resend_tasks(phone)

        elif text.startswith("START"):
            # Manually restart before-photo phase for a unit
            unit_hint = msg["text"][5:].strip()
            self._state.setdefault("clean_phase", {})[phone] = {
                "phase": "before",
                "before_photos": [],
                "before_photos_b64": [],
            }
            self._save_state()
            await self.wa.send_text(
                phone,
                f"📸 Ready! Send {settings.REQUIRED_BEFORE_PHOTOS} BEFORE photos "
                f"for *{unit_hint or 'this unit'}* when you arrive."
            )

    async def _handle_button(self, msg: dict):
        """Handle interactive button replies."""
        phone = msg["from"]
        button_id = msg["button_id"]

        if button_id.startswith("confirm_done_"):
            task_id = button_id.replace("confirm_done_", "")
            await self._complete_task(phone, settings.REQUIRED_PHOTOS_PER_TASK)

    async def _resend_tasks(self, phone: str):
        """Resend today's remaining task list to a cleaner."""
        phone_state = self._state["tasks"].get(phone, {})
        pending = phone_state.get("pending", [])
        details = phone_state.get("tasks_detail", {})

        if not pending:
            await self.wa.send_text(phone, "✅ You've completed all your tasks for today! Great job!")
            return

        lines = [f"📋 *Your remaining tasks today ({len(pending)} units):*\n"]
        for i, task_id in enumerate(pending, 1):
            task = details.get(task_id, {})
            listing_id = task.get("listingId", "")
            unit_name = get_listing_nickname(listing_id) if listing_id else task_id
            lines.append(f"{i}. {unit_name}")

        await self.wa.send_text(phone, "\n".join(lines))

    def _get_cleaner_phone(self, task: dict) -> Optional[str]:
        """Get phone for a task's assignee."""
        assignee_id = task.get("assigneeId", "")
        return get_cleaner_phone(assignee_id)

    # ─── Bad Review Warnings ───────────────────────────────────────────────────

    async def check_and_warn_bad_reviews(self):
        """
        Called at 7:30 AM every day.
        Finds listings with recent bad reviews and warns cleaners before they go in.
        """
        logger.info("⚠️  Checking for bad review warnings...")
        bad_reviews = await self.guesty.get_reservations_with_bad_reviews(
            days_back=30,
            min_rating=3.5
        )

        for review in bad_reviews:
            listing_id = review.get("listingId", "")
            listing_name = review.get("listingName", "this property")
            rating = review.get("rating", "?")
            comment = review.get("publicReview", "")[:200] if review.get("publicReview") else ""
            cleaner_phone = self._get_cleaner_phone_by_listing(listing_id)

            if not cleaner_phone:
                continue

            message = (
                f"⚠️ *HEADS UP before you clean {listing_name}!*\n\n"
                f"This property recently received a {rating}★ review.\n"
            )
            if comment:
                message += f"\nGuest said: _{comment}_\n"

            message += (
                f"\nPlease pay *extra attention* to:\n"
                f"• Cleanliness of bathrooms and kitchen\n"
                f"• Stains on linens/towels\n"
                f"• Any damage or maintenance issues\n"
                f"• Report anything unusual\n\n"
                f"We want to turn this around! 💪"
            )

            await self.wa.send_text(cleaner_phone, message)
            logger.info(f"⚠️  Bad review warning sent for {listing_name}")

    def _get_cleaner_phone_by_listing(self, listing_id: str) -> Optional[str]:
        """Get cleaner phone by listing ID (from state — which cleaner is assigned today)."""
        # Look up who is cleaning this unit today
        for phone, task_info in self._state.get("tasks", {}).items():
            details = task_info.get("tasks_detail", {})
            for task in details.values():
                if task.get("listingId") == listing_id:
                    return phone
        return None

    # ─── Good Review Celebrations ──────────────────────────────────────────────

    async def celebrate_good_reviews(self):
        """
        Called at 6 PM every day.
        Finds new 5-star reviews and sends a celebration to the cleaner.
        """
        logger.info("🌟 Checking for good reviews to celebrate...")
        great_reviews = await self.guesty.get_new_5star_reviews(hours_back=24)

        for review in great_reviews:
            listing_name = review.get("listingName", "your property")
            rating = review.get("rating", 5)
            comment = review.get("publicReview", "")[:300] if review.get("publicReview") else ""
            listing_id = review.get("listingId", "")
            cleaner_phone = self._get_cleaner_phone_by_listing(listing_id)

            await self._send_celebration(cleaner_phone, listing_name, rating, comment)

        if not great_reviews:
            logger.info("No new 5-star reviews today.")

    async def _send_celebration(self, cleaner_phone: Optional[str],
                                  listing_name: str, rating: float, comment: str):
        """Send a celebration message for a great review."""
        stars = "⭐" * int(rating)
        message = (
            f"🎊 *AMAZING! You got a {rating}-star review!* {stars}\n\n"
            f"*Property:* {listing_name}\n"
        )
        if comment:
            message += f"\n*Guest said:*\n_{comment}_\n"

        message += (
            f"\n🙌 Your hard work made someone's stay perfect!\n"
            f"Thank you for representing Norvelco so well! 🏆\n\n"
            f"Keep up the incredible work! 💫"
        )

        if cleaner_phone:
            await self.wa.send_text(cleaner_phone, message)
            logger.info(f"🎉 Celebration sent to {cleaner_phone} for {listing_name}")
        else:
            logger.info(f"🌟 5-star review for {listing_name} (no cleaner assigned today)")
