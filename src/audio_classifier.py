"""
src/audio_classifier.py — Multi-Stage Confidence-Based Audio Classifier
========================================================================
Menggantikan logika keyword-based sorter lama dengan sistem classifier berbasis
skor kepercayaan (confidence score) yang transparan dan dapat diaudit.

Prinsip utama:
- Parent folder hanya signal LEMAH (+15 poin), tidak pernah jadi keputusan final.
- Prefix resmi (JINGLE-, BUMPER-, dll.) adalah signal KUAT (+90 poin) → AUTO_SORT.
- Keyword umum (love, remix, theme, dll.) tidak boleh auto-sort sendirian.
- Default bukan Pop Indonesia, melainkan 90_NEEDS_REVIEW.
- Hanya AUTO_SORT (score >= 80) yang boleh masuk folder final.
"""

import os
import re
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger("RADIO_MUSIC_CLEANER")


# ─────────────────────────────────────────────
# STRUKTUR OUTPUT CLASSIFIER
# ─────────────────────────────────────────────
def _empty_result() -> Dict[str, Any]:
    return {
        "media_type": "UNKNOWN",
        "master_bucket": "90_NEEDS_REVIEW",
        "target_folder": "90_NEEDS_REVIEW/INSUFFICIENT_DATA",
        "confidence_score": 0.0,
        "decision": "NEEDS_REVIEW",
        "signals": [],
        "warnings": [],
        "reason": "Tidak ada informasi yang cukup untuk klasifikasi."
    }


# ─────────────────────────────────────────────
# HELPER: DETEKSI BAHASA
# ─────────────────────────────────────────────
def _detect_language(text: str, config: Dict[str, Any]) -> str:
    """Mendeteksi bahasa teks (EN/ID/UNKNOWN) berdasarkan stopwords."""
    if not text:
        return "UNKNOWN"
    words = set(re.sub(r'[^a-zA-Z\\s]', '', text.lower()).split())
    en_words = set(config.get("english_stopwords", []))
    id_words = set(config.get("indonesian_stopwords", []))
    en_count = len(words & en_words)
    id_count = len(words & id_words)
    if en_count == 0 and id_count == 0:
        return "UNKNOWN"
    if en_count > id_count:
        return "EN"
    if id_count > en_count:
        return "ID"
    return "AMBIGUOUS"


# ─────────────────────────────────────────────
# HELPER: CEK ARTIS TERKENAL
# ─────────────────────────────────────────────
def _find_known_artist(text: str, known_artists: Dict[str, List[str]]) -> Tuple[str, str]:
    """
    Mencari artis yang dikenal dalam teks (nama file / tag).
    Mengembalikan (target_folder, nama_artis_cocok) atau ("", "").
    """
    if not text:
        return "", ""
    text_lower = text.lower()
    for folder, artists in known_artists.items():
        for artist in artists:
            if artist.lower() in text_lower:
                return folder, artist
    return "", ""


# ─────────────────────────────────────────────
# HELPER: CEK KATA KUNCI DAERAH
# ─────────────────────────────────────────────
def _find_daerah_keyword(text: str, daerah_keywords: Dict[str, List[str]]) -> Tuple[str, str]:
    """
    Mencari kata kunci daerah dalam teks.
    Mengembalikan (target_folder, keyword_cocok) atau ("", "").
    """
    if not text:
        return "", ""
    text_lower = text.lower()
    for folder, keywords in daerah_keywords.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                return folder, kw
    return "", ""


# ─────────────────────────────────────────────
# HELPER: CEK PREFIX RESMI
# ─────────────────────────────────────────────
def _find_strong_prefix(filename: str, strong_prefixes: Dict[str, Any]) -> Tuple[str, str, str, int]:
    """
    Mencari prefix resmi pada nama file.
    Mengembalikan (target_folder, media_type, prefix, points) atau ("", "", "", 0).
    """
    filename_lower = filename.lower()
    for prefix, data in strong_prefixes.items():
        if filename_lower.startswith(prefix.lower()):
            return data["target_folder"], data["media_type"], prefix, data["points"]
    return "", "", "", 0


# ─────────────────────────────────────────────
# HELPER: CEK GENRE TAG SPESIFIK
# ─────────────────────────────────────────────
def _find_genre_tag_match(genre_tag: str, genre_tag_map: Dict[str, str]) -> Tuple[str, bool]:
    """
    Mencocokkan genre tag ke folder target.
    Mengembalikan (target_folder, is_specific).
    Jika folder == "AMBIGUOUS", is_specific = False.
    """
    if not genre_tag:
        return "", False
    genre_lower = genre_tag.lower().strip()
    for genre_key, folder in genre_tag_map.items():
        if genre_key.lower() in genre_lower:
            is_specific = folder != "AMBIGUOUS"
            return folder, is_specific
    return "", False


# ─────────────────────────────────────────────
# HELPER: CEK NAMA FILE AMBIGU
# ─────────────────────────────────────────────
def _is_filename_ambiguous(filename: str, ambiguous_keywords: List[str]) -> Tuple[bool, str]:
    """
    Memeriksa apakah nama file mengandung pola ambigu.
    Mengembalikan (is_ambiguous, reason).
    """
    name_no_ext = os.path.splitext(filename.lower())[0]
    for kw in ambiguous_keywords:
        kw_lower = kw.lower()
        if name_no_ext == kw_lower or name_no_ext.startswith(kw_lower):
            return True, f"Nama file dimulai dengan kata ambigu '{kw}'"
    return False, ""


# ─────────────────────────────────────────────
# HELPER: CEK POLA ARTIS-JUDUL
# ─────────────────────────────────────────────
def _has_clean_artist_title_pattern(filename: str) -> Tuple[bool, str, str]:
    """
    Memeriksa apakah nama file memiliki pola 'Artis - Judul'.
    Mengembalikan (has_pattern, artist_part, title_part).
    """
    name_no_ext = os.path.splitext(filename)[0]
    if " - " in name_no_ext:
        parts = name_no_ext.split(" - ", 1)
        artist_part = parts[0].strip()
        title_part = parts[1].strip()
        if artist_part and title_part and len(artist_part) > 1 and len(title_part) > 1:
            return True, artist_part, title_part
    return False, "", ""


# ─────────────────────────────────────────────
# HELPER: DETEKSI KONFLIK
# ─────────────────────────────────────────────
def _detect_conflicts(
    resolved_folder: str,
    artist_from_filename: str,
    genre_tag: str,
    parent_folder: str,
    duration_seconds: float,
    config: Dict[str, Any]
) -> List[str]:
    """
    Mendeteksi konflik antar signal.
    Mengembalikan daftar pesan konflik (warnings).
    """
    warnings = []
    dt = config.get("duration_thresholds", {})
    jingle_max = dt.get("jingle_max_seconds", 60)
    music_min = dt.get("music_min_seconds", 90)
    very_short = dt.get("very_short_flag_seconds", 10)

    # Konflik durasi: file sangat pendek tapi bukan BROADCAST
    if duration_seconds > 0:
        if duration_seconds < very_short:
            warnings.append(f"Durasi sangat pendek ({duration_seconds:.1f}s) — kemungkinan bukan lagu")
        elif duration_seconds < jingle_max:
            if "NON_MUSIK" not in resolved_folder and "BROADCAST" not in resolved_folder:
                warnings.append(f"Durasi pendek ({duration_seconds:.1f}s) tapi tidak memiliki prefix jingle/bumper")
        elif duration_seconds < music_min and resolved_folder.startswith("0"):
            warnings.append(f"Durasi {duration_seconds:.1f}s lebih pendek dari ekspektasi lagu (min {music_min}s)")

    # Konflik genre tag vs folder yang dihasilkan
    if genre_tag:
        genre_lower = genre_tag.lower()
        if "rock" in genre_lower and "02_MUSIK_INDONESIA/Pop_Indonesia" in resolved_folder:
            warnings.append(f"Genre tag '{genre_tag}' mengindikasikan Rock tapi folder tujuan adalah Pop Indonesia")
        if "dangdut" in genre_lower and "Pop_Indonesia" in resolved_folder:
            warnings.append(f"Genre tag '{genre_tag}' mengindikasikan Dangdut tapi tidak cocok folder tujuan")

    return warnings


# ─────────────────────────────────────────────
# FUNGSI UTAMA: CLASSIFIER
# ─────────────────────────────────────────────
def classify_audio(
    filename: str,
    artist_tag: str,
    title_tag: str,
    genre_tag: str,
    duration_seconds: float,
    parent_folder: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Mengklasifikasikan file audio menggunakan sistem multi-stage confidence scoring.

    Parameter:
        filename       : Nama file (bersih / setelah rename suggestion)
        artist_tag     : Nilai tag Artist dari metadata audio
        title_tag      : Nilai tag Title dari metadata audio
        genre_tag      : Nilai tag Genre dari metadata audio
        duration_seconds: Durasi audio dalam detik
        parent_folder  : Nama folder induk relatif dari input_dir
        config         : Konfigurasi classifier dari classifier_config.json

    Return:
        Dict berisi: media_type, master_bucket, target_folder, confidence_score,
                     decision, signals, warnings, reason
    """
    result = _empty_result()
    signals = []
    warnings = []
    total_score = 0.0
    resolved_folder = ""
    media_type = "UNKNOWN"
    signal_pts = config.get("signal_points", {})
    known_artists = config.get("known_artists", {})
    daerah_keywords = config.get("daerah_keywords", {})
    strong_prefixes = config.get("strong_prefixes", {})
    genre_tag_map = config.get("genre_tag_map", {})
    ambiguous_keywords = config.get("ambiguous_keywords", [])

    filename_lower = filename.lower()
    artist_tag_clean = (artist_tag or "").strip()
    title_tag_clean = (title_tag or "").strip()
    genre_tag_clean = (genre_tag or "").strip()

    # ─── TAHAP 1: CEK PREFIX RESMI (SIGNAL KUAT) ───────────────────────────
    pf_folder, pf_media, pf_prefix, pf_pts = _find_strong_prefix(filename, strong_prefixes)
    if pf_folder:
        resolved_folder = pf_folder
        media_type = pf_media
        pts = signal_pts.get("PREFIX_RESMI", pf_pts)
        total_score += pts
        signals.append({
            "source": "PREFIX_RESMI",
            "value": pf_prefix,
            "points": pts,
            "strength": "STRONG"
        })
        # Prefix resmi langsung tutup — tidak perlu cek lagi
        result.update({
            "media_type": media_type,
            "master_bucket": resolved_folder.split("/")[0],
            "target_folder": resolved_folder,
            "confidence_score": min(total_score, 100.0),
            "decision": "AUTO_SORT",
            "signals": signals,
            "warnings": warnings,
            "reason": f"Prefix resmi '{pf_prefix}' terdeteksi — klasifikasi otomatis."
        })
        return result

    # ─── TAHAP 2: CEK KATA KUNCI DAERAH (SIGNAL KUAT) ──────────────────────
    # Cek di nama file dahulu (lebih kuat)
    daerah_folder_fn, daerah_kw_fn = _find_daerah_keyword(filename, daerah_keywords)
    if daerah_folder_fn:
        resolved_folder = daerah_folder_fn
        media_type = "MUSIC"
        pts = signal_pts.get("DAERAH_KEYWORD_FILENAME", 70)
        total_score += pts
        signals.append({
            "source": "DAERAH_KEYWORD_FILENAME",
            "value": daerah_kw_fn,
            "points": pts,
            "strength": "STRONG"
        })

    # Cek di tag (lebih lemah dari nama file)
    if not daerah_folder_fn:
        combined_tags = f"{artist_tag_clean} {title_tag_clean} {genre_tag_clean}"
        daerah_folder_tag, daerah_kw_tag = _find_daerah_keyword(combined_tags, daerah_keywords)
        if daerah_folder_tag:
            resolved_folder = daerah_folder_tag
            media_type = "MUSIC"
            pts = signal_pts.get("DAERAH_KEYWORD_TAG", 60)
            total_score += pts
            signals.append({
                "source": "DAERAH_KEYWORD_TAG",
                "value": daerah_kw_tag,
                "points": pts,
                "strength": "STRONG"
            })

    # ─── TAHAP 3: CEK ARTIS TERKENAL (TAG METADATA) ─────────────────────────
    artist_folder_tag, artist_match_tag = _find_known_artist(artist_tag_clean, known_artists)
    if artist_folder_tag:
        if not resolved_folder:
            resolved_folder = artist_folder_tag
        media_type = "MUSIC"
        pts = signal_pts.get("ARTIST_TAG_KNOWN", 60)
        total_score += pts
        signals.append({
            "source": "ARTIST_TAG_KNOWN",
            "value": artist_match_tag,
            "points": pts,
            "strength": "STRONG"
        })
        # Deteksi konflik: artis tag vs folder dari daerah keyword
        if daerah_folder_fn and artist_folder_tag != daerah_folder_fn:
            warnings.append(f"Artis tag '{artist_match_tag}' menyarankan '{artist_folder_tag}' tapi kata kunci daerah menyarankan '{daerah_folder_fn}'")

    # ─── TAHAP 4: CEK ARTIS TERKENAL (NAMA FILE) ────────────────────────────
    if not artist_folder_tag:
        artist_folder_fn, artist_match_fn = _find_known_artist(filename, known_artists)
        if artist_folder_fn:
            if not resolved_folder:
                resolved_folder = artist_folder_fn
            media_type = "MUSIC"
            pts = signal_pts.get("ARTIST_FILENAME_KNOWN", 55)
            total_score += pts
            signals.append({
                "source": "ARTIST_FILENAME_KNOWN",
                "value": artist_match_fn,
                "points": pts,
                "strength": "STRONG"
            })

    # ─── TAHAP 5: CEK GENRE TAG SPESIFIK ────────────────────────────────────
    genre_folder, is_specific_genre = _find_genre_tag_match(genre_tag_clean, genre_tag_map)
    if genre_folder and genre_folder != "AMBIGUOUS":
        if not resolved_folder:
            resolved_folder = genre_folder
        media_type = "MUSIC"
        pts = signal_pts.get("GENRE_TAG_SPECIFIC", 45)
        total_score += pts
        signals.append({
            "source": "GENRE_TAG_SPECIFIC",
            "value": genre_tag_clean,
            "points": pts,
            "strength": "MEDIUM"
        })
        # Konflik: genre tag berbeda dengan hasil artis
        if resolved_folder and genre_folder != resolved_folder:
            if not any("DAERAH" in s["source"] or "ARTIST" in s["source"] for s in signals if s["source"] != "GENRE_TAG_SPECIFIC"):
                pass  # Hanya peringatan, tidak ganti folder jika artis sudah diketahui
            else:
                warnings.append(f"Genre tag '{genre_tag_clean}' menyarankan '{genre_folder}' tapi artis menyarankan '{resolved_folder}'")
    elif genre_folder == "AMBIGUOUS" or genre_tag_clean:
        pts = signal_pts.get("GENRE_TAG_AMBIGUOUS", 10)
        total_score += pts
        signals.append({
            "source": "GENRE_TAG_AMBIGUOUS",
            "value": genre_tag_clean or "(kosong)",
            "points": pts,
            "strength": "WEAK"
        })

    # ─── TAHAP 6: CEK POLA NAMA FILE (ARTIS - JUDUL) ────────────────────────
    has_pattern, artist_from_fn, title_from_fn = _has_clean_artist_title_pattern(filename)
    if has_pattern:
        pts = signal_pts.get("CLEAN_FILENAME_PATTERN", 30)
        total_score += pts
        signals.append({
            "source": "CLEAN_FILENAME_PATTERN",
            "value": f"{artist_from_fn} - {title_from_fn}",
            "points": pts,
            "strength": "MEDIUM"
        })

    # ─── TAHAP 7: CEK TAG ARTIST+TITLE KEDUANYA VALID ───────────────────────
    if artist_tag_clean and title_tag_clean:
        invalid_markers = ["unknown", "various", "vario", "untitled", "track"]
        if not any(m in artist_tag_clean.lower() for m in invalid_markers):
            pts = signal_pts.get("BOTH_TAG_VALID", 30)
            total_score += pts
            signals.append({
                "source": "BOTH_TAG_VALID",
                "value": f"{artist_tag_clean} / {title_tag_clean}",
                "points": pts,
                "strength": "MEDIUM"
            })
        else:
            warnings.append(f"Tag Artist mengandung nilai generik: '{artist_tag_clean}'")
    elif not artist_tag_clean and not title_tag_clean:
        # Kurangi penalti jika artis sudah teridentifikasi dari nama file
        has_known_artist_from_fn = any(
            s["source"] == "ARTIST_FILENAME_KNOWN" for s in signals
        )
        if has_known_artist_from_fn:
            # Penalti lebih kecil — nama file sudah cukup jelas
            penalty = min(config.get("conflict_penalties", {}).get("missing_both_tags", 25) // 2, 10)
            warnings.append(f"Tag Artist dan Title kosong (artis dikenali dari nama file) — poin dikurangi {penalty}")
        else:
            penalty = config.get("conflict_penalties", {}).get("missing_both_tags", 25)
            warnings.append("Kedua tag Artist dan Title kosong — poin dikurangi")
        total_score = max(0, total_score - penalty)

    # ─── TAHAP 8: DETEKSI BAHASA UNTUK ALIH GENRE INTERNASIONAL ─────────────
    combined_text = f"{artist_tag_clean} {title_tag_clean}"
    if not combined_text.strip():
        combined_text = os.path.splitext(filename)[0]

    lang = _detect_language(combined_text, config)
    if lang == "EN" and resolved_folder and resolved_folder.startswith("02_MUSIK_INDONESIA"):
        # Cek fallback internasional
        intl_fallback = {
            "02_MUSIK_INDONESIA/Rock_Alternative": "03_MUSIK_BARAT_INTERNASIONAL/Rock_Barat",
            "02_MUSIK_INDONESIA/Jazz_Rnb": "03_MUSIK_BARAT_INTERNASIONAL/Jazz_Rnb_Barat",
            "02_MUSIK_INDONESIA/Indie_Folk_Acoustic": "03_MUSIK_BARAT_INTERNASIONAL/Acoustic_Chill",
            "02_MUSIK_INDONESIA/Tembang_Kenangan": "03_MUSIK_BARAT_INTERNASIONAL/Nostalgia_Barat",
            "02_MUSIK_INDONESIA/Pop_Indonesia": "03_MUSIK_BARAT_INTERNASIONAL/Pop_Barat",
            "02_MUSIK_INDONESIA/Dangdut": "03_MUSIK_BARAT_INTERNASIONAL/Pop_Barat",
        }
        if resolved_folder in intl_fallback:
            resolved_folder = intl_fallback[resolved_folder]
        pts = signal_pts.get("LANGUAGE_DETECTION_EN", 15)
        total_score += pts
        signals.append({
            "source": "LANGUAGE_DETECTION_EN",
            "value": combined_text[:50],
            "points": pts,
            "strength": "WEAK"
        })
    elif lang == "ID":
        pts = signal_pts.get("LANGUAGE_DETECTION_ID", 15)
        total_score += pts
        signals.append({
            "source": "LANGUAGE_DETECTION_ID",
            "value": combined_text[:50],
            "points": pts,
            "strength": "WEAK"
        })

    # ─── TAHAP 9: PARENT FOLDER SEBAGAI HINT LEMAH ──────────────────────────
    if parent_folder and parent_folder not in [".", "", "input"]:
        daerah_folder_parent, daerah_kw_parent = _find_daerah_keyword(parent_folder, daerah_keywords)
        if daerah_folder_parent and not resolved_folder:
            resolved_folder = daerah_folder_parent
            pts = signal_pts.get("PARENT_FOLDER_HINT", 15)
            total_score += pts
            signals.append({
                "source": "PARENT_FOLDER_HINT",
                "value": f"folder '{parent_folder}' → '{daerah_kw_parent}'",
                "points": pts,
                "strength": "WEAK"
            })
        elif parent_folder:
            # Hanya tambahkan poin kecil sebagai hint
            pts = signal_pts.get("PARENT_FOLDER_HINT", 15)
            total_score += pts
            signals.append({
                "source": "PARENT_FOLDER_HINT",
                "value": f"folder '{parent_folder}'",
                "points": pts,
                "strength": "WEAK"
            })

    # ─── TAHAP 10: DETEKSI NAMA FILE AMBIGU ─────────────────────────────────
    is_ambiguous_fn, ambig_reason = _is_filename_ambiguous(filename, ambiguous_keywords)
    if is_ambiguous_fn:
        penalty = config.get("conflict_penalties", {}).get("ambiguous_artist_part", 20)
        total_score = max(0, total_score - penalty)
        warnings.append(f"Nama file ambigu: {ambig_reason}")

    # ─── TAHAP 11: DETEKSI KONFLIK DURASI & GENRE ───────────────────────────
    conflict_warnings = _detect_conflicts(
        resolved_folder or "UNKNOWN",
        artist_from_fn,
        genre_tag_clean,
        parent_folder,
        duration_seconds,
        config
    )
    warnings.extend(conflict_warnings)

    # Penalti konflik
    for w in conflict_warnings:
        if "Durasi" in w:
            penalty = config.get("conflict_penalties", {}).get("duration_vs_type_mismatch", 15)
            total_score = max(0, total_score - penalty)

    # ─── TAHAP 12: FALLBACK JIKA TIDAK ADA FOLDER TERESOLUSI ────────────────
    if not resolved_folder:
        review_subfolders = config.get("review_subfolders", {})
        if is_ambiguous_fn:
            resolved_folder = review_subfolders.get("ambiguous_filename", "90_NEEDS_REVIEW/AMBIGUOUS_FILENAME")
        elif duration_seconds > 0 and duration_seconds < config.get("duration_thresholds", {}).get("very_short_flag_seconds", 10):
            resolved_folder = review_subfolders.get("possible_non_music", "90_NEEDS_REVIEW/POSSIBLE_NON_MUSIC")
        elif conflict_warnings:
            resolved_folder = review_subfolders.get("genre_conflict", "90_NEEDS_REVIEW/GENRE_CONFLICT")
        else:
            resolved_folder = review_subfolders.get("insufficient_data", "90_NEEDS_REVIEW/INSUFFICIENT_DATA")

    # ─── KEPUTUSAN FINAL ─────────────────────────────────────────────────────
    final_score = min(max(total_score, 0.0), 100.0)
    thresholds = config.get("thresholds", {})
    auto_sort_threshold = thresholds.get("auto_sort", 80)
    review_suggestion_threshold = thresholds.get("review_with_suggestion", 50)

    if final_score >= auto_sort_threshold and not resolved_folder.startswith("90_NEEDS_REVIEW"):
        decision = "AUTO_SORT"
        media_type = media_type if media_type != "UNKNOWN" else "MUSIC"
    elif final_score >= review_suggestion_threshold:
        decision = "REVIEW_WITH_SUGGESTION"
        # Pastikan folder review_with_suggestion
        review_subfolders = config.get("review_subfolders", {})
        if not resolved_folder.startswith("90_NEEDS_REVIEW"):
            # Simpan saran sebagai context tapi fisik masuk LOW_CONFIDENCE
            suggested = resolved_folder
            resolved_folder = review_subfolders.get("low_confidence", "90_NEEDS_REVIEW/LOW_CONFIDENCE_MUSIC")
            signals.append({
                "source": "SUGGESTION_ONLY",
                "value": suggested,
                "points": 0,
                "strength": "INFO"
            })
    else:
        decision = "NEEDS_REVIEW"
        review_subfolders = config.get("review_subfolders", {})
        if conflict_warnings:
            resolved_folder = review_subfolders.get("genre_conflict", "90_NEEDS_REVIEW/GENRE_CONFLICT")
        elif is_ambiguous_fn:
            resolved_folder = review_subfolders.get("ambiguous_filename", "90_NEEDS_REVIEW/AMBIGUOUS_FILENAME")
        else:
            resolved_folder = review_subfolders.get("insufficient_data", "90_NEEDS_REVIEW/INSUFFICIENT_DATA")

    # Bangun reason string
    signal_summary = "; ".join([f"{s['source']}({s['points']})" for s in signals if s["strength"] != "INFO"])
    reason = f"[{decision}] Score={final_score:.0f}/100. Signals: {signal_summary or '(tidak ada)'}"
    if warnings:
        reason += f". Peringatan: {' | '.join(warnings[:2])}"

    master_bucket = resolved_folder.split("/")[0] if "/" in resolved_folder else resolved_folder

    result.update({
        "media_type": media_type,
        "master_bucket": master_bucket,
        "target_folder": resolved_folder,
        "confidence_score": round(final_score, 1),
        "decision": decision,
        "signals": signals,
        "warnings": warnings,
        "reason": reason
    })
    return result
