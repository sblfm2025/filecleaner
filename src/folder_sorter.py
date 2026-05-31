import os
import re
from typing import Dict, Any, Tuple

def is_likely_english_text(text: str) -> bool:
    """Mendeteksi apakah teks kemungkinan besar berbahasa Inggris berdasarkan kata kunci umum."""
    if not text:
        return False
        
    # Bersihkan teks dari karakter non-alfabet
    words = set(re.sub(r'[^a-zA-Z\s]', '', text.lower()).split())
    
    # Kata-kata bahasa Inggris yang sangat umum (stopwords)
    english_stopwords = {
        "the", "you", "me", "i", "love", "my", "your", "it", "on", "to", "for", "with", 
        "is", "are", "am", "was", "were", "that", "this", "have", "has", "had", "dont", "cant",
        "of", "in", "at", "by", "about", "we", "he", "she", "they", "them", "his", "her",
        "go", "come", "do", "will", "would", "should", "could", "all", "no", "yes", "not",
        "up", "down", "out", "so", "workout", "instrumental", "sound", "track", "music", "song"
    }
    
    # Kata-kata bahasa Indonesia yang sangat umum dan khas
    indonesian_stopwords = {
        "yang", "dan", "di", "ke", "dari", "untuk", "dengan", "pada", "oleh", "ini", "itu",
        "aku", "kamu", "dia", "mereka", "kita", "kami", "kau", "cinta", "hati", "jiwa", "rindu",
        "kasih", "sayang", "jangan", "bisa", "ada", "tidak", "ya", "sudah", "belum", "adalah"
    }
    
    english_count = len(words.intersection(english_stopwords))
    indonesian_count = len(words.intersection(indonesian_stopwords))
    
    # Jika mengandung kata Inggris lebih banyak dan tidak didominasi kata Indonesia
    if english_count > 0 and english_count >= indonesian_count:
        return True
    return False

def determine_target_folder(
    filename: str,
    genre_tag: str,
    artist_tag: str,
    title_tag: str,
    mapping_config: Dict[str, Any],
    parent_folder: str = ""
) -> Tuple[str, str]:
    """
    Menentukan folder target relatif di dalam RADIO_AUDIO_LIBRARY berdasarkan:
    1. Nama folder induk (Parent folder di input)
    2. Prefix nama file
    3. Kata kunci nama file
    4. Tag genre
    5. Deteksi kejelasan Artist/Title (fallback default musik vs perlu dicek)
    
    Mengembalikan tuple: (folder_tujuan_relatif, alasan_pencocokan)
    """
    prefix_mapping = mapping_config.get("prefix_mapping", {})
    keyword_mapping = mapping_config.get("keyword_mapping", {})
    default_music = mapping_config.get("default_music_folder", "02_MUSIK_INDONESIA/Pop_Indonesia")
    needs_review = mapping_config.get("needs_review_folder", "90_PERLU_DICEK")
    
    filename_lower = filename.lower()
    genre_lower = genre_tag.lower() if genre_tag else ""
    parent_lower = parent_folder.lower() if parent_folder else ""
    
    # Deteksi bahasa Inggris awal untuk alih genre internasional cerdas
    text_to_check = ""
    if title_tag:
        text_to_check += " " + title_tag
    if artist_tag:
        text_to_check += " " + artist_tag
    if not text_to_check.strip():
        text_to_check = filename_lower
        
    is_eng = is_likely_english_text(text_to_check)
    fallback_map = mapping_config.get("international_genre_fallback", {})
    
    def resolve_folder(folder: str) -> Tuple[str, str]:
        if is_eng and folder in fallback_map:
            return fallback_map[folder], " (dialihkan ke internasional)"
        return folder, ""
        
    # 1. Cek berdasarkan Kata Kunci Folder Induk (Parent Folder) - Prioritas Utama
    if parent_lower:
        for keyword, target_folder in keyword_mapping.items():
            if keyword.lower() in parent_lower:
                resolved_folder, note = resolve_folder(target_folder)
                return resolved_folder, f"Cocok dengan kata kunci folder induk '{keyword}'{note}"
            
    # 2. Cek berdasarkan Prefix Nama File (case-insensitive)
    for prefix, target_folder in prefix_mapping.items():
        if filename_lower.startswith(prefix.lower()):
            resolved_folder, note = resolve_folder(target_folder)
            return resolved_folder, f"Cocok dengan prefix '{prefix}'{note}"
            
    # 3. Cek berdasarkan Kata Kunci Nama File (case-insensitive)
    for keyword, target_folder in keyword_mapping.items():
        if keyword.lower() in filename_lower:
            resolved_folder, note = resolve_folder(target_folder)
            return resolved_folder, f"Cocok dengan kata kunci nama file '{keyword}'{note}"
            
    # 4. Cek berdasarkan Tag Genre
    if genre_lower:
        for keyword, target_folder in keyword_mapping.items():
            if keyword.lower() in genre_lower:
                resolved_folder, note = resolve_folder(target_folder)
                return resolved_folder, f"Cocok dengan kata kunci genre tag '{keyword}'{note}"

    # 5. Filter file ambigu
    # Daftar nama file yang dianggap ambigu
    ambiguous_patterns = [
        "track", "audio", "whatsapp", "unknown", "recording", "voice", "lagu viral",
        "lagu baru", "video", "download", "converted", "copy", "salinan"
    ]
    
    is_ambiguous = False
    name_without_ext, _ = os.path.splitext(filename_lower)
    reason_ambiguous = ""
    
    # Cek apakah file memiliki tag metadata yang valid
    has_valid_metadata = False
    if artist_tag and title_tag:
        a_clean = artist_tag.strip().lower()
        t_clean = title_tag.strip().lower()
        # Jika artis dan judul diisi secara valid (bukan kata "unknown" atau dummy)
        if a_clean and t_clean and not any(pat in a_clean for pat in ["unknown", "vario", "various"]):
            has_valid_metadata = True

    # Jika tidak memiliki metadata valid, jalankan pengecekan nama berkas fisik
    if not has_valid_metadata:
        # Jika tidak ada pola Artist - Title (tanda hubung)
        if "-" not in filename:
            is_ambiguous = True
            reason_ambiguous = "Tidak ada separator Artis - Judul dan tag metadata kosong"
        else:
            # Periksa bagian-bagiannya
            parts = filename.split("-", 1)
            artist_part = parts[0].strip()
            title_part = parts[1].strip()
            
            # Jika salah satu kosong atau mengandung kata ambigu
            if not artist_part or not title_part:
                is_ambiguous = True
                reason_ambiguous = "Nama artis atau judul kosong"
            elif any(pat in artist_part.lower() for pat in ["unknown", "track", "audio"]):
                is_ambiguous = True
                reason_ambiguous = f"Artis tidak jelas ('{artist_part}')"
            elif any(pat in title_part.lower() for pat in ["track", "audio", "whatsapp"]):
                is_ambiguous = True
                reason_ambiguous = f"Judul tidak jelas ('{title_part}')"
            else:
                reason_ambiguous = ""

        # Cek jika nama file sangat mencurigakan
        for pattern in ambiguous_patterns:
            if name_without_ext == pattern or name_without_ext.startswith(pattern + " "):
                is_ambiguous = True
                reason_ambiguous = f"Nama file diawali kata ambigu '{pattern}'"
                break

    # 6. Keputusan Fallback
    if is_ambiguous:
        return needs_review, f"File ambigu: {reason_ambiguous}"
    else:
        if is_eng:
            resolved_folder, note = resolve_folder(default_music)
            return resolved_folder, f"Terdeteksi kemungkinan besar lagu internasional (bahasa Inggris){note}"
            
        # Jika file memiliki pola Artist - Title yang jelas atau metadata yang valid, default masuk Pop Indonesia
        return default_music, "Fallback default musik Indonesia (pola Artis - Judul jelas atau metadata valid)"
