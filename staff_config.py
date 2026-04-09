"""
Staff Configuration — maps Guesty listing IDs to cleaner WhatsApp phone numbers.

Phone numbers in international format without '+': e.g. 7705272219
当前所有 121 个 sub-unit 全部指向 Talita，跑通后逐一替换为各房源专属保洁员。
"""

# Map: Guesty Listing ID → {"phone": ..., "name": ...}
LISTING_TO_CLEANER: dict[str, dict] = {
    # ── 2F (Unit 201–220) ───────────────────────────────────────────────────
    "689cf0bb62c3e80031c2799f": {"phone": "7705272219", "name": "Talita"},  # Unit 201
    "680911cc07c94d001969441b": {"phone": "7705272219", "name": "Talita"},  # Unit 202
    "680911cc07c94d001969442c": {"phone": "7705272219", "name": "Talita"},  # Unit 203
    "680911cc07c94d001969443d": {"phone": "7705272219", "name": "Talita"},  # Unit 204
    "6806e3a5617ed000133b6c39": {"phone": "7705272219", "name": "Talita"},  # Unit 205
    "680914adb42f420012a6147b": {"phone": "7705272219", "name": "Talita"},  # Unit 206
    "680914adb42f420012a6148b": {"phone": "7705272219", "name": "Talita"},  # Unit 207
    "680914adb42f420012a6149b": {"phone": "7705272219", "name": "Talita"},  # Unit 208
    "68028f62ef49fe0011e69b10": {"phone": "7705272219", "name": "Talita"},  # Unit 209
    "68028f62ef49fe0011e69b18": {"phone": "7705272219", "name": "Talita"},  # Unit 210
    "680914adb42f420012a614ab": {"phone": "7705272219", "name": "Talita"},  # Unit 212
    "680914adb42f420012a614bb": {"phone": "7705272219", "name": "Talita"},  # Unit 213
    "680914adb42f420012a6172b": {"phone": "7705272219", "name": "Talita"},  # Unit 215
    "680914adb42f420012a614cb": {"phone": "7705272219", "name": "Talita"},  # Unit 216
    "680914adb42f420012a614db": {"phone": "7705272219", "name": "Talita"},  # Unit 217
    "680914adb42f420012a614eb": {"phone": "7705272219", "name": "Talita"},  # Unit 218
    "68028f62ef49fe0011e69b20": {"phone": "7705272219", "name": "Talita"},  # Unit 219
    "6806e5861703750014984b3d": {"phone": "7705272219", "name": "Talita"},  # Unit 220

    # ── 3F (Unit 301–322) ───────────────────────────────────────────────────
    "6806e3a5617ed000133b6c61": {"phone": "7705272219", "name": "Talita"},  # Unit 301
    "680911cc07c94d001969444e": {"phone": "7705272219", "name": "Talita"},  # Unit 302
    "680911cc07c94d001969445f": {"phone": "7705272219", "name": "Talita"},  # Unit 303
    "680911cc07c94d0019694470": {"phone": "7705272219", "name": "Talita"},  # Unit 304
    "680914adb42f420012a6150b": {"phone": "7705272219", "name": "Talita"},  # Unit 307
    "680914adb42f420012a6151b": {"phone": "7705272219", "name": "Talita"},  # Unit 308
    "68028f62ef49fe0011e69b28": {"phone": "7705272219", "name": "Talita"},  # Unit 309
    "68028f62ef49fe0011e69b30": {"phone": "7705272219", "name": "Talita"},  # Unit 310
    "6806e5861703750014984bbb": {"phone": "7705272219", "name": "Talita"},  # Unit 311
    "680914adb42f420012a6152b": {"phone": "7705272219", "name": "Talita"},  # Unit 312
    "680914adb42f420012a6153b": {"phone": "7705272219", "name": "Talita"},  # Unit 313
    "680914adb42f420012a6173b": {"phone": "7705272219", "name": "Talita"},  # Unit 315
    "680911cc07c94d0019694481": {"phone": "7705272219", "name": "Talita"},  # Unit 316
    "680911cc07c94d0019694492": {"phone": "7705272219", "name": "Talita"},  # Unit 317
    "680914adb42f420012a6154b": {"phone": "7705272219", "name": "Talita"},  # Unit 318
    "680914adb42f420012a6155b": {"phone": "7705272219", "name": "Talita"},  # Unit 319
    "6806a8164511e50013022def": {"phone": "7705272219", "name": "Talita"},  # Unit 320
    "68028f62ef49fe0011e69b38": {"phone": "7705272219", "name": "Talita"},  # Unit 321
    "6806e5861703750014984b52": {"phone": "7705272219", "name": "Talita"},  # Unit 322

    # ── 4F (Unit 401–422) ───────────────────────────────────────────────────
    "6806e0ca1af74500132c3488": {"phone": "7705272219", "name": "Talita"},  # Unit 401
    "680911cd07c94d00196944a3": {"phone": "7705272219", "name": "Talita"},  # Unit 402
    "680911cd07c94d00196944b4": {"phone": "7705272219", "name": "Talita"},  # Unit 403
    "680911cd07c94d00196944c5": {"phone": "7705272219", "name": "Talita"},  # Unit 404
    "6806e3a5617ed000133b6c89": {"phone": "7705272219", "name": "Talita"},  # Unit 405
    "680914adb42f420012a6156b": {"phone": "7705272219", "name": "Talita"},  # Unit 406
    "680914adb42f420012a6157b": {"phone": "7705272219", "name": "Talita"},  # Unit 407
    "680914adb42f420012a6158b": {"phone": "7705272219", "name": "Talita"},  # Unit 408
    "68028f62ef49fe0011e69b40": {"phone": "7705272219", "name": "Talita"},  # Unit 409
    "68028f62ef49fe0011e69b48": {"phone": "7705272219", "name": "Talita"},  # Unit 410
    "6806e5861703750014984bd0": {"phone": "7705272219", "name": "Talita"},  # Unit 411
    "680914adb42f420012a6159b": {"phone": "7705272219", "name": "Talita"},  # Unit 412
    "680914adb42f420012a615ab": {"phone": "7705272219", "name": "Talita"},  # Unit 413
    "680914adb42f420012a6174b": {"phone": "7705272219", "name": "Talita"},  # Unit 415
    "680911cd07c94d00196944d6": {"phone": "7705272219", "name": "Talita"},  # Unit 416
    "680911cd07c94d00196944e7": {"phone": "7705272219", "name": "Talita"},  # Unit 417
    "680914adb42f420012a615bb": {"phone": "7705272219", "name": "Talita"},  # Unit 418
    "680914adb42f420012a615cb": {"phone": "7705272219", "name": "Talita"},  # Unit 419
    "6806a8164511e50013022e00": {"phone": "7705272219", "name": "Talita"},  # Unit 420
    "68028f62ef49fe0011e69b50": {"phone": "7705272219", "name": "Talita"},  # Unit 421
    "6806e5861703750014984b67": {"phone": "7705272219", "name": "Talita"},  # Unit 422

    # ── 5F (Unit 501–522) ───────────────────────────────────────────────────
    "68092d5eb79db8002179ec5d": {"phone": "7705272219", "name": "Talita"},  # Unit 501
    "680911cd07c94d00196944f8": {"phone": "7705272219", "name": "Talita"},  # Unit 502
    "680911cd07c94d0019694509": {"phone": "7705272219", "name": "Talita"},  # Unit 503
    "680911cd07c94d001969451a": {"phone": "7705272219", "name": "Talita"},  # Unit 504
    "6806e3a5617ed000133b6c9d": {"phone": "7705272219", "name": "Talita"},  # Unit 505
    "680914adb42f420012a615db": {"phone": "7705272219", "name": "Talita"},  # Unit 506
    "680914adb42f420012a615eb": {"phone": "7705272219", "name": "Talita"},  # Unit 507
    "680914adb42f420012a615fb": {"phone": "7705272219", "name": "Talita"},  # Unit 508
    "68028f62ef49fe0011e69b58": {"phone": "7705272219", "name": "Talita"},  # Unit 509
    "68028f62ef49fe0011e69b60": {"phone": "7705272219", "name": "Talita"},  # Unit 510
    "6806e5861703750014984be5": {"phone": "7705272219", "name": "Talita"},  # Unit 511
    "680914adb42f420012a6160b": {"phone": "7705272219", "name": "Talita"},  # Unit 512
    "680914adb42f420012a6161b": {"phone": "7705272219", "name": "Talita"},  # Unit 513
    "680914adb42f420012a6175b": {"phone": "7705272219", "name": "Talita"},  # Unit 515
    "680911cd07c94d001969452b": {"phone": "7705272219", "name": "Talita"},  # Unit 516
    "680911cd07c94d001969453c": {"phone": "7705272219", "name": "Talita"},  # Unit 517
    "680914adb42f420012a6162b": {"phone": "7705272219", "name": "Talita"},  # Unit 518
    "680914adb42f420012a6163b": {"phone": "7705272219", "name": "Talita"},  # Unit 519
    "6806a8164511e50013022e11": {"phone": "7705272219", "name": "Talita"},  # Unit 520
    "68028f62ef49fe0011e69b68": {"phone": "7705272219", "name": "Talita"},  # Unit 521
    "6806e5861703750014984b7c": {"phone": "7705272219", "name": "Talita"},  # Unit 522

    # ── 6F (Unit 601–622) ───────────────────────────────────────────────────
    "68092d5eb79db8002179ec78": {"phone": "7705272219", "name": "Talita"},  # Unit 601
    "680911cd07c94d001969454d": {"phone": "7705272219", "name": "Talita"},  # Unit 602
    "680911cd07c94d001969455e": {"phone": "7705272219", "name": "Talita"},  # Unit 603
    "680911cd07c94d001969456f": {"phone": "7705272219", "name": "Talita"},  # Unit 604
    "6806e3a5617ed000133b6cb1": {"phone": "7705272219", "name": "Talita"},  # Unit 605
    "680914adb42f420012a6164b": {"phone": "7705272219", "name": "Talita"},  # Unit 606
    "680914adb42f420012a6165b": {"phone": "7705272219", "name": "Talita"},  # Unit 607
    "680914adb42f420012a6166b": {"phone": "7705272219", "name": "Talita"},  # Unit 608
    "68028f62ef49fe0011e69b70": {"phone": "7705272219", "name": "Talita"},  # Unit 609
    "68028f62ef49fe0011e69b78": {"phone": "7705272219", "name": "Talita"},  # Unit 610
    "68093d0cb58c67002329ff80": {"phone": "7705272219", "name": "Talita"},  # Unit 611
    "680914adb42f420012a6167b": {"phone": "7705272219", "name": "Talita"},  # Unit 612
    "680914adb42f420012a6168b": {"phone": "7705272219", "name": "Talita"},  # Unit 613
    "680914adb42f420012a6176b": {"phone": "7705272219", "name": "Talita"},  # Unit 615
    "680911cd07c94d0019694580": {"phone": "7705272219", "name": "Talita"},  # Unit 616
    "680911cd07c94d0019694591": {"phone": "7705272219", "name": "Talita"},  # Unit 617
    "680914adb42f420012a6169b": {"phone": "7705272219", "name": "Talita"},  # Unit 618
    "680914adb42f420012a616ab": {"phone": "7705272219", "name": "Talita"},  # Unit 619
    "6806a8164511e50013022e22": {"phone": "7705272219", "name": "Talita"},  # Unit 620
    "68028f62ef49fe0011e69b80": {"phone": "7705272219", "name": "Talita"},  # Unit 621
    "6806e5861703750014984b91": {"phone": "7705272219", "name": "Talita"},  # Unit 622

    # ── 7F (Unit 701–722) ───────────────────────────────────────────────────
    "6806e3a5617ed000133b6cc5": {"phone": "7705272219", "name": "Talita"},  # Unit 701
    "680911cd07c94d00196945a2": {"phone": "7705272219", "name": "Talita"},  # Unit 702
    "680911cd07c94d00196945b3": {"phone": "7705272219", "name": "Talita"},  # Unit 703
    "680911cd07c94d00196945c4": {"phone": "7705272219", "name": "Talita"},  # Unit 704
    "6806e3a5617ed000133b6cd9": {"phone": "7705272219", "name": "Talita"},  # Unit 705
    "680914adb42f420012a616bb": {"phone": "7705272219", "name": "Talita"},  # Unit 706
    "680914adb42f420012a616cb": {"phone": "7705272219", "name": "Talita"},  # Unit 707
    "680914adb42f420012a616db": {"phone": "7705272219", "name": "Talita"},  # Unit 708
    "68028f62ef49fe0011e69b88": {"phone": "7705272219", "name": "Talita"},  # Unit 709
    "68028f62ef49fe0011e69b90": {"phone": "7705272219", "name": "Talita"},  # Unit 710
    "68093d0cb58c67002329ff9d": {"phone": "7705272219", "name": "Talita"},  # Unit 711
    "680914adb42f420012a616eb": {"phone": "7705272219", "name": "Talita"},  # Unit 712
    "680914adb42f420012a616fb": {"phone": "7705272219", "name": "Talita"},  # Unit 713
    "680914adb42f420012a6177b": {"phone": "7705272219", "name": "Talita"},  # Unit 715
    "680911cd07c94d00196945d5": {"phone": "7705272219", "name": "Talita"},  # Unit 716
    "680911cd07c94d00196945e6": {"phone": "7705272219", "name": "Talita"},  # Unit 717
    "680914adb42f420012a6170b": {"phone": "7705272219", "name": "Talita"},  # Unit 718
    "680914adb42f420012a6171b": {"phone": "7705272219", "name": "Talita"},  # Unit 719
    "6806a8164511e50013022e33": {"phone": "7705272219", "name": "Talita"},  # Unit 720
    "68028f62ef49fe0011e69b98": {"phone": "7705272219", "name": "Talita"},  # Unit 721
    "6806e5861703750014984ba6": {"phone": "7705272219", "name": "Talita"},  # Unit 722
}


def get_cleaner_phone(listing_id: str) -> str | None:
    """返回房源对应保洁员的 WhatsApp 号码，找不到返回 None"""
    cleaner = LISTING_TO_CLEANER.get(listing_id)
    return cleaner["phone"] if cleaner else None


def get_cleaner_name(listing_id: str) -> str:
    """返回房源对应保洁员的姓名，找不到返回 'Cleaner'"""
    cleaner = LISTING_TO_CLEANER.get(listing_id)
    return cleaner["name"] if cleaner else "Cleaner"
