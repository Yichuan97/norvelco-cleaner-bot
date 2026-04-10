"""
Staff Configuration — maps Guesty staff IDs to WhatsApp phone numbers.

The old approach mapped 121 listing IDs → cleaner.
The new approach maps Guesty Assignee ID → cleaner phone, because
cleaning tasks are now pulled from the Guesty Tasks view and already
have the assignee set there.

Phone numbers in international format without '+': e.g. 17705272219
"""

# ─── Assignee ID → Cleaner WhatsApp phone ────────────────────────────────────
# These IDs come from the Guesty Tasks API (task.assigneeId field).
# To find a cleaner's ID: look at any task assigned to them in Guesty
# Tasks view, the assigneeId is in the API response.

ASSIGNEE_TO_CLEANER: dict[str, dict] = {
    # TEST MODE: using proxy numbers so real cleaners aren't messaged yet.
    # When ready to go live, replace each phone with the cleaner's real WhatsApp number.
    "6995a59b843d592f55246db5": {"phone": "17706249539", "name": "Alis Sales"},       # → Lui (test)
    "6995a820843d592f552479e3": {"phone": "17706249539", "name": "Cleonice Brito"},   # → Lui (test)
    "6995eb72c44144456218ab1f": {"phone": "17705272219", "name": "Geraldina Quiroz"}, # → Talita (test)
    "6995a6e3c44144456216d6dc": {"phone": "17705272219", "name": "Norelkis Nieves"},  # → Talita (test)
    "699a61055012f3ee4cb37a6a": {"phone": "16789897818", "name": "Vanilza Debora"},   # → Gabi (test)
}

# ─── Listing ID → Unit nickname (for display in task messages) ────────────────
# Used to show "Unit 505" instead of the raw listing ID.

LISTING_TO_NICKNAME: dict[str, str] = {
    # ── 2F ──────────────────────────────────────────────────────────────────
    "689cf0bb62c3e80031c2799f": "Unit 201",
    "680911cc07c94d001969441b": "Unit 202",
    "680911cc07c94d001969442c": "Unit 203",
    "680911cc07c94d001969443d": "Unit 204",
    "6806e3a5617ed000133b6c39": "Unit 205",
    "680914adb42f420012a6147b": "Unit 206",
    "680914adb42f420012a6148b": "Unit 207",
    "680914adb42f420012a6149b": "Unit 208",
    "68028f62ef49fe0011e69b10": "Unit 209",
    "68028f62ef49fe0011e69b18": "Unit 210",
    "680914adb42f420012a614ab": "Unit 212",
    "680914adb42f420012a614bb": "Unit 213",
    "680914adb42f420012a6172b": "Unit 215",
    "680914adb42f420012a614cb": "Unit 216",
    "680914adb42f420012a614db": "Unit 217",
    "680914adb42f420012a614eb": "Unit 218",
    "68028f62ef49fe0011e69b20": "Unit 219",
    "6806e5861703750014984b3d": "Unit 220",
    # ── 3F ──────────────────────────────────────────────────────────────────
    "6806e3a5617ed000133b6c61": "Unit 301",
    "680911cc07c94d001969444e": "Unit 302",
    "680911cc07c94d001969445f": "Unit 303",
    "680911cc07c94d0019694470": "Unit 304",
    "680914adb42f420012a6150b": "Unit 307",
    "680914adb42f420012a6151b": "Unit 308",
    "68028f62ef49fe0011e69b28": "Unit 309",
    "68028f62ef49fe0011e69b30": "Unit 310",
    "6806e5861703750014984bbb": "Unit 311",
    "680914adb42f420012a6152b": "Unit 312",
    "680914adb42f420012a6153b": "Unit 313",
    "680914adb42f420012a6173b": "Unit 315",
    "680911cc07c94d0019694481": "Unit 316",
    "680911cc07c94d0019694492": "Unit 317",
    "680914adb42f420012a6154b": "Unit 318",
    "680914adb42f420012a6155b": "Unit 319",
    "6806a8164511e50013022def": "Unit 320",
    "68028f62ef49fe0011e69b38": "Unit 321",
    "6806e5861703750014984b52": "Unit 322",
    # ── 4F ──────────────────────────────────────────────────────────────────
    "6806e0ca1af74500132c3488": "Unit 401",
    "680911cd07c94d00196944a3": "Unit 402",
    "680911cd07c94d00196944b4": "Unit 403",
    "680911cd07c94d00196944c5": "Unit 404",
    "6806e3a5617ed000133b6c89": "Unit 405",
    "680914adb42f420012a6156b": "Unit 406",
    "680914adb42f420012a6157b": "Unit 407",
    "680914adb42f420012a6158b": "Unit 408",
    "68028f62ef49fe0011e69b40": "Unit 409",
    "68028f62ef49fe0011e69b48": "Unit 410",
    "6806e5861703750014984bd0": "Unit 411",
    "680914adb42f420012a6159b": "Unit 412",
    "680914adb42f420012a615ab": "Unit 413",
    "680914adb42f420012a6174b": "Unit 415",
    "680911cd07c94d00196944d6": "Unit 416",
    "680911cd07c94d00196944e7": "Unit 417",
    "680914adb42f420012a615bb": "Unit 418",
    "680914adb42f420012a615cb": "Unit 419",
    "6806a8164511e50013022e00": "Unit 420",
    "68028f62ef49fe0011e69b50": "Unit 421",
    "6806e5861703750014984b67": "Unit 422",
    # ── 5F ──────────────────────────────────────────────────────────────────
    "68092d5eb79db8002179ec5d": "Unit 501",
    "680911cd07c94d00196944f8": "Unit 502",
    "680911cd07c94d0019694509": "Unit 503",
    "680911cd07c94d001969451a": "Unit 504",
    "6806e3a5617ed000133b6c9d": "Unit 505",
    "680914adb42f420012a615db": "Unit 506",
    "680914adb42f420012a615eb": "Unit 507",
    "680914adb42f420012a615fb": "Unit 508",
    "68028f62ef49fe0011e69b58": "Unit 509",
    "68028f62ef49fe0011e69b60": "Unit 510",
    "6806e5861703750014984be5": "Unit 511",
    "680914adb42f420012a6160b": "Unit 512",
    "680914adb42f420012a6161b": "Unit 513",
    "680914adb42f420012a6175b": "Unit 515",
    "680911cd07c94d001969452b": "Unit 516",
    "680911cd07c94d001969453c": "Unit 517",
    "680914adb42f420012a6162b": "Unit 518",
    "680914adb42f420012a6163b": "Unit 519",
    "6806a8164511e50013022e11": "Unit 520",
    "68028f62ef49fe0011e69b68": "Unit 521",
    "6806e5861703750014984b7c": "Unit 522",
    # ── 6F ──────────────────────────────────────────────────────────────────
    "68092d5eb79db8002179ec78": "Unit 601",
    "680911cd07c94d001969454d": "Unit 602",
    "680911cd07c94d001969455e": "Unit 603",
    "680911cd07c94d001969456f": "Unit 604",
    "6806e3a5617ed000133b6cb1": "Unit 605",
    "680914adb42f420012a6164b": "Unit 606",
    "680914adb42f420012a6165b": "Unit 607",
    "680914adb42f420012a6166b": "Unit 608",
    "68028f62ef49fe0011e69b70": "Unit 609",
    "68028f62ef49fe0011e69b78": "Unit 610",
    "68093d0cb58c67002329ff80": "Unit 611",
    "680914adb42f420012a6167b": "Unit 612",
    "680914adb42f420012a6168b": "Unit 613",
    "680914adb42f420012a6176b": "Unit 615",
    "680911cd07c94d0019694580": "Unit 616",
    "680911cd07c94d0019694591": "Unit 617",
    "680914adb42f420012a6169b": "Unit 618",
    "680914adb42f420012a616ab": "Unit 619",
    "6806a8164511e50013022e22": "Unit 620",
    "68028f62ef49fe0011e69b80": "Unit 621",
    "6806e5861703750014984b91": "Unit 622",
    # ── 7F ──────────────────────────────────────────────────────────────────
    "6806e3a5617ed000133b6cc5": "Unit 701",
    "680911cd07c94d00196945a2": "Unit 702",
    "680911cd07c94d00196945b3": "Unit 703",
    "680911cd07c94d00196945c4": "Unit 704",
    "6806e3a5617ed000133b6cd9": "Unit 705",
    "680914adb42f420012a616bb": "Unit 706",
    "680914adb42f420012a616cb": "Unit 707",
    "680914adb42f420012a616db": "Unit 708",
    "68028f62ef49fe0011e69b88": "Unit 709",
    "68028f62ef49fe0011e69b90": "Unit 710",
    "68093d0cb58c67002329ff9d": "Unit 711",
    "680914adb42f420012a616eb": "Unit 712",
    "680914adb42f420012a616fb": "Unit 713",
    "680914adb42f420012a6177b": "Unit 715",
    "680911cd07c94d00196945d5": "Unit 716",
    "680911cd07c94d00196945e6": "Unit 717",
    "680914adb42f420012a6170b": "Unit 718",
    "680914adb42f420012a6171b": "Unit 719",
    "6806a8164511e50013022e33": "Unit 720",
    "68028f62ef49fe0011e69b98": "Unit 721",
    "6806e5861703750014984ba6": "Unit 722",
}


def get_cleaner_names_by_phone(phone: str) -> list[str]:
    """Return all cleaner names sharing a given phone number (proxy test setup)."""
    return [
        data["name"]
        for data in ASSIGNEE_TO_CLEANER.values()
        if data.get("phone") == phone
    ]


def get_cleaner_phone(assignee_id: str) -> str | None:
    """Return WhatsApp phone for a Guesty assignee ID, or None if not configured."""
    cleaner = ASSIGNEE_TO_CLEANER.get(assignee_id)
    if not cleaner:
        return None
    phone = cleaner["phone"]
    return None if phone.startswith("TODO") else phone


def get_cleaner_name(assignee_id: str) -> str:
    """Return cleaner display name for a Guesty assignee ID."""
    cleaner = ASSIGNEE_TO_CLEANER.get(assignee_id)
    return cleaner["name"] if cleaner else "Cleaner"


def get_listing_nickname(listing_id: str) -> str:
    """Return unit nickname for display (e.g. 'Unit 505')."""
    return LISTING_TO_NICKNAME.get(listing_id, f"Listing {listing_id[:8]}...")
