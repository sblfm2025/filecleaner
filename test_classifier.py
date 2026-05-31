"""
Test suite untuk audio_classifier.py v3.0
Menjalankan semua kasus uji yang diminta dalam spesifikasi.
"""
from src.audio_classifier import classify_audio_file

PASS = 0
FAIL = 0

def test(label, result, expected_decision, expected_folder_contains=None, expected_conflict=None):
    global PASS, FAIL
    ok = True
    notes = []

    if result["decision"] != expected_decision:
        ok = False
        notes.append(f"decision={result['decision']} (expected {expected_decision})")

    if expected_folder_contains:
        folder = result.get("target_folder", "") + "|" + result.get("review_folder", "")
        if expected_folder_contains.lower() not in folder.lower():
            ok = False
            notes.append(f"folder tidak mengandung '{expected_folder_contains}' -> target={result['target_folder']} review={result['review_folder']}")

    if expected_conflict:
        if expected_conflict not in result.get("conflicts", []):
            ok = False
            notes.append(f"konflik '{expected_conflict}' tidak ditemukan di {result['conflicts']}")

    status = "PASS" if ok else "FAIL"
    if not ok:
        FAIL += 1
    else:
        PASS += 1

    print(f"{status} [{label}]")
    print(f"       Score={result['confidence_score']:>3} | Decision={result['decision']:<25} | target={result['target_folder']}")
    if not ok:
        for n in notes:
            print(f"       NOTE: {n}")
    if result.get("conflicts"):
        print(f"       Conflicts: {result['conflicts']}")
    print()


print("=" * 90)
print("  AUDIO CLASSIFIER v3.0 — TEST SUITE")
print("=" * 90)
print()

# ── TEST 1: Jingle jelas dengan prefix resmi ─────────────────────
r = classify_audio_file("JINGLE - Radio SBL Pagi Ceria - 15s.mp3", duration_seconds=15)
test("JINGLE_PREFIX_CLEAR", r, "AUTO_SORT", "JINGLES")

# ── TEST 2: IKLAN dengan durasi normal ───────────────────────────
r = classify_audio_file("IKLAN - Toko ABC Promo Akhir Tahun.mp3", duration_seconds=30)
test("IKLAN_NORMAL_DURATION", r, "AUTO_SORT", "COMMERCIAL_ADS")

# ── TEST 3: IKLAN dengan durasi aneh (5 menit) ───────────────────
r = classify_audio_file("IKLAN - Promo Toko ABC.mp3", duration_seconds=270)
test("IKLAN_DURATION_CONFLICT", r, "REVIEW_WITH_SUGGESTION", "DURATION_ANOMALY", "DURATION_CATEGORY_CONFLICT")

# ── TEST 4: ILM/PSA ──────────────────────────────────────────────
r = classify_audio_file("ILM - Cegah DBD Dinkes Pinrang.mp3", duration_seconds=60)
test("ILM_PREFIX_PSA", r, "AUTO_SORT", "PUBLIC_SERVICE_ANNOUNCEMENT")

# ── TEST 5: BUMPER radio ─────────────────────────────────────────
r = classify_audio_file("BUMPER - Program Pagi RRI.mp3", duration_seconds=10)
test("BUMPER_RADIO", r, "AUTO_SORT", "PROGRAM_BUMPERS")

# ── TEST 6: Artis KPop terkenal (Blackpink) dengan genre tag ─────
r = classify_audio_file("Blackpink - Pink Venom.mp3", artist_tag="Blackpink", title_tag="Pink Venom", genre_tag="K-Pop", duration_seconds=200)
test("KPOP_BLACKPINK_TAG", r, "AUTO_SORT", "INTERNATIONAL")

# TEST 7: Blackpink tanpa tag - whitelist terdeteksi, missing tags -> NEEDS_REVIEW (score 35 < 60)
r = classify_audio_file("Blackpink - How You Like That.mp3", duration_seconds=200)
test("KPOP_BLACKPINK_NOMORE_TAG", r, "NEEDS_REVIEW")

# ── TEST 8: Artis Indonesia terkenal (Slank) dengan tag ──────────
r = classify_audio_file("Slank - Ku Tak Bisa.mp3", artist_tag="Slank", title_tag="Ku Tak Bisa", genre_tag="Rock", duration_seconds=240)
test("SLANK_ROCK_INDONESIA", r, "AUTO_SORT")

# ── TEST 9: Artis Barat Metallica dengan tag valid ───────────────
# Metallica dengan tag artist+title tapi tanpa genre dan year: REVIEW_WITH_SUGGESTION wajar
r = classify_audio_file("Metallica - Enter Sandman.mp3", artist_tag="Metallica", title_tag="Enter Sandman", duration_seconds=330)
test("METALLICA_WESTERN", r, "REVIEW_WITH_SUGGESTION", "INTERNATIONAL")

# ── TEST 10: File ambigu (Track 01) ──────────────────────────────
r = classify_audio_file("Track 01.mp3", duration_seconds=180)
test("TRACK_AMBIGU", r, "NEEDS_REVIEW", "UNKNOWN_ARTIST_TITLE")

# ── TEST 11: WhatsApp audio ──────────────────────────────────────
r = classify_audio_file("AUD-20260531-WA0002.mp3", duration_seconds=45)
test("WHATSAPP_AUDIO", r, "NEEDS_REVIEW", "UNKNOWN_ARTIST_TITLE")

# ── TEST 12: Keyword berbahaya saja (Love.mp3) ───────────────────
r = classify_audio_file("Love.mp3", duration_seconds=210)
test("DANGEROUS_KEYWORD_LOVE", r, "NEEDS_REVIEW")

# ── TEST 13: Background Music.mp3 ────────────────────────────────
r = classify_audio_file("Background Music.mp3", duration_seconds=210)
test("DANGEROUS_KEYWORD_BG", r, "NEEDS_REVIEW")

# ── TEST 14: Metadata vs filename conflict ────────────────────────
r = classify_audio_file("Judika - Aku Yang Tersakiti.mp3",
    artist_tag="Dewa 19", title_tag="Kangen", duration_seconds=240)
test("METADATA_FILENAME_CONFLICT", r, "NEEDS_REVIEW", "METADATA_FILENAME_CONFLICT", "METADATA_FILENAME_CONFLICT")

# ── TEST 15: Parent folder menyesatkan (Dangdut Campur/Dewa 19) ──
# Dewa19 parent folder menyesatkan tanpa tag -> NEEDS_REVIEW (sesuai spesifikasi)
r = classify_audio_file("Dewa 19 - Kangen.mp3", parent_folder="Dangdut Campur", duration_seconds=240)
test("PARENT_FOLDER_MISLEADING_DEWA", r, "NEEDS_REVIEW")

# TEST 16: Bugis dua sinyal: keyword filename + genre_tag = REVIEW_WITH_SUGGESTION (score 50 < 85)
# Operator masih perlu konfirmasi agar tidak salah sort
r = classify_audio_file("Elong Bugis - Mappideceng.mp3", genre_tag="Bugis", duration_seconds=200)
test("BUGIS_TWO_SIGNALS", r, "REVIEW_WITH_SUGGESTION", "02_MASTER_LOCAL_REGIONAL")

# TEST 17: Bugis satu sinyal (keyword 'daerah' medium = LOCAL_LANGUAGE_UNCERTAIN)
r = classify_audio_file("Bugis Daerah Lokal.mp3", duration_seconds=200)
test("BUGIS_ONE_SIGNAL", r, "REVIEW_WITH_SUGGESTION", "LOCAL_LANGUAGE_UNCERTAIN")

# ── TEST 18: Sholawat religi ─────────────────────────────────────
r = classify_audio_file("Sholawat Nabi - Ya Rasulullah.mp3", duration_seconds=180)
test("SHOLAWAT_RELIGI", r, "REVIEW_WITH_SUGGESTION", "03_MASTER_RELIGIOUS")

# ── TEST 19: Murottal Quran ───────────────────────────────────────
r = classify_audio_file("Murottal Surah Al-Fatihah.mp3", duration_seconds=120)
test("MUROTTAL_QURAN", r, "REVIEW_WITH_SUGGESTION", "QURAN_RECITATION")

# ── TEST 20: File minimal info (Hello.mp3) ────────────────────────
r = classify_audio_file("Hello.mp3", parent_folder="Lagu Campur", duration_seconds=200)
test("HELLO_MINIMAL_INFO", r, "NEEDS_REVIEW")

print("=" * 90)
print(f"  HASIL: {PASS} PASS | {FAIL} FAIL")
print("=" * 90)
