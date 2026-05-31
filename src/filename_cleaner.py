import os
import re
import logging
from typing import Dict, Any, Tuple

def safe_title_case(text: str) -> str:
    """
    Mengubah teks menjadi format Title Case yang cerdas dan aman untuk nama file audio.
    Mempertahankan kata singkatan (seperti SBL, RRI, ILM, TV) tetap huruf besar,
    dan mengecilkan kata hubung tertentu jika berada di tengah kalimat.
    """
    if not text:
        return ""
        
    words = text.split()
    capitalized_words = []
    
    # Daftar kata hubung/partikel yang sebaiknya huruf kecil jika tidak di awal/akhir
    lowercase_words = {
        "dan", "atau", "di", "ke", "dari", "yang", "untuk", "dengan", "pada", "oleh",
        "vs", "feat", "ft", "by", "the", "a", "an", "and", "or", "in", "on", "at", "of", "to", "for"
    }
    
    for i, word in enumerate(words):
        word_clean = re.sub(r'[^a-zA-Z0-9]', '', word)
        
        # Jika kata adalah singkatan (misalnya SBL, ILM, RRI)
        if word_clean.isupper() and len(word_clean) <= 4:
            capitalized_words.append(word)
        # Kata pertama dan kata terakhir selalu dikapitalisasi
        elif i == 0 or i == len(words) - 1:
            # Menangani kata yang diawali tanda kurung
            if word.startswith(('(', '[', '{')):
                capitalized_words.append(word[0] + word[1:].capitalize())
            else:
                capitalized_words.append(word.capitalize())
        # Kata hubung di tengah kalimat diubah menjadi huruf kecil
        elif word.lower() in lowercase_words:
            capitalized_words.append(word.lower())
        else:
            # Kapitalisasi kata biasa, menangani tanda hubung internal seperti dangdut-koplo
            if '-' in word:
                parts = [p.capitalize() for p in word.split('-')]
                capitalized_words.append('-'.join(parts))
            elif word.startswith(('(', '[', '{')):
                capitalized_words.append(word[0] + word[1:].capitalize())
            else:
                capitalized_words.append(word.capitalize())
                
    return " ".join(capitalized_words)

def clean_filename(
    filename: str, 
    rules: Dict[str, Any],
    artist_tag: str = "",
    title_tag: str = ""
) -> Tuple[str, str, str, str]:
    """
    Membersihkan nama file berdasarkan aturan konfigurasi JSON.
    Mengembalikan tuple: (new_filename_suggestion, detected_artist, detected_title, change_reason)
    """
    # 1. Pisahkan nama file dari ekstensi
    name_part, ext = os.path.splitext(filename)
    original_name_part = name_part
    reasons = []
    
    # Ambil aturan dari config
    remove_phrases = rules.get("remove_phrases", [])
    replace_chars = rules.get("replace_chars", {})
    remove_brackets = rules.get("remove_brackets_content_when_contains", [])
    preserve_brackets = rules.get("preserve_brackets_content_when_contains", [])
    forbidden_chars = rules.get("windows_forbidden_chars", ["<", ">", ":", "\"", "/", "\\", "|", "?", "*"])
    max_length = rules.get("max_filename_length", 180)

    # 2. Deteksi & Hapus Nama Situs / URL (Domain) secara dinamis
    domain_pattern = r'\b(?:www\.)?[a-zA-Z0-9\-]+\.(?:com|net|org|co|info|biz|cc|mobi|me|id|io|us|ca|xyz|top|site|club|app|fm)\b'
    domains = re.findall(domain_pattern, name_part, re.IGNORECASE)
    domain_removed = False
    for dom in domains:
        name_part = re.sub(re.escape(dom), '', name_part, flags=re.IGNORECASE)
        domain_removed = True
    if domain_removed:
        reasons.append("Nama situs web/domain dibersihkan")

    # 3. Deteksi & Hapus YouTube Video ID / Hash unik di akhir nama berkas (panjang 8-12 karakter) sebelum modifikasi karakter
    yt_match = re.search(r'-([a-zA-Z0-9_\-]{8,12})$', name_part)
    if yt_match:
        video_id = yt_match.group(1)
        # Memastikan bahwa ini adalah hash acak (campuran huruf besar, kecil, angka)
        if sum([any(c.isupper() for c in video_id), any(c.islower() for c in video_id), any(c.isdigit() for c in video_id)]) >= 2:
            name_part = name_part[:-(len(video_id) + 1)]
            reasons.append("ID unik unduhan Youtube dibersihkan")

    # 4. Ganti karakter berdasarkan replace_chars
    replaced = False
    for old_char, new_char in replace_chars.items():
        if old_char in name_part:
            name_part = name_part.replace(old_char, new_char)
            replaced = True
    if replaced:
        reasons.append("Karakter khusus diganti")

    # 5. Proses tanda kurung () dan []
    brackets_removed = False
    # regex untuk menangkap pasangan kurung biasa () dan kurung siku [] beserta isinya
    bracket_matches = re.findall(r'([\(\[][^\)\]]*[\)\]])', name_part)
    for match in bracket_matches:
        # ambil isi di dalam kurung
        content = match[1:-1].lower().strip()
        
        # Cek apakah mengandung frasa yang harus dihilangkan
        should_remove = False
        for phrase in remove_brackets:
            if phrase in content:
                should_remove = True
                break
                
        # Cek apakah mengandung frasa yang harus dipertahankan
        should_preserve = False
        for phrase in preserve_brackets:
            if phrase in content:
                should_preserve = True
                break
                
        if should_remove and not should_preserve:
            name_part = name_part.replace(match, "")
            brackets_removed = True
            
    if brackets_removed:
        reasons.append("Isi kurung tidak penting dihapus")

    # 6. Bersihkan sisa tanda kurung kosong [] atau () dan tanda hubung menggantung
    name_part = re.sub(r'\[\s*\]|\(\s*\)', '', name_part)
    name_part = re.sub(r'^[\s\-\_\.\,]+|[\s\-\_\.\,]+$', '', name_part)
    name_part = re.sub(r'\s*-\s*-+\s*', ' - ', name_part)

    # Rapikan spasi setelah pembersihan dinamis
    name_part = re.sub(r'\s+', ' ', name_part).strip()

    # 4. Hapus frasa kotor secara case-insensitive
    phrases_removed = False
    for phrase in remove_phrases:
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        if pattern.search(name_part):
            name_part = pattern.sub("", name_part)
            phrases_removed = True
            
    if phrases_removed:
        reasons.append("Frasa promosi/kotor dibersihkan")

    # 5. Hapus spasi ganda dan rapikan spasi di awal/akhir
    name_part = re.sub(r'\s+', ' ', name_part).strip()

    # 6. Inisialisasi awal variabel
    detected_artist = ""
    detected_title = ""
    
    # Deteksi berkas khusus WhatsApp
    is_whatsapp = False
    name_part_lower = name_part.lower()
    
    if "whatsapp" in name_part_lower or re.search(r'^(aud|ptt)-\d{8}-wa', name_part_lower):
        is_whatsapp = True
        detected_artist = "WHATSAPP"
        
        # Coba rapikan format berkas WA "AUD-YYYYMMDD-WAXXXX"
        wa_match = re.search(r'^(aud|ptt)-(\d{4})(\d{2})(\d{2})-wa(\d+)', name_part_lower)
        if wa_match:
            prefix, year, month, day, num = wa_match.groups()
            type_label = "Voice Note" if prefix == "ptt" else "Audio"
            name_part = f"WhatsApp {type_label} {year}-{month}-{day} (WA{num.zfill(4)})"
            reasons.append("Pola nama berkas WA didecode")
        else:
            # Rapikan format "WhatsApp Audio YYYY-MM-DD at HH.MM.SS"
            # Hapus bagian waktu "at HH.MM.SS" atau "at HH.MM"
            name_part_clean = re.sub(r'\s+at\s+\d{2}[\.\:\-]\d{2}([\.\:\-]\d{2})?', '', name_part, flags=re.IGNORECASE)
            name_part = safe_title_case(name_part_clean)
            reasons.append("Waktu berkas WA dibersihkan")
            
        detected_title = name_part
        
    # 6. Deteksi pola Artis - Judul (hanya jika bukan berkas WhatsApp)
    elif "-" in name_part:
        parts = name_part.split("-", 1)
        artist_part = parts[0].strip()
        title_part = parts[1].strip()
        
        # Pastikan kedua bagian tidak kosong
        if artist_part and title_part:
            detected_artist = safe_title_case(artist_part)
            detected_title = safe_title_case(title_part)
        else:
            detected_title = safe_title_case(name_part)
    else:
        detected_title = safe_title_case(name_part)

    # 6.5 Integrasikan tag metadata jika tag tersebut tersedia dan nama berkas tidak memiliki artis
    if not detected_artist and artist_tag and title_tag:
        a_tag_clean = artist_tag.strip()
        t_tag_clean = title_tag.strip()
        # Abaikan nilai tag dummy/default
        if a_tag_clean and t_tag_clean and not any(pat in a_tag_clean.lower() for pat in ["unknown", "vario", "various"]):
            detected_artist = safe_title_case(a_tag_clean)
            detected_title = safe_title_case(t_tag_clean)
            reasons.append("Nama berkas dilengkapi dari tag metadata")

    # Jika artis berhasil dideteksi/dilengkapi, susun nama berkas dengan pola Artis - Judul
    if detected_artist and detected_title:
        name_part = f"{detected_artist} - {detected_title}"
    elif detected_title:
        name_part = detected_title

    # 7. Bersihkan sisa karakter terlarang Windows
    forbidden_removed = False
    for char in forbidden_chars:
        if char in name_part:
            name_part = name_part.replace(char, "")
            forbidden_removed = True
    if forbidden_removed:
        reasons.append("Karakter terlarang Windows dihapus")

    # Rapikan kembali spasi setelah penghapusan karakter
    name_part = re.sub(r'\s+', ' ', name_part).strip()

    # 8. Batasi panjang nama file
    if len(name_part) > max_length:
        name_part = name_part[:max_length].strip()
        reasons.append("Panjang nama file dibatasi")

    # 9. Jika hasil akhir kosong, fallback ke nama asli yang dibersihkan dari forbidden chars
    if not name_part:
        name_part = "Cleaned_Audio"
        reasons.append("Fallback nama default karena hasil kosong")

    new_filename = f"{name_part}{ext.lower()}"
    change_reason = ", ".join(reasons) if reasons else "Nama file sudah bersih"

    return new_filename, detected_artist, detected_title, change_reason
