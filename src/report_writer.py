import os
import csv
import logging
from typing import List, Dict, Any

try:
    import pandas as pd
except ImportError:
    pd = None

def write_csv_report(data: List[Dict[str, Any]], file_path: str, columns: List[str]) -> bool:
    """Menulis daftar dictionary ke file CSV secara aman."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            for row in data:
                # Filter agar hanya menyimpan kolom yang didefinisikan
                clean_row = {col: row.get(col, "") for col in columns}
                writer.writerow(clean_row)
        return True
    except Exception as e:
        logging.error(f"Gagal menulis CSV report ke {file_path}: {e}")
        return False

def convert_csv_to_xlsx(csv_path: str, xlsx_path: str) -> bool:
    """Mengonversi file CSV menjadi file XLSX Excel menggunakan pandas."""
    if pd is None:
        logging.warning("Pustaka pandas tidak tersedia. Konversi CSV ke XLSX dilewati.")
        return False
        
    if not os.path.exists(csv_path):
        logging.error(f"File CSV sumber tidak ditemukan di {csv_path}")
        return False
        
    try:
        df = pd.read_csv(csv_path)
        df.to_excel(xlsx_path, index=False, sheet_name="Laporan Proses")
        return True
    except Exception as e:
        logging.error(f"Gagal mengonversi {csv_path} ke XLSX: {e}")
        return False

def write_final_summary_md(summary: Dict[str, Any], file_path: str) -> bool:
    """
    Menulis ringkasan eksekutif pemrosesan audio ke berkas final_summary.md
    menggunakan format Markdown bahasa Indonesia yang rapi.
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        md_content = f"""# Laporan Ringkasan Eksekutif — RADIO_MUSIC_CLEANER

**ID Batch**: `{summary.get("batch_id", "N/A")}`  
**Waktu Proses**: {summary.get("processed_at", "N/A")}  
**Status Eksekusi**: `{summary.get("execution_mode", "DRY_RUN")}`

---

## Ringkasan Statistik File

| Kategori Pengukuran | Jumlah File | Keterangan |
| :--- | :---: | :--- |
| **Total File Ditemukan** | {summary.get("total_files", 0)} | Seluruh file di folder input |
| **Total Audio Terdeteksi** | {summary.get("total_audio", 0)} | File dengan ekstensi audio valid |
| **Berhasil Dipindai (Scan)** | {summary.get("scanned_success", 0)} | File audio yang sukses dibaca metadatanya |
| **Gagal Dipindai (Scan Error)** | {summary.get("scanned_error", 0)} | File audio corrupt atau rusak |
| **Berhasil Disalin & Rename** | {summary.get("renamed_success", 0)} | Salinan bersih yang berhasil dibuat |
| **Tag Metadata Ditulis** | {summary.get("metadata_written", 0)} | File yang metadata dasarnya diisi |
| **Berhasil Disortir** | {summary.get("sorted_success", 0)} | File yang telah dipindahkan ke folder kategori |
| **Ambigu (Perlu Dicek)** | {summary.get("needs_review", 0)} | File yang diragukan dan masuk folder `90_PERLU_DICEK` |
| **Dugaan Duplikat** | {summary.get("duplicates_suspect", 0)} | File yang diidentifikasi sebagai duplikat |
| **Audio Bermasalah** | {summary.get("bad_audio", 0)} | File corrupt/rusak yang disendirikan |

---

## Detail Lokasi Hasil & Laporan

* **Folder Library Output**:  
  `{summary.get("output_library_path", "N/A")}`
* **Laporan Scan Library (CSV/XLSX)**:  
  `{summary.get("scan_report_path", "N/A")}`
* **Laporan Simulasi Rename (CSV/XLSX)**:  
  `{summary.get("preview_report_path", "N/A")}`
* **Laporan Penulisan Tag (CSV/XLSX)**:  
  `{summary.get("metadata_report_path", "N/A")}`
* **Laporan Sortir Folder (CSV/XLSX)**:  
  `{summary.get("sorting_report_path", "N/A")}`
* **Laporan Dugaan Duplikat (CSV)**:  
  `{summary.get("duplicates_report_path", "N/A")}`
* **Laporan Validasi Kualitas QA**:  
  `{summary.get("validation_report_path", "N/A")}`

---

## Catatan Operator / Rekomendasi Tindakan

1. **Pemeriksaan Manual**: Harap periksa file di folder `{summary.get("needs_review_folder_name", "90_PERLU_DICEK")}` untuk memastikan apakah file tersebut merupakan lagu resmi, rekaman program, atau iklan yang salah format.
2. **Penanganan Duplikat**: File duplikat yang tercantum di `{summary.get("duplicates_report_name", "possible_duplicates_report.csv")}` tidak dihapus secara otomatis. Silakan audit secara manual menggunakan bantuan Mp3tag.
3. **Finishing Metadata**: Sangat direkomendasikan membuka folder output library menggunakan **Mp3tag** untuk melengkapi tag metadata (seperti cover art dan tahun rilis resmi) secara massal.

---
*Laporan ini dibuat otomatis oleh RADIO_MUSIC_CLEANER.*
"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        return True
    except Exception as e:
        logging.error(f"Gagal menulis ringkasan Markdown ke {file_path}: {e}")
        return False
