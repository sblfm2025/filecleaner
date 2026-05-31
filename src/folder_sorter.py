import os
from typing import Dict, Any, Tuple

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
    
    # 1. Cek berdasarkan Kata Kunci Folder Induk (Parent Folder) - Prioritas Utama
    if parent_lower:
        for keyword, target_folder in keyword_mapping.items():
            if keyword.lower() in parent_lower:
                return target_folder, f"Cocok dengan kata kunci folder induk '{keyword}'"
            
    # 2. Cek berdasarkan Prefix Nama File (case-insensitive)
    for prefix, target_folder in prefix_mapping.items():
        if filename_lower.startswith(prefix.lower()):
            return target_folder, f"Cocok dengan prefix '{prefix}'"
            
    # 3. Cek berdasarkan Kata Kunci Nama File (case-insensitive)
    for keyword, target_folder in keyword_mapping.items():
        if keyword.lower() in filename_lower:
            return target_folder, f"Cocok dengan kata kunci nama file '{keyword}'"
            
    # 4. Cek berdasarkan Tag Genre
    if genre_lower:
        for keyword, target_folder in keyword_mapping.items():
            if keyword.lower() in genre_lower:
                return target_folder, f"Cocok dengan kata kunci genre tag '{keyword}'"

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
        # Jika file memiliki pola Artist - Title yang jelas atau metadata yang valid, default masuk Pop Indonesia
        return default_music, "Fallback default musik (pola Artis - Judul jelas atau metadata valid)"
