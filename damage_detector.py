"""
AI-powered damage detection for before-cleaning photos.
Uses Claude claude-haiku-4-5 (multimodal vision) via the Anthropic API.

Called by task_manager when a cleaner submits their BEFORE photos.
Returns a structured damage assessment.
"""

import base64
import json
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"

ANALYSIS_PROMPT = """You are a property damage inspector for a short-term rental company.

Analyze these photos taken BEFORE cleaning to document the unit's condition.

Look carefully for:
- Stains on carpets, furniture, bedding, walls, or floors
- Broken or damaged furniture, fixtures, or appliances
- Signs of smoking (cigarette butts, ash, burn marks, weed/marijuana paraphernalia)
- Excessive dirt or mess beyond normal guest use
- Wall damage (holes, scuffs, large marks, graffiti)
- Biohazard or bodily fluid issues
- Missing items that should be there

Respond ONLY with a JSON object (no markdown, no extra text) in this exact format:
{
  "has_damage": true,
  "severity": "moderate",
  "categories": ["stains", "broken_items"],
  "description": "Brown stain on living room carpet. Broken lamp by bed.",
  "recommended_action": "manager_approval_required"
}

Rules for severity and recommended_action:
- No damage found → has_damage: false, severity: "none", recommended_action: "none"
- Minor issues (small stain, normal mess) → severity: "minor", recommended_action: "document_and_proceed"
- Significant damage (broken items, large stains, smoke damage) → severity: "moderate", recommended_action: "manager_approval_required"
- Severe damage (structural, biohazard, flooding) → severity: "severe", recommended_action: "manager_approval_required"

Valid categories: stains, broken_items, cigarette_smoke, weed_paraphernalia, wall_damage,
furniture_damage, excessive_dirt, biohazard, missing_items, other
"""


async def analyze_photos(image_bytes_list: list[bytes], api_key: str) -> dict:
    """
    Analyze a list of before-cleaning photos for damage using Claude vision.

    Args:
        image_bytes_list: List of raw image bytes (JPEG or PNG)
        api_key: Anthropic API key

    Returns:
        {
            "has_damage": bool,
            "severity": "none" | "minor" | "moderate" | "severe",
            "categories": list[str],
            "description": str,
            "recommended_action": "none" | "document_and_proceed" | "manager_approval_required"
        }
    """
    if not api_key:
        logger.warning("No Anthropic API key — skipping damage analysis")
        return _no_damage_result("No API key configured")

    if not image_bytes_list:
        return _no_damage_result("No photos to analyze")

    # Build content: up to 5 images + analysis prompt
    content = []
    for img_bytes in image_bytes_list[:5]:
        b64 = base64.standard_b64encode(img_bytes).decode("utf-8")
        # Detect image format (JPEG vs PNG)
        media_type = "image/jpeg"
        if img_bytes[:4] == b"\x89PNG":
            media_type = "image/png"

        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": b64,
            }
        })

    content.append({
        "type": "text",
        "text": ANALYSIS_PROMPT
    })

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                ANTHROPIC_API_URL,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 512,
                    "messages": [{"role": "user", "content": content}]
                }
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["content"][0]["text"].strip()

            # Strip any markdown fences if Claude added them
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()

            result = json.loads(text)
            logger.info(f"🔍 Damage analysis result: severity={result.get('severity')}, "
                        f"damage={result.get('has_damage')}, categories={result.get('categories')}")
            return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        return _error_result("AI response could not be parsed — review photos manually")
    except httpx.HTTPStatusError as e:
        logger.error(f"Anthropic API error {e.response.status_code}: {e.response.text[:200]}")
        return _error_result(f"AI service error ({e.response.status_code})")
    except Exception as e:
        logger.error(f"❌ Damage analysis failed: {e}")
        return _error_result(str(e))


def _no_damage_result(reason: str = "") -> dict:
    return {
        "has_damage": False,
        "severity": "none",
        "categories": [],
        "description": reason or "No damage detected",
        "recommended_action": "none"
    }


def _error_result(reason: str) -> dict:
    """Used when analysis fails — default to document_and_proceed so cleaner isn't blocked."""
    return {
        "has_damage": False,
        "severity": "none",
        "categories": [],
        "description": f"Analysis error: {reason}",
        "recommended_action": "document_and_proceed"
    }
