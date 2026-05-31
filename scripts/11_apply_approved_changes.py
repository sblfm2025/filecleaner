"""
scripts/11_apply_approved_changes.py — Skrip CLI Eksekusi Persetujuan v4.0
========================================================================
Menerapkan seluruh perubahan nama berkas fisik, alokasi folder master,
dan penulisan tag metadata yang telah disetujui (APPROVED/EDITED) oleh operator.

Pagar Pengaman:
  - Menyimpan manifest rollback untuk memulihkan file jika terjadi kesalahan.
  - Mencatat setiap aktivitas penulisan berkas ke audit log operasi.
"""

import os
import sys
import csv
import logging
from typing import List, Dict, Any

# Pastikan root workspace masuk sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import setup_logger, load_json_config
from src.audio_reader import read_audio_metadata
from src.metadata_writer import write_basic_metadata
from src.safe_file_ops import safe_copy_file
from src.naming_template_engine import format_filename_by_template
from src.operation_log import log_operation
from src.rollback_manager import write_to_rollback_manifest
from src.report_writer import write_csv_report, convert_csv_to_xlsx

logger = logging.getLogger("RADIO_MUSIC_CLEANER")


def apply_approved_changes(
    final_output_dir: str = "data/output/RADIO_AUDIO_MASTER_LIBRARY",
    logs_dir: str = "data/logs"
) -> Dict[str, Any]:
    """
    Memproses dan mengeksekusi seluruh antrean berkas yang berstatus APPROVED atau EDITED.
    """
    logger.info("======================================================================")
    logger.info("      MEMULAI EKSEKUSI PERSETUJUAN PERUBAHAN FISIK v4.0")
    logger.info("======================================================================")

    review_queue_path = os.path.join(logs_dir, "review_queue.csv")
    if not os.path.exists(review_queue_path):
        logger.error(f"[APPLY] Berkas review_queue.csv tidak ditemukan di {review_queue_path}. Silakan susun antrean review dahulu.")
        return {"total_processed": 0, "success_count": 0, "failed_count": 0}

    # 1. Baca seluruh antrean review
    review_records: List[Dict[str, Any]] = []
    try:
        with open(review_queue_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            review_records = list(reader)
    except Exception as e:
        logger.error(f"[APPLY] Gagal membaca antrean review: {e}")
        return {"total_processed": 0, "success_count": 0, "failed_count": 0}

    # Saring file yang siap di-apply (APPROVED atau EDITED)
    target_records = [
        r for r in review_records 
        if r.get("status") in ("APPROVED", "EDITED")
    ]

    total_target = len(target_records)
    logger.info(f"Ditemukan {total_target} berkas yang telah disetujui (APPROVED/EDITED) untuk dieksekusi.")

    if total_target == 0:
        logger.info("Selesai: Tidak ada berkas baru yang disetujui untuk di-apply.")
        return {"total_processed": 0, "success_count": 0, "failed_count": 0}

    # Muat aturan metadata defaults
    meta_defaults = load_json_config("config/metadata_defaults.json", {})
    naming_rules = load_json_config("config/cleaner_rules.json", {})

    success_count = 0
    failed_count = 0

    # 2. Proses eksekusi modifikasi berkas
    for idx, row in enumerate(target_records, 1):
        file_id = row.get("file_id", "")
        file_path = row.get("file_path", "")
        filename = row.get("filename", "")
        status = row.get("status", "")
        
        # Ambil usulan metadata
        suggested_artist = row.get("suggested_artist", "")
        suggested_title = row.get("suggested_title", "")
        suggested_album = row.get("suggested_album", "")
        suggested_year = row.get("suggested_year", "")
        media_type = row.get("media_type", "MUSIC")
        
        # Tujuan target folder
        dest_folder_rel = row.get("target_folder_suggestion", "01_MASTER_MUSIC/10_UNKNOWN_RELEASE_TYPE")
        dest_dir = os.path.join(final_output_dir, dest_folder_rel)

        if not os.path.exists(file_path):
            logger.error(f"Berkas sumber tidak ditemukan: {file_path}")
            row["status"] = "FAILED"
            row["operator_notes"] = "Gagal: Berkas sumber di disk tidak ditemukan."
            failed_count += 1
            continue

        # Baca metadata lama sebelum ditulis (sebagai backup untuk rollback)
        old_meta = read_audio_metadata(file_path)

        # 3. Formulasi nama berkas tujuan menggunakan naming template
        meta_to_format = {
            "artist_tag": suggested_artist if suggested_artist else old_meta.get("artist_tag", ""),
            "title_tag": suggested_title if suggested_title else old_meta.get("title_tag", ""),
            "album_tag": suggested_album if suggested_album else old_meta.get("album_tag", ""),
            "year_tag": suggested_year if suggested_year else old_meta.get("year_tag", ""),
            "genre_tag": old_meta.get("genre_tag", "")
        }

        # Gunakan nama file yang sudah bersih, atau susun ulang berdasarkan tag baru
        new_filename = format_filename_by_template(
            template="%artist% - %title%%ext%",
            metadata=meta_to_format,
            original_filename=filename
        )

        # 4. Salin/Pindahkan fisik file secara aman (No Overwrite, No Delete otomatis)
        os.makedirs(dest_dir, exist_ok=True)
        actual_dest_path, copy_res = safe_copy_file(file_path, dest_dir, new_filename)

        if copy_res != "SUCCESS":
            logger.error(f"Gagal menyalin fisik berkas {filename}: {copy_res}")
            row["status"] = "FAILED"
            row["operator_notes"] = f"Gagal menyalin berkas: {copy_res}"
            failed_count += 1
            continue

        # 5. Tulis metadata baru ke berkas tujuan secara aman
        # Pagar Pengaman: Jangan tulis tag lagu untuk tipe non-musik stasiun radio
        is_non_music = media_type in ("RADIO_ASSET", "COMMERCIAL_AD", "PUBLIC_SERVICE", "INSTRUMENTAL_BED", "PROGRAM_RECORDING")
        
        if is_non_music:
            write_status = "SUCCESS"
            write_notes = "Tag dilewati aman untuk tipe non-musik."
        else:
            # Tentukan genre berdasarkan alokasi folder master
            suggested_genre = ""
            if "02_MASTER_LOCAL_REGIONAL" in dest_folder_rel:
                suggested_genre = meta_defaults.get("default_genre_local", "Musik Lokal Daerah")
            elif "01_MASTER_MUSIC" in dest_folder_rel:
                suggested_genre = meta_defaults.get("default_genre_music", "Musik")
            elif "04_MASTER_INTERNATIONAL" in dest_folder_rel:
                suggested_genre = meta_defaults.get("default_genre_intl", "Musik Internasional")
            elif "03_MASTER_RELIGIOUS" in dest_folder_rel:
                suggested_genre = meta_defaults.get("default_genre_religious", "Musik Religi")

            write_status, write_notes = write_basic_metadata(
                actual_dest_path,
                artist=suggested_artist if suggested_artist else old_meta.get("artist_tag", ""),
                title=suggested_title if suggested_title else old_meta.get("title_tag", ""),
                defaults=meta_defaults,
                suggested_genre=suggested_genre
            )

        if write_status != "SUCCESS":
            logger.error(f"Gagal menulis tag metadata ke {new_filename}: {write_notes}")
            # Hapus berkas tujuan yang gagal ditulis tag-nya agar tidak meninggalkan sampah
            try:
                os.remove(actual_dest_path)
            except OSError:
                pass
            row["status"] = "FAILED"
            row["operator_notes"] = f"Gagal menulis metadata: {write_notes}"
            failed_count += 1
            continue

        # 6. Catat log operasi atomik keselamatan data
        new_meta = read_audio_metadata(actual_dest_path)
        
        op_id = log_operation(
            logs_dir=logs_dir,
            file_id=file_id,
            operation_type="COPY_RENAME_TAG",
            source_path=file_path,
            target_path=actual_dest_path,
            old_filename=filename,
            new_filename=new_filename,
            old_tags={
                "artist_tag": old_meta.get("artist_tag", ""),
                "title_tag": old_meta.get("title_tag", ""),
                "album_tag": old_meta.get("album_tag", ""),
                "genre_tag": old_meta.get("genre_tag", ""),
                "year_tag": old_meta.get("year_tag", "")
            },
            new_tags={
                "artist_tag": new_meta.get("artist_tag", ""),
                "title_tag": new_meta.get("title_tag", ""),
                "album_tag": new_meta.get("album_tag", ""),
                "genre_tag": new_meta.get("genre_tag", ""),
                "year_tag": new_meta.get("year_tag", "")
            },
            decision_source="OPERATOR_APPROVED" if status == "APPROVED" else "OPERATOR_EDITED",
            confidence_score=100.0,
            operator="OPERATOR"
        )

        # 7. Catat manifest pemulihan (rollback manager)
        if op_id:
            write_to_rollback_manifest(
                logs_dir=logs_dir,
                operation_id=op_id,
                file_id=file_id,
                current_path=actual_dest_path,
                original_source_path=file_path,
                original_filename=filename,
                original_tags={
                    "artist_tag": old_meta.get("artist_tag", ""),
                    "title_tag": old_meta.get("title_tag", ""),
                    "album_tag": old_meta.get("album_tag", ""),
                    "genre_tag": old_meta.get("genre_tag", ""),
                    "year_tag": old_meta.get("year_tag", "")
                }
            )

        # Perbarui status di review_queue manifest menjadi APPLIED
        row["status"] = "APPLIED"
        row["operator_decision"] = "APPLIED"
        row["operator_notes"] = f"Sukses di-apply ke {dest_folder_rel} | Log: {op_id}"
        success_count += 1

        if idx % 50 == 0 or idx == total_target:
            logger.info(f"[APPLY] Mengeksekusi modifikasi {idx}/{total_target} berkas...")

    # 8. Tulis kembali perubahan ke antrean review_queue.csv/xlsx di disk
    # Baca entri review queue asli untuk menggabungkan status update-nya
    full_queue_records: List[Dict[str, Any]] = []
    try:
        with open(review_queue_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                # Sinkronkan data status yang ter-apply
                for tg in target_records:
                    if tg.get("file_id") == r.get("file_id"):
                        r["status"] = tg["status"]
                        r["operator_decision"] = tg["operator_decision"]
                        r["operator_notes"] = tg["operator_notes"]
                        break
                full_queue_records.append(r)
    except Exception as e:
        logger.error(f"[APPLY] Gagal mensinkronkan status review queue: {e}")

    write_csv_report(full_queue_records, review_queue_path, REVIEW_COLUMNS)
    convert_csv_to_xlsx(review_queue_path, review_queue_path.replace(".csv", ".xlsx"))

    logger.info("======================================================================")
    logger.info("                      RINGKASAN EKSEKUSI PERSETUJUAN")
    logger.info("======================================================================")
    logger.info(f"Total Target Di-apply  : {total_target}")
    logger.info(f"Eksekusi Sukses        : {success_count}")
    logger.info(f"Eksekusi Gagal         : {failed_count}")
    logger.info("======================================================================")

    return {
        "total_processed": total_target,
        "success_count": success_count,
        "failed_count": failed_count
    }


if __name__ == "__main__":
    setup_logger()
    apply_approved_changes()
