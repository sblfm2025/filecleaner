"""
src/audio_classifier.py — Multi-Stage Confidence-Based Audio Classifier v3.0
==============================================================================
Sistem classifier berbasis confidence score untuk kebutuhan stasiun radio
profesional. Menggantikan keyword-based sorter lama dengan pendekatan
multi-stage yang transparan dan dapat diaudit.

Prinsip utama v3.0:
  - Parent folder hanya signal LEMAH (+8 poin), TIDAK pernah keputusan final.
  - Prefix resmi (JINGLE-, BUMPER-, IKLAN-, ILM-, dst) = signal KUAT (+50).
  - Keyword berbahaya (love, remix, dj, audio, track) TIDAK boleh auto-sort sendirian.
  - Default folder: 01_MASTER_MUSIC/10_UNKNOWN_RELEASE_TYPE (bukan Pop Indonesia).
  - Threshold: >= 85 AUTO_SORT | 60-84 REVIEW_WITH_SUGGESTION | < 60 NEEDS_REVIEW.
  - Deteksi konflik eksplisit: metadata vs filename, parent vs content, durasi vs tipe.
  - 1 FILE = 1 LOKASI FISIK. Genre/mood/artis = index M3U, bukan salinan file.

Struktur output folder: RADIO_AUDIO_MASTER_LIBRARY/ (bukan RADIO_AUDIO_LIBRARY/).
"""

import os
import re
import json
import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger("RADIO_MUSIC_CLEANER")

# Direktori config classification
_CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "classification")
_config_cache: Dict[str, Any] = {}


# ══════════════════════════════════════════════════════════════════
# LOADER KONFIGURASI
# ══════════════════════════════════════════════════════════════════

def _load_classification_config(filename: str) -> Dict[str, Any]:
    """Memuat satu file JSON dari config/classification/ dengan caching."""
    if filename in _config_cache:
        return _config_cache[filename]
    path = os.path.join(_CONFIG_DIR, filename)
    if not os.path.exists(path):
        logger.warning(f"[CLASSIFIER] Config tidak ditemukan: {path}")
        _config_cache[filename] = {}
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        _config_cache[filename] = data
        return data
    except Exception as e:
        logger.error(f"[CLASSIFIER] Gagal memuat {path}: {e}")
        _config_cache[filename] = {}
        return {}


def _get_all_configs() -> Dict[str, Any]:
    """Memuat semua config classification sekaligus."""
    return {
        "rules":          _load_classification_config("classification_rules.json"),
        "prefixes":       _load_classification_config("strong_prefix_rules.json"),
        "dangerous":      _load_classification_config("dangerous_keywords.json"),
        "local":          _load_classification_config("local_regional_keywords.json"),
        "religious":      _load_classification_config("religious_keywords.json"),
        "international":  _load_classification_config("international_keywords.json"),
        "radio_asset":    _load_classification_config("radio_asset_keywords.json"),
        "program":        _load_classification_config("program_recording_keywords.json"),
        "whitelist_local":_load_classification_config("artist_whitelist_local.json"),
        "whitelist_intl": _load_classification_config("artist_whitelist_international.json"),
        "genre_index":    _load_classification_config("genre_index_rules.json"),
        "mood_index":     _load_classification_config("mood_index_rules.json"),
        "review":         _load_classification_config("review_rules.json"),
    }


# ══════════════════════════════════════════════════════════════════
# STRUKTUR OUTPUT
# ══════════════════════════════════════════════════════════════════

def _empty_result() -> Dict[str, Any]:
    return {
        "media_type":    "UNKNOWN",
        "master_bucket": "90_NEEDS_REVIEW",
        "target_folder": "90_NEEDS_REVIEW/01_UNKNOWN_ARTIST_TITLE",
        "review_folder": "90_NEEDS_REVIEW/01_UNKNOWN_ARTIST_TITLE",
        "confidence_score": 0,
        "decision":      "NEEDS_REVIEW",
        "signals":       [],
        "warnings":      [],
        "conflicts":     [],
        "reason":        "Tidak ada informasi yang cukup untuk klasifikasi.",
    }


# ══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════

def _normalize(text: str) -> str:
    """Normalisasi teks ke lowercase, hilangkan karakter non-alfanumerik berlebih."""
    return re.sub(r'\s+', ' ', text.lower().strip()) if text else ""


def _word_in_text(word: str, text: str) -> bool:
    """Cek apakah word ada sebagai kata utuh dalam text (word boundary)."""
    return bool(re.search(r'(?<![a-z])' + re.escape(word) + r'(?![a-z])', text))


def _contains_any(text: str, keywords: List[str]) -> Tuple[bool, str]:
    """Cek apakah teks mengandung salah satu keyword. Kembalikan (found, keyword)."""
    t = _normalize(text)
    for kw in keywords:
        if kw.lower() in t:
            return True, kw
    return False, ""


def _detect_language(text: str, cfg_intl: Dict[str, Any]) -> str:
    """Deteksi bahasa teks: EN/ID/LOCAL/UNKNOWN."""
    if not text:
        return "UNKNOWN"
    words = set(re.sub(r'[^a-zA-Z\s]', '', text.lower()).split())
    en_words = set(cfg_intl.get("english_stopwords", []))
    id_words = set(cfg_intl.get("indonesian_stopwords", []))
    en_count = len(words & en_words)
    id_count = len(words & id_words)
    if en_count == 0 and id_count == 0:
        return "UNKNOWN"
    if en_count > id_count:
        return "EN"
    if id_count > en_count:
        return "ID"
    return "AMBIGUOUS"


def _has_clean_artist_title_pattern(filename: str) -> Tuple[bool, str, str]:
    """Cek pola 'Artis - Judul' dalam nama file. Kembalikan (found, artist, title)."""
    name = os.path.splitext(filename)[0]
    if " - " in name:
        parts = name.split(" - ", 1)
        a, t = parts[0].strip(), parts[1].strip()
        if a and t and len(a) > 1 and len(t) > 1:
            return True, a, t
    return False, "", ""


def _is_ambiguous_filename(filename: str, dangerous_cfg: Dict[str, Any]) -> Tuple[bool, str]:
    """Cek apakah nama file ambigu/tidak informatif."""
    name_lower = _normalize(os.path.splitext(filename)[0])
    patterns = dangerous_cfg.get("ambiguous_filename_patterns", [])
    whatsapp = dangerous_cfg.get("whatsapp_patterns", [])
    watermarks = dangerous_cfg.get("site_watermark_patterns", [])

    for p in whatsapp:
        if name_lower.startswith(p.lower()):
            return True, f"Pola WhatsApp/PTT: '{p}'"
    for p in watermarks:
        if p.lower() in name_lower:
            return True, f"Watermark situs download: '{p}'"
    for p in patterns:
        pl = p.lower()
        if name_lower == pl or name_lower.startswith(pl + " ") or name_lower.startswith(pl + "_"):
            return True, f"Pola ambigu: '{p}'"
    return False, ""


def _check_strong_prefix(filename: str, prefix_cfg: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Cek prefix resmi pada nama file.
    Kembalikan (target_folder, media_type, matched_prefix) atau ('', '', '').
    """
    fname_lower = filename.lower()
    category_map = {
        "radio_asset": "RADIO_ASSET",
        "commercial_public_service": "COMMERCIAL_AD",
        "instrumental_bed": "INSTRUMENTAL_BED",
        "special_event": "SPECIAL_EVENT",
    }
    for category, prefixes in prefix_cfg.items():
        if not isinstance(prefixes, dict):
            continue
        media_type = category_map.get(category, "UNKNOWN")
        if category == "commercial_public_service":
            # Bedakan iklan vs ILM/PSA
            for prefix, folder in prefixes.items():
                if fname_lower.startswith(prefix.lower()):
                    if "ILM" in prefix.upper() or "PSA" in prefix.upper() or "LAYANAN" in prefix.upper():
                        media_type = "PUBLIC_SERVICE"
                    else:
                        media_type = "COMMERCIAL_AD"
                    return folder, media_type, prefix
        else:
            for prefix, folder in prefixes.items():
                if fname_lower.startswith(prefix.lower()):
                    return folder, media_type, prefix
    return "", "", ""


def _find_in_whitelist(text: str, whitelist: Dict[str, Any]) -> Tuple[str, str]:
    """
    Cari artis dalam whitelist.
    Whitelist bisa berupa dict {folder: [list artis]} ATAU dict {kategori: [list artis]}.
    Kembalikan (folder_target, nama_artis_cocok) atau ('', '').
    """
    text_lower = _normalize(text)
    for key, value in whitelist.items():
        if key.startswith("_"):
            continue
        if isinstance(value, list):
            # Format: {folder_path: [artis1, artis2, ...]}
            # atau {category_name: [artis1, artis2, ...]}
            for artist in value:
                if not isinstance(artist, str):
                    continue
                if len(artist) > 3 and _word_in_text(artist.lower(), text_lower):
                    # Jika key adalah path folder valid, gunakan langsung
                    if "/" in key or key.startswith("0") or key.startswith("9"):
                        return key, artist
                    else:
                        # key adalah nama kategori, map ke folder
                        cat_map = {
                            "pop_indonesia_artists": "01_MASTER_MUSIC/10_UNKNOWN_RELEASE_TYPE",
                            "rock_alternative_indonesia": "01_MASTER_MUSIC/10_UNKNOWN_RELEASE_TYPE",
                            "dangdut_artists": "01_MASTER_MUSIC/10_UNKNOWN_RELEASE_TYPE",
                            "jazz_rnb_indonesia": "01_MASTER_MUSIC/10_UNKNOWN_RELEASE_TYPE",
                            "tembang_kenangan_artists": "01_MASTER_MUSIC/10_UNKNOWN_RELEASE_TYPE",
                            "anak_anak_artists": "01_MASTER_MUSIC/10_UNKNOWN_RELEASE_TYPE",
                        }
                        return cat_map.get(key, "01_MASTER_MUSIC/10_UNKNOWN_RELEASE_TYPE"), artist
        elif isinstance(value, dict):
            # Format nested, skip
            continue
    return "", ""


def _find_local_keyword(text: str, local_cfg: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Cari kata kunci lokal dalam teks.
    Kembalikan (folder, keyword, strength: 'strong'/'medium') atau ('','','').
    """
    t = _normalize(text)
    strong_kws = local_cfg.get("strong_keywords", {})
    for folder, keywords in strong_kws.items():
        for kw in keywords:
            if kw.lower() in t:
                return folder, kw, "strong"
    medium_kws = local_cfg.get("medium_keywords", {})
    for _, keywords in medium_kws.items():
        for kw in keywords:
            if kw.lower() in t:
                return "02_MASTER_LOCAL_REGIONAL/05_UNKNOWN_LOCAL", kw, "medium"
    return "", "", ""


def _find_religious_keyword(text: str, religious_cfg: Dict[str, Any]) -> Tuple[str, str, str]:
    """
    Cari kata kunci religi.
    Kembalikan (folder, keyword, media_type) atau ('','','').
    """
    t = _normalize(text)
    sections = ["islamic_songs", "quran_recitation", "tausiyah_ceramah", "ramadan_eid", "religious_background"]
    for section in sections:
        data = religious_cfg.get(section, {})
        folder = data.get("target_folder", "")
        media_type = data.get("media_type", "RELIGIOUS_MUSIC")
        for kw in data.get("keywords", []):
            if kw.lower() in t:
                return folder, kw, media_type
    return "", "", ""


def _detect_conflicts(
    filename: str,
    artist_tag: str,
    title_tag: str,
    parent_folder: str,
    duration_seconds: float,
    resolved_folder: str,
    resolved_media_type: str,
    cfg_rules: Dict[str, Any],
) -> List[str]:
    """Deteksi konflik antar sinyal. Kembalikan daftar jenis konflik."""
    conflicts = []
    dur = cfg_rules.get("duration_rules", {})

    # 1. Konflik metadata vs filename
    has_pattern, fn_artist, fn_title = _has_clean_artist_title_pattern(filename)
    if has_pattern and artist_tag and title_tag:
        a_tag = _normalize(artist_tag)
        t_tag = _normalize(title_tag)
        a_fn  = _normalize(fn_artist)
        t_fn  = _normalize(fn_title)
        # Jika tag artis SANGAT berbeda dari artis di nama file
        if a_tag and a_fn and a_tag not in a_fn and a_fn not in a_tag:
            if len(a_tag) > 3 and len(a_fn) > 3:
                conflicts.append("METADATA_FILENAME_CONFLICT")

    # 2. Konflik durasi vs tipe
    if duration_seconds > 0:
        sfx_max    = dur.get("sfx_max_seconds", 10)
        jingle_max = dur.get("jingle_max_seconds", 60)
        ad_min     = dur.get("ad_min_seconds", 10)
        ad_max     = dur.get("ad_max_seconds", 120)
        song_min   = dur.get("song_min_seconds", 120)
        prog_min   = dur.get("long_program_min_seconds", 900)

        if resolved_media_type in ("COMMERCIAL_AD", "PUBLIC_SERVICE"):
            if duration_seconds < ad_min or duration_seconds > ad_max:
                conflicts.append("DURATION_CATEGORY_CONFLICT")
        elif resolved_media_type == "RADIO_ASSET":
            if duration_seconds > jingle_max:
                conflicts.append("DURATION_CATEGORY_CONFLICT")
        elif resolved_media_type in ("MUSIC", "RELIGIOUS_MUSIC", "LOCAL_REGIONAL_MUSIC", "INTERNATIONAL_MUSIC"):
            if duration_seconds < song_min:
                conflicts.append("DURATION_CATEGORY_CONFLICT")
        elif resolved_media_type == "PROGRAM_RECORDING":
            if duration_seconds < prog_min:
                conflicts.append("DURATION_CATEGORY_CONFLICT")

    # 3. Konflik parent folder vs artis dikenal
    # (akan diisi oleh pemanggil jika ada sinyal yang bertentangan)

    return conflicts


# ══════════════════════════════════════════════════════════════════
# FUNGSI UTAMA: classify_audio_file
# ══════════════════════════════════════════════════════════════════

def classify_audio_file(
    filename: str,
    source_path: str = "",
    parent_folder: str = "",
    duration_seconds: Optional[float] = None,
    genre_tag: str = "",
    artist_tag: str = "",
    title_tag: str = "",
    album_tag: str = "",
    year_tag: str = "",
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Klasifikasi file audio menggunakan sistem multi-stage confidence scoring.

    Parameter:
        filename         : Nama file (clean/setelah rename suggestion)
        source_path      : Path lengkap file sumber (opsional)
        parent_folder    : Nama relatif folder induk dari input_dir
        duration_seconds : Durasi audio dalam detik (None jika tidak diketahui)
        genre_tag        : Tag Genre dari metadata
        artist_tag       : Tag Artist dari metadata
        title_tag        : Tag Title dari metadata
        album_tag        : Tag Album dari metadata
        year_tag         : Tag Year dari metadata
        config           : Dict konfigurasi (opsional, otomatis dimuat jika None)

    Return:
        Dict dengan kunci: media_type, master_bucket, target_folder, review_folder,
        confidence_score, decision, signals, warnings, conflicts, reason
    """
    result   = _empty_result()
    signals: List[str]  = []
    warnings: List[str] = []
    conflicts: List[str] = []
    score    = 0
    resolved_folder = ""
    resolved_media  = "UNKNOWN"

    # Load semua config
    cfg = _get_all_configs()
    rules_cfg   = cfg["rules"]
    score_matrix = rules_cfg.get("score_matrix", {})
    pos_scores   = score_matrix.get("positive", {})
    neg_scores   = score_matrix.get("penalties", {})

    dur = duration_seconds if duration_seconds is not None else -1.0
    dur_rules = rules_cfg.get("duration_rules", {})

    fname_lower = filename.lower()
    artist_clean = (artist_tag or "").strip()
    title_clean  = (title_tag or "").strip()
    genre_clean  = (genre_tag or "").strip()

    # ──────────────────────────────────────────────
    # STAGE 1 — VALIDASI AUDIO DASAR
    # ──────────────────────────────────────────────
    if dur == 0.0:
        result.update({
            "media_type":    "BAD_AUDIO",
            "master_bucket": "92_BAD_AUDIO",
            "target_folder": "92_BAD_AUDIO",
            "review_folder": "92_BAD_AUDIO",
            "confidence_score": 100,
            "decision":      "REJECT_BAD_AUDIO",
            "signals":       ["duration_zero"],
            "warnings":      ["File durasi nol, kemungkinan corrupt"],
            "conflicts":     [],
            "reason":        "Durasi audio = 0 detik. File kemungkinan corrupt atau kosong."
        })
        return result

    ext = os.path.splitext(filename)[1].lower()
    supported_exts = rules_cfg.get("supported_extensions", [".mp3", ".wav", ".flac", ".ogg", ".aac", ".m4a", ".wma"])
    if ext and ext not in supported_exts:
        result.update({
            "media_type":    "BAD_AUDIO",
            "target_folder": "92_BAD_AUDIO",
            "review_folder": "90_NEEDS_REVIEW/10_UNSUPPORTED_OR_UNKNOWN_TYPE",
            "confidence_score": 90,
            "decision":      "REJECT_BAD_AUDIO",
            "signals":       ["unsupported_extension"],
            "warnings":      [f"Ekstensi tidak didukung: {ext}"],
            "reason":        f"Ekstensi file '{ext}' tidak dikenali sebagai audio."
        })
        return result

    # ──────────────────────────────────────────────
    # STAGE 2 — DETEKSI NON-MUSIK (PREFIX KUAT)
    # ──────────────────────────────────────────────
    pf_folder, pf_media, pf_prefix = _check_strong_prefix(filename, cfg["prefixes"])
    if pf_folder:
        pf_score = pos_scores.get("strong_prefix_match", 50)
        score += pf_score
        signals.append(f"strong_prefix_match:{pf_prefix}")
        resolved_folder = pf_folder
        resolved_media  = pf_media

        # Cek konflik durasi
        dur_conflict = False
        if dur > 0:
            if pf_media in ("COMMERCIAL_AD", "PUBLIC_SERVICE"):
                ad_min = dur_rules.get("ad_min_seconds", 10)
                ad_max = dur_rules.get("ad_max_seconds", 120)
                if dur < ad_min or dur > ad_max:
                    conflicts.append("DURATION_CATEGORY_CONFLICT")
                    score += neg_scores.get("duration_category_conflict", -30)
                    warnings.append(f"Durasi {dur:.0f}s tidak wajar untuk iklan/ILM (expected {ad_min}–{ad_max}s)")
                    dur_conflict = True
                else:
                    score += pos_scores.get("duration_type_match", 10)
                    signals.append("duration_type_match")
            elif pf_media == "RADIO_ASSET":
                jmax = dur_rules.get("jingle_max_seconds", 60)
                if dur > jmax:
                    conflicts.append("DURATION_CATEGORY_CONFLICT")
                    warnings.append(f"Durasi {dur:.0f}s terlalu panjang untuk aset radio (max {jmax}s)")
                    dur_conflict = True
                else:
                    score += pos_scores.get("duration_type_match", 10)
                    signals.append("duration_type_match")
            elif pf_media == "INSTRUMENTAL_BED":
                score += pos_scores.get("duration_type_match", 10)
                signals.append("duration_type_match")
        else:
            score += 25

        # Tentukan decision berdasarkan skor dan konflik durasi
        final_score = max(0, min(100, score))
        auto_thresh = rules_cfg.get("confidence_thresholds", {}).get("auto_sort", 85)
        if dur_conflict:
            decision = "REVIEW_WITH_SUGGESTION"
            review_sub = cfg["review"].get("review_subfolders", {})
            r_folder = review_sub.get("duration_anomaly", "90_NEEDS_REVIEW/09_DURATION_ANOMALY")
        else:
            # Prefix resmi kuat = AUTO_SORT langsung (tidak perlu threshold skor)
            decision = "AUTO_SORT"
            r_folder = resolved_folder

        bucket = resolved_folder.split("/")[0] if "/" in resolved_folder else resolved_folder
        reason = f"[{decision}] Prefix '{pf_prefix}' terdeteksi. Score={final_score}/100."
        if warnings:
            reason += " Peringatan: " + "; ".join(warnings)

        result.update({
            "media_type":       resolved_media,
            "master_bucket":    bucket,
            "target_folder":    resolved_folder,
            "review_folder":    r_folder,
            "confidence_score": final_score,
            "decision":         decision,
            "signals":          signals,
            "warnings":         warnings,
            "conflicts":        conflicts,
            "reason":           reason,
        })
        return result

    # ──────────────────────────────────────────────
    # STAGE 2b — DETEKSI PROGRAM RECORDING
    # ──────────────────────────────────────────────
    prog_cfg = cfg["program"]
    prog_min_dur = prog_cfg.get("min_duration_for_auto_sort", 900)
    if dur >= prog_min_dur:
        prog_sections = ["talkshow", "interview", "news_bulletin", "podcast", "voxpop", "longform"]
        for section in prog_sections:
            data = prog_cfg.get(section, {})
            found, kw = _contains_any(f"{filename} {artist_clean} {title_clean}", data.get("keywords", []))
            if found:
                prog_score = pos_scores.get("program_duration_and_keyword", 40)
                score += prog_score
                signals.append(f"program_duration_and_keyword:{kw}")
                resolved_folder = data.get("target_folder", "08_MASTER_PROGRAM_RECORDINGS/06_LONGFORM_ARCHIVE")
                resolved_media  = "PROGRAM_RECORDING"
                break

    if resolved_media == "PROGRAM_RECORDING":
        final_score = max(0, min(100, score))
        auto_thresh = rules_cfg.get("confidence_thresholds", {}).get("auto_sort", 85)
        decision = "AUTO_SORT" if final_score >= auto_thresh else "REVIEW_WITH_SUGGESTION"
        review_sub = cfg["review"].get("review_subfolders", {})
        r_folder = resolved_folder if decision == "AUTO_SORT" else review_sub.get("low_confidence", "90_NEEDS_REVIEW/02_LOW_CONFIDENCE_CATEGORY")
        bucket = resolved_folder.split("/")[0]
        result.update({
            "media_type": resolved_media,
            "master_bucket": bucket,
            "target_folder": resolved_folder,
            "review_folder": r_folder,
            "confidence_score": final_score,
            "decision": decision,
            "signals": signals,
            "warnings": warnings,
            "conflicts": conflicts,
            "reason": f"[{decision}] Rekaman program terdeteksi (durasi {dur:.0f}s + keyword). Score={final_score}/100.",
        })
        return result

    # ──────────────────────────────────────────────
    # STAGE 3 — DETEKSI MUSIK LOKAL/RELIGI/INTERNASIONAL
    # ──────────────────────────────────────────────
    combined_all = f"{filename} {artist_clean} {title_clean} {genre_clean} {parent_folder}"
    local_evidence_count = 0
    religious_folder = ""
    religious_media  = ""
    # Pre-compute pola artis-judul (dipakai di beberapa stage)
    has_pattern, fn_artist, fn_title = _has_clean_artist_title_pattern(filename)

    # 3a. Deteksi Religi
    rel_folder, rel_kw, rel_media = _find_religious_keyword(combined_all, cfg["religious"])
    if rel_folder:
        resolved_folder = rel_folder
        resolved_media  = rel_media
        score += pos_scores.get("keyword_strong_match", 25)
        signals.append(f"religious_keyword:{rel_kw}")
        religious_folder = rel_folder
        religious_media  = rel_media

    # 3b. Deteksi Lokal — hitungan bukti
    if not resolved_folder:
        local_signals = []
        # Pre-compute pola artis-judul untuk dipakai di stage 3b dan seterusnya
        has_pattern, fn_artist, fn_title = _has_clean_artist_title_pattern(filename)

        # Bukti 1: keyword lokal di filename
        lf, lkw, lstr = _find_local_keyword(filename, cfg["local"])
        if lf:
            local_signals.append(("filename_local_keyword", lf, lkw, lstr))

        # Bukti 2: keyword lokal di genre_tag secara terpisah
        # Genre tag 'Bugis' adalah bukti terpisah dari keyword 'bugis' di filename
        # karena sumbernya berbeda (metadata vs nama file)
        if genre_clean:
            lt_genre, lkw_genre, lstr_genre = _find_local_keyword(genre_clean, cfg["local"])
            if lt_genre:
                local_signals.append(("genre_tag_local", lt_genre, lkw_genre, lstr_genre))
        # Juga cek dari artist_tag dan title_tag
        tags_text = f"{artist_clean} {title_clean}"
        lt, lkw2, lstr2 = _find_local_keyword(tags_text, cfg["local"])
        if lt and lkw2:
            local_signals.append(("tag_local_keyword", lt, lkw2, lstr2))

        # Bukti 3: artis whitelist lokal
        wl_folder, wl_artist = _find_in_whitelist(f"{artist_clean} {fn_artist}", cfg["whitelist_local"])
        if wl_folder and "02_MASTER_LOCAL_REGIONAL" in wl_folder:
            local_signals.append(("local_artist_whitelist", wl_folder, wl_artist, "strong"))

        # Bukti 4: parent folder hint lokal
        local_parent_hints = cfg["local"].get("parent_folder_hints", [])
        found_ph, ph_kw = _contains_any(parent_folder, local_parent_hints)
        if found_ph:
            local_signals.append(("parent_folder_local_hint", "", ph_kw, "weak"))

        local_evidence_count = len(local_signals)

        if local_evidence_count >= 2:
            # Cukup bukti kuat — tentukan folder dari sinyal terkuat
            strong_signals = [s for s in local_signals if s[3] == "strong"]
            best = strong_signals[0] if strong_signals else local_signals[0]
            resolved_folder = best[1] if best[1] else "02_MASTER_LOCAL_REGIONAL/05_UNKNOWN_LOCAL"
            resolved_media = "LOCAL_REGIONAL_MUSIC"
            for sig in local_signals:
                if sig[3] == "strong":
                    score += pos_scores.get("local_keyword_strong", 25)
                else:
                    score += pos_scores.get("parent_folder_hint", 8)
                signals.append(f"{sig[0]}:{sig[2]}")

        elif local_evidence_count == 1:
            # Hanya satu bukti — masuk review lokal
            resolved_media = "LOCAL_REGIONAL_MUSIC"
            score += pos_scores.get("keyword_medium_match", 15)
            signals.append(f"local_single_evidence:{local_signals[0][2]}")
            warnings.append("LOCAL_INSUFFICIENT_EVIDENCE")
            review_sub = cfg["review"].get("review_subfolders", {})
            resolved_folder = review_sub.get("local_language_uncertain", "90_NEEDS_REVIEW/07_LOCAL_LANGUAGE_UNCERTAIN")

    # 3c. Deteksi Internasional & Artis Indonesia Terkenal
    if not resolved_folder:
        # Cek whitelist artis internasional — dari tag DAN dari nama file
        search_intl = " ".join(filter(None, [artist_clean, fn_artist, os.path.splitext(filename)[0]]))
        wl_intl_folder, wl_intl_artist = _find_in_whitelist(search_intl, cfg["whitelist_intl"])
        if wl_intl_folder:
            score += pos_scores.get("international_artist_whitelist", 30)
            signals.append(f"international_artist_whitelist:{wl_intl_artist}")
            resolved_folder = wl_intl_folder
            resolved_media  = "INTERNATIONAL_MUSIC"

        # Cek genre tag internasional
        if not resolved_folder:
            intl_genre_sections = cfg["international"].get("western", {}).get("genre_keywords", [])
            kpop_genre = cfg["international"].get("kpop_jpop", {}).get("genre_keywords", [])
            all_intl_genre = intl_genre_sections + kpop_genre
            found_ig, ig_kw = _contains_any(genre_clean, all_intl_genre)
            if found_ig:
                score += pos_scores.get("genre_tag_strong_match", 20)
                signals.append(f"intl_genre_tag:{ig_kw}")
                resolved_folder = "04_MASTER_INTERNATIONAL/05_UNKNOWN_INTERNATIONAL"
                resolved_media  = "INTERNATIONAL_MUSIC"

    # 3d. Deteksi Artis Indonesia dari whitelist lokal (jika belum terklasifikasi)
    if not resolved_folder:
        search_local = " ".join(filter(None, [artist_clean, fn_artist]))
        wl_local_folder, wl_local_artist = _find_in_whitelist(search_local, cfg["whitelist_local"])
        if wl_local_folder:
            score += pos_scores.get("artist_whitelist_match", 30)
            signals.append(f"local_indonesia_artist_whitelist:{wl_local_artist}")
            resolved_folder = wl_local_folder
            resolved_media  = "MUSIC"  # Artis Indonesia umum

    # ──────────────────────────────────────────────
    # STAGE 4 — MUSIK UMUM (FALLBACK)
    # ──────────────────────────────────────────────
    if not resolved_folder:
        resolved_media = "MUSIC"
        resolved_folder = rules_cfg.get("default_music_folder", "01_MASTER_MUSIC/10_UNKNOWN_RELEASE_TYPE")

    # ──────────────────────────────────────────────
    # STAGE 4b — AKUMULASI SKOR UMUM
    # ──────────────────────────────────────────────
    dangerous_cfg = cfg["dangerous"]

    # Skor pola Artist - Title (gunakan has_pattern yang sudah dihitung di Stage 3)
    if has_pattern:
        score += pos_scores.get("filename_artist_title_pattern", 20)
        signals.append(f"filename_artist_title_pattern:{fn_artist}")
    else:
        if resolved_media in ("MUSIC", "INTERNATIONAL_MUSIC", "LOCAL_REGIONAL_MUSIC"):
            score += neg_scores.get("no_artist_title_pattern", -25)
            warnings.append("no_artist_title_pattern")

    # Skor nama file ambigu
    is_ambig, ambig_reason = _is_ambiguous_filename(filename, dangerous_cfg)
    if is_ambig:
        score += neg_scores.get("ambiguous_filename", -40)
        warnings.append(f"AMBIGUOUS_FILENAME:{ambig_reason}")
        conflicts.append("AMBIGUOUS_FILENAME")

    # Skor tag metadata valid
    invalid_markers = {"unknown", "various", "vario", "untitled", "track", ""}
    artist_valid = artist_clean.lower() not in invalid_markers and len(artist_clean) > 1
    title_valid  = title_clean.lower()  not in invalid_markers and len(title_clean)  > 1

    if artist_valid and title_valid:
        score += pos_scores.get("valid_metadata_artist_title", 25)
        signals.append("valid_metadata_artist_title")
    elif artist_valid or title_valid:
        # Satu dari dua valid — setengah poin
        score += pos_scores.get("valid_metadata_artist_title", 25) // 2
        signals.append("partial_metadata_valid")
    else:
        # Cek apakah artis dari whitelist (artis terkenal dari nama file)
        has_known = any(
            "whitelist" in s or "local_artist" in s
            for s in signals
        )
        if has_known:
            score += neg_scores.get("missing_both_tags_with_known_artist", -5)
            warnings.append("missing_both_tags (artis dikenali dari nama file)")
        elif resolved_media in ("RELIGIOUS_MUSIC", "RELIGIOUS_NON_MUSIC"):
            # Untuk religi: tidak penalti berat missing tags
            warnings.append("missing_both_tags (konten religi, tidak penalti berat)")
        else:
            score += neg_scores.get("missing_both_tags", -20)
            warnings.append("MISSING_BOTH_TAGS")

    # Skor genre tag
    if genre_clean:
        # Untuk religi dan lokal, genre tag sudah dihitung di stage sebelumnya
        if resolved_media not in ("RELIGIOUS_MUSIC", "RELIGIOUS_NON_MUSIC", "LOCAL_REGIONAL_MUSIC"):
            score += pos_scores.get("genre_tag_strong_match", 20)
            signals.append(f"genre_tag:{genre_clean}")
    else:
        # Jangan penalti genre_unknown untuk konten religi (sudah punya keyword kuat)
        if resolved_media not in ("RELIGIOUS_MUSIC", "RELIGIOUS_NON_MUSIC"):
            score += neg_scores.get("genre_unknown", -5)
            warnings.append("genre_unknown")

    # Skor tahun
    if year_tag and re.match(r'^\d{4}$', str(year_tag).strip()):
        signals.append(f"year_tag:{year_tag}")
    else:
        # Jangan penalti year_unknown untuk konten religi dan lokal
        if resolved_media not in ("RELIGIOUS_MUSIC", "RELIGIOUS_NON_MUSIC", "LOCAL_REGIONAL_MUSIC"):
            score += neg_scores.get("year_unknown", -5)
            warnings.append("year_unknown")

    # Deteksi bahasa untuk koreksi folder internasional
    lang_text = f"{artist_clean} {title_clean}" or os.path.splitext(filename)[0]
    lang = _detect_language(lang_text, cfg["international"])
    if lang == "EN" and resolved_media == "MUSIC":
        # Hanya upgrade ke internasional jika ada bukti pendukung
        score += pos_scores.get("english_title_short", 5)
        signals.append(f"language_detection:EN")
        warnings.append("Bahasa Inggris terdeteksi tapi belum cukup bukti artis internasional")
    elif lang == "ID":
        signals.append("language_detection:ID")

    # Parent folder sebagai hint lemah
    if parent_folder and parent_folder not in [".", "", "input", "data"]:
        score += pos_scores.get("parent_folder_hint", 8)
        signals.append(f"parent_folder_hint:{parent_folder}")

    # Konflik keyword berbahaya
    dangerous_kws = dangerous_cfg.get("dangerous_standalone_keywords", [])
    found_dk, dk_kw = _contains_any(filename, dangerous_kws)
    if found_dk and not has_pattern:
        score += neg_scores.get("dangerous_keyword_only", -30)
        warnings.append(f"DANGEROUS_KEYWORD_ONLY:{dk_kw}")
        conflicts.append("DANGEROUS_KEYWORD_PRESENT")

    # ──────────────────────────────────────────────
    # STAGE 5 — CONFLICT DETECTION & FINAL DECISION
    # ──────────────────────────────────────────────
    # Deteksi konflik metadata vs filename
    if has_pattern and artist_valid and title_valid:
        a_fn_n  = _normalize(fn_artist)
        a_tag_n = _normalize(artist_clean)
        if len(a_tag_n) > 3 and len(a_fn_n) > 3 and a_tag_n not in a_fn_n and a_fn_n not in a_tag_n:
            conflicts.append("METADATA_FILENAME_CONFLICT")
            score += neg_scores.get("metadata_filename_conflict", -35)
            warnings.append(f"METADATA_FILENAME_CONFLICT: tag='{artist_clean}' vs file='{fn_artist}'")

    # Deteksi konflik durasi vs tipe musik
    if dur > 0 and resolved_media in ("MUSIC", "LOCAL_REGIONAL_MUSIC", "INTERNATIONAL_MUSIC", "RELIGIOUS_MUSIC"):
        song_min = dur_rules.get("song_min_seconds", 120)
        song_max = dur_rules.get("song_max_seconds", 480)
        if dur < song_min:
            warnings.append(f"Durasi {dur:.0f}s lebih pendek dari lagu normal (min {song_min}s)")
            if dur < dur_rules.get("sfx_max_seconds", 10):
                conflicts.append("DURATION_CATEGORY_CONFLICT")
                score += neg_scores.get("duration_category_conflict", -30)

    # Clamp skor
    final_score = max(0, min(100, score))

    # Tentukan decision & routing
    auto_thresh   = rules_cfg.get("confidence_thresholds", {}).get("auto_sort", 85)
    review_thresh = rules_cfg.get("confidence_thresholds", {}).get("review_with_suggestion", 60)
    review_sub    = cfg["review"].get("review_subfolders", {})

    has_heavy_conflict = "METADATA_FILENAME_CONFLICT" in conflicts

    if "AMBIGUOUS_FILENAME" in conflicts or is_ambig:
        decision = "NEEDS_REVIEW"
        review_folder = review_sub.get("unknown_artist_title", "90_NEEDS_REVIEW/01_UNKNOWN_ARTIST_TITLE")
    elif has_heavy_conflict:
        decision = "NEEDS_REVIEW"
        review_folder = review_sub.get("metadata_filename_conflict", "90_NEEDS_REVIEW/05_METADATA_FILENAME_CONFLICT")
    elif "DANGEROUS_KEYWORD_PRESENT" in conflicts and not has_pattern:
        decision = "NEEDS_REVIEW"
        review_folder = review_sub.get("unknown_artist_title", "90_NEEDS_REVIEW/01_UNKNOWN_ARTIST_TITLE")
    elif "LOCAL_INSUFFICIENT_EVIDENCE" in warnings:
        decision = "REVIEW_WITH_SUGGESTION"
        review_folder = review_sub.get("local_language_uncertain", "90_NEEDS_REVIEW/07_LOCAL_LANGUAGE_UNCERTAIN")
    elif resolved_media in ("RELIGIOUS_MUSIC", "RELIGIOUS_NON_MUSIC") and final_score >= 20:
        # Konten religi dengan keyword kuat: minimal REVIEW_WITH_SUGGESTION
        if final_score >= auto_thresh and not resolved_folder.startswith("90_NEEDS_REVIEW"):
            decision = "AUTO_SORT"
            review_folder = resolved_folder
        else:
            decision = "REVIEW_WITH_SUGGESTION"
            review_folder = review_sub.get("low_confidence", "90_NEEDS_REVIEW/02_LOW_CONFIDENCE_CATEGORY")
    elif resolved_media == "LOCAL_REGIONAL_MUSIC" and not resolved_folder.startswith("90_NEEDS_REVIEW"):
        # Lokal yang terdeteksi dengan cukup sinyal
        if final_score >= auto_thresh:
            decision = "AUTO_SORT"
            review_folder = resolved_folder
        elif final_score >= review_thresh:
            decision = "REVIEW_WITH_SUGGESTION"
            review_folder = review_sub.get("low_confidence", "90_NEEDS_REVIEW/02_LOW_CONFIDENCE_CATEGORY")
        else:
            # Score 50: masih berikan REVIEW_WITH_SUGGESTION untuk lokal yang sudah punya folder
            decision = "REVIEW_WITH_SUGGESTION"
            review_folder = review_sub.get("low_confidence", "90_NEEDS_REVIEW/02_LOW_CONFIDENCE_CATEGORY")
    elif final_score >= auto_thresh and not resolved_folder.startswith("90_NEEDS_REVIEW"):
        decision = "AUTO_SORT"
        review_folder = resolved_folder
    elif final_score >= review_thresh:
        decision = "REVIEW_WITH_SUGGESTION"
        if len(conflicts) > 1:
            review_folder = review_sub.get("conflicting_signals", "90_NEEDS_REVIEW/03_CONFLICTING_SIGNALS")
        else:
            review_folder = review_sub.get("low_confidence", "90_NEEDS_REVIEW/02_LOW_CONFIDENCE_CATEGORY")
    else:
        decision = "NEEDS_REVIEW"
        if conflicts:
            review_folder = review_sub.get("conflicting_signals", "90_NEEDS_REVIEW/03_CONFLICTING_SIGNALS")
        elif "MISSING_BOTH_TAGS" in warnings:
            review_folder = review_sub.get("unknown_artist_title", "90_NEEDS_REVIEW/01_UNKNOWN_ARTIST_TITLE")
        else:
            review_folder = review_sub.get("low_confidence", "90_NEEDS_REVIEW/02_LOW_CONFIDENCE_CATEGORY")

    bucket = resolved_folder.split("/")[0] if "/" in resolved_folder else resolved_folder
    signal_str = "; ".join(signals[:5]) or "(tidak ada)"
    reason = f"[{decision}] Score={final_score}/100. Media={resolved_media}. Sinyal: {signal_str}."
    if warnings:
        reason += " Peringatan: " + " | ".join(warnings[:3])

    result.update({
        "media_type":       resolved_media,
        "master_bucket":    bucket,
        "target_folder":    resolved_folder,
        "review_folder":    review_folder,
        "confidence_score": final_score,
        "decision":         decision,
        "signals":          signals,
        "warnings":         warnings,
        "conflicts":        conflicts,
        "reason":           reason,
    })
    return result


# ══════════════════════════════════════════════════════════════════
# ALIAS BACKWARD-COMPATIBLE (v2.x)
# ══════════════════════════════════════════════════════════════════

def classify_audio(
    filename: str,
    artist_tag: str = "",
    title_tag: str = "",
    genre_tag: str = "",
    duration_seconds: float = 0.0,
    parent_folder: str = "",
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    [DEPRECATED] Alias backward-compat untuk classify_audio_file().
    Gunakan classify_audio_file() untuk kode baru.
    Mengembalikan output yang kompatibel dengan pemanggil v2.
    """
    result = classify_audio_file(
        filename=filename,
        parent_folder=parent_folder,
        duration_seconds=duration_seconds if duration_seconds > 0 else None,
        genre_tag=genre_tag,
        artist_tag=artist_tag,
        title_tag=title_tag,
        config=config,
    )
    # Tambah kunci lama yang mungkin masih dipakai
    result["suggested_folder"] = result["target_folder"]
    return result


# ══════════════════════════════════════════════════════════════════
# Helper publik untuk dipakai script lain
# ══════════════════════════════════════════════════════════════════

def _find_daerah_keyword(text: str, daerah_keywords: Dict[str, Any]) -> Tuple[str, str]:
    """[Backward compat] Wrapper untuk _find_local_keyword dengan format config lama."""
    folder, kw, _ = _find_local_keyword(text, {"strong_keywords": daerah_keywords})
    return folder, kw


def _find_known_artist(text: str, known_artists: Dict[str, Any]) -> Tuple[str, str]:
    """[Backward compat] Wrapper untuk _find_in_whitelist."""
    return _find_in_whitelist(text, known_artists)
