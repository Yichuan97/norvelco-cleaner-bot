"""
Task Manager — core business logic.

Handles:
- Daily task dispatch
- Incoming message routing (photos, completions, replies)
- Bad review warnings
- Good review celebrations
- Photo counting / task completion
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from whatsapp import WhatsAppClient, extract_message_data
from guesty import GuestyClient, prioritize_cleaning_tasks
from config import settings
from staff_config import get_cleaner_phone, get_cleaner_name

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
        return {"tasks": {}, "photo_counts": {}, "completed": []}

    def _save_state(self):
        STATE_FILE.write_text(json.dumps(self._state, indent=2, default=str))

    # ─── Daily Task Dispatch ───────────────────────────────────────────────────

    async def dispatch_daily_tasks(self):
        """
        Called at 8 AM every day.
        Fetches today's checkouts from Guesty, prioritizes them,
        and sends each cleaner their task list via WhatsApp.
        """
        logger.info("🏠 Dispatching daily cleaning tasks...")

        checkouts = await self.guesty.get_today_checkouts()
        if not checkouts:
            logger.info("No checkouts today, nothing to dispatch.")
            return

        sorted_tasks = prioritize_cleaning_tasks(checkouts)

        # Group by assigned cleaner (Guesty listing → cleaner phone)
        cleaner_tasks: dict[str, list] = {}
        for task in sorted_tasks:
            phone = self._get_cleaner_phone(task)
            if phone:
                cleaner_tasks.setdefault(phone, []).append(task)

        for cleaner_phone, tasks in cleaner_tasks.items():
            await self._send_task_list(cleaner_phone, tasks)

        logger.info(f"✅ Dispatched tasks to {len(cleaner_tasks)} cleaners")

    async def _send_task_list(self, phone: str, tasks: list[dict]):
        """Send a prioritized task list to one cleaner."""
        today = datetime.now().strftime("%A, %B %d")
        lines = [f"🧹 *Good morning! Here are your tasks for {today}*\n"]

        for i, task in enumerate(tasks, 1):
            listing_name = task.get("listing", {}).get("name", "Property")
            checkout_time = task.get("checkOut", "")[-8:-3] or "TBD"
            checkin_time = task.get("checkIn", "")[-8:-3]
            address = task.get("listing", {}).get("address", {}).get("full", "")

            priority = "🔴 URGENT" if i == 1 and len(tasks) > 1 else f"#{i}"
            lines.append(f"{priority} *{listing_name}*")
            lines.append(f"   📍 {address}")
            lines.append(f"   🚪 Checkout: {checkout_time}")
            if checkin_time:
                lines.append(f"   🛎  Next guest: {checkin_time}")
            lines.append("")

        lines.append(
            f"📸 *Remember: Send {settings.REQUIRED_PHOTOS_PER_TASK} photos "
            f"(before + after) for each property to mark it complete.*"
        )
        lines.append("\nReply 'DONE [property name]' when finished with each one.")

        message = "\n".join(lines)

        # Store pending tasks for this cleaner
        task_ids = [t.get("_id", "") for t in tasks]
        self._state["tasks"][phone] = {
            "pending": task_ids,
            "tasks_detail": {t.get("_id", ""): t for t in tasks},
            "sent_at": datetime.now().isoformat()
        }
        self._save_state()

        await self.wa.send_text(phone, message)
        logger.info(f"📤 Sent {len(tasks)} tasks to {phone}")

    # ─── Incoming Message Handler ──────────────────────────────────────────────

    async def handle_message(self, raw_message: dict):
        """Route an incoming WhatsApp message to the right handler."""
        msg = extract_message_data(raw_message)
        logger.info(f"📨 Message from {msg['from']}: type={msg['type']}")

        if msg["type"] == "image":
            await self._handle_photo(msg)
        elif msg["type"] == "text":
            await self._handle_text(msg)
        elif msg["type"] == "interactive":
            await self._handle_button(msg)

    async def _handle_photo(self, msg: dict):
        """
        Cleaner sent a photo.
        Count it. When they reach the required number, mark task complete.
        """
        phone = msg["from"]
        image_id = msg["image_id"]
        caption = msg["image_caption"].lower()

        # Determine which property this photo belongs to
        # (cleaner can include property name in caption, or we track by session)
        task_key = f"{phone}:current"
        count_key = f"{phone}:photo_count"

        current_count = self._state["photo_counts"].get(count_key, 0) + 1
        self._state["photo_counts"][count_key] = current_count
        self._save_state()

        # React with a camera emoji to acknowledge the photo
        await self.wa.send_reaction(phone, msg["message_id"], "📸")

        remaining = settings.REQUIRED_PHOTOS_PER_TASK - current_count

        if remaining > 0:
            if current_count % 3 == 0:  # Only notify every 3 photos
                await self.wa.send_text(
                    phone,
                    f"✅ Photo {current_count}/{settings.REQUIRED_PHOTOS_PER_TASK} received! "
                    f"Need {remaining} more to complete."
                )
        else:
            # All photos received — mark task complete!
            await self._complete_task(phone, current_count)
            # Reset counter for next property
            self._state["photo_counts"][count_key] = 0
            self._save_state()

    async def _complete_task(self, phone: str, photo_count: int):
        """Mark a cleaning task as complete after enough photos received."""
        await self.wa.send_text(
            phone,
            f"🎉 *Perfect! All {photo_count} photos received.*\n\n"
            f"✅ This property is marked COMPLETE!\n\n"
            f"Great work! If you have more properties today, "
            f"keep it up! 💪"
        )
        # Update state
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
        logger.info(f"✅ Task completed by {phone} with {photo_count} photos")

    async def _handle_text(self, msg: dict):
        """Handle text replies from cleaners."""
        phone = msg["from"]
        text = msg["text"].strip().upper()

        if text.startswith("DONE"):
            # "DONE [property name]" — cleaner says they're done
            property_hint = msg["text"][4:].strip()
            await self.wa.send_text(
                phone,
                f"👍 Got it! Please send your {settings.REQUIRED_PHOTOS_PER_TASK} "
                f"before/after photos for {property_hint or 'this property'} "
                f"to officially mark it complete."
            )
        elif text in ("HELP", "?"):
            await self.wa.send_text(
                phone,
                "📋 *Commands:*\n"
                "• Send photos to log your cleaning progress\n"
                f"• Need {settings.REQUIRED_PHOTOS_PER_TASK} photos per property to complete\n"
                "• Reply DONE [property] when you're finished\n"
                "• Reply TASKS to see today's list again"
            )
        elif text == "TASKS":
            await self._resend_tasks(phone)

    async def _handle_button(self, msg: dict):
        """Handle interactive button replies."""
        phone = msg["from"]
        button_id = msg["button_id"]

        if button_id.startswith("confirm_done_"):
            task_id = button_id.replace("confirm_done_", "")
            await self._complete_task(phone, settings.REQUIRED_PHOTOS_PER_TASK)

    async def _resend_tasks(self, phone: str):
        """Resend today's task list to a cleaner."""
        phone_state = self._state["tasks"].get(phone, {})
        pending = phone_state.get("pending", [])
        details = phone_state.get("tasks_detail", {})

        if not pending:
            await self.wa.send_text(phone, "✅ You've completed all your tasks for today! Great job!")
            return

        lines = [f"📋 *Your remaining tasks today ({len(pending)} properties):*\n"]
        for task_id in pending:
            task = details.get(task_id, {})
            name = task.get("listing", {}).get("name", task_id)
            lines.append(f"• {name}")

        await self.wa.send_text(phone, "\n".join(lines))

    def _get_cleaner_phone(self, task: dict) -> Optional[str]:
        """
        Map a reservation/listing to the assigned cleaner's WhatsApp number.
        Looks up staff_config.py first, then falls back to Guesty custom fields.
        """
        listing_id = task.get("listing", {}).get("_id", "") or task.get("listingId", "")

        # Primary: staff_config.py lookup
        phone = get_cleaner_phone(listing_id)
        if phone:
            return phone

        # Fallback: Guesty custom fields
        custom_fields = task.get("listing", {}).get("customFields", [])
        for field in custom_fields:
            if field.get("fieldId", "").lower() in ("cleaner_phone", "cleaner_whatsapp"):
                return field.get("value")

        return None

    # ─── Bad Review Warnings ───────────────────────────────────────────────────

    async def check_and_warn_bad_reviews(self):
        """
        Called at 7:30 AM every day.
        Finds listings with recent bad reviews and warns cleaners
        BEFORE they go in, so they pay extra attention.
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
                f"• Report anything unusual immediately\n\n"
                f"We want to turn this around! 💪"
            )

            await self.wa.send_text(cleaner_phone, message)
            logger.info(f"⚠️  Bad review warning sent for {listing_name}")

    def _get_cleaner_phone_by_listing(self, listing_id: str) -> Optional[str]:
        """Get cleaner phone by listing ID."""
        return get_cleaner_phone(listing_id)

    # ─── Good Review Celebrations ──────────────────────────────────────────────

    async def celebrate_good_reviews(self):
        """
        Called at 6 PM every day.
        Finds new 5-star reviews and celebrates with the responsible cleaner.
        """
        logger.info("🌟 Checking for good reviews to celebrate...")
        great_reviews = await self.guesty.get_new_5star_reviews(hours_back=24)

        for review in great_reviews:
            listing_name = review.get("listingName", "your property")
            rating = review.get("rating", 5)
            comment = review.get("publicReview", "")[:300] if review.get("publicReview") else ""
            listing_id = review.get("listingId", "")
            cleaner_phone = self._get_cleaner_phone_by_listing(listing_id)

            # Also notify manager (from config)
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
            logger.info(f"🌟 5-star review for {listing_name} (no cleaner phone on file)")
