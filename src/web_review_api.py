"""
src/web_review_api.py — Server API Tinjauan Lokal & Kontrol Backend v4.0
========================================================================
Menyediakan server API lokal portabel stasiun radio menggunakan http.server
bawaan Python guna melayani komunikasi interaktif antara dashboard.html
dengan disk lokal (audit logs, review queue, apply approved, & rollback).

Bebas Dependensi: 100% menggunakan pustaka standard Python.
Fitur Pendukung: Menyediakan CORS headers untuk komunikasi lintas domain.
"""

import os
import csv
import json
import logging
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, List, Tuple

# Import modular keselamatan data
from src.utils import load_json_config, setup_logger, import_module_by_path
from src.rollback_manager import execute_rollback_for_file
from src.review_queue import REVIEW_COLUMNS
from src.report_writer import write_csv_report, convert_csv_to_xlsx

# Impor dinamis untuk menghindari syntax error modul numerik
apply_approved_changes = import_module_by_path(
    "apply_approved_changes", 
    "scripts/11_apply_approved_changes.py"
).apply_approved_changes

logger = logging.getLogger("RADIO_MUSIC_CLEANER")

_PORT = 8000
_LOGS_DIR = "data/logs"
_FINAL_OUTPUT_DIR = "data/output/RADIO_AUDIO_MASTER_LIBRARY"
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class WebReviewAPIHandler(BaseHTTPRequestHandler):
    """
    Handler request HTTP kustom stasiun radio untuk menangani rute statis dashboard
    dan endpoints API review.
    """

    def _set_headers(self, status_code: int = 200, content_type: str = "application/json"):
        """Menyisipkan header respons HTTP standar dengan penanganan CORS lengkap."""
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        # CORS headers agar dashboard.html lokal (file:///) dapat berinteraksi
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        """Menangani kueri pre-flight CORS OPTIONS secara aman."""
        self._set_headers(200, "text/plain")

    def do_GET(self):
        """Menangani rute pencarian visual dashboard statis dan endpoints API GET."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        # ── Rute Statis: Menyajikan dashboard.html di http://localhost:8000/ ──
        if path in ("/", "/index.html", "/dashboard.html"):
            dashboard_path = os.path.join(_PROJECT_ROOT, "dashboard.html")
            if os.path.exists(dashboard_path):
                try:
                    with open(dashboard_path, mode='r', encoding='utf-8') as f:
                        content = f.read()
                    self._set_headers(200, "text/html; charset=utf-8")
                    self.wfile.write(content.encode('utf-8'))
                    return
                except Exception as e:
                    self.send_error(500, f"Gagal membaca dashboard: {e}")
                    return
            else:
                self.send_error(404, "Berkas dashboard.html tidak ditemukan di proyek root.")
                return

        # ── Endpoint API: GET /api/queue (Mengambil antrean tinjauan) ───────
        elif path == "/api/queue":
            queue_csv_path = os.path.join(_LOGS_DIR, "review_queue.csv")
            records = []
            if os.path.exists(queue_csv_path):
                try:
                    with open(queue_csv_path, mode='r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        records = list(reader)
                except Exception as e:
                    logger.error(f"[API] Gagal membaca review queue: {e}")
            
            self._set_headers(200)
            self.wfile.write(json.dumps(records).encode('utf-8'))
            return

        # ── Endpoint API: GET /api/logs (Mengambil log audit operasi) ───────
        elif path == "/api/logs":
            log_csv_path = os.path.join(_LOGS_DIR, "operation_log.csv")
            records = []
            if os.path.exists(log_csv_path):
                try:
                    with open(log_csv_path, mode='r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        records = list(reader)
                except Exception as e:
                    logger.error(f"[API] Gagal membaca log operasi: {e}")
            
            self._set_headers(200)
            self.wfile.write(json.dumps(records).encode('utf-8'))
            return

        self.send_error(404, "Rute GET tidak ditemukan.")

    def do_POST(self):
        """Menangani rute endpoints API POST untuk aksi operator."""
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        # Baca data body request JSON
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else "{}"
        
        try:
            req_body = json.loads(post_data) if post_data else {}
        except Exception:
            req_body = {}

        # ── Endpoint API: POST /api/action (Update keputusan operator) ──────
        if path == "/api/action":
            file_id = req_body.get("file_id")
            action = req_body.get("action")  # APPROVED, REJECTED, EDITED
            
            if not file_id or not action:
                self._set_headers(400)
                self.wfile.write(json.dumps({"status": "failed", "message": "file_id dan action wajib diisi."}).encode('utf-8'))
                return

            queue_csv_path = os.path.join(_LOGS_DIR, "review_queue.csv")
            if not os.path.exists(queue_csv_path):
                self._set_headers(404)
                self.wfile.write(json.dumps({"status": "failed", "message": "Review queue belum dibuat."}).encode('utf-8'))
                return

            # Baca, update status di memori, dan tulis kembali ke disk
            records: List[Dict[str, Any]] = []
            updated = False
            
            try:
                with open(queue_csv_path, mode='r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        if r.get("file_id") == file_id:
                            r["status"] = action
                            r["operator_decision"] = action
                            
                            # Update meta usulan jika disunting oleh operator (EDITED)
                            if action == "EDITED":
                                r["suggested_artist"] = req_body.get("suggested_artist", r["suggested_artist"])
                                r["suggested_title"] = req_body.get("suggested_title", r["suggested_title"])
                                r["suggested_album"] = req_body.get("suggested_album", r["suggested_album"])
                                r["suggested_year"] = req_body.get("suggested_year", r["suggested_year"])
                                r["target_folder_suggestion"] = req_body.get("target_folder_suggestion", r["target_folder_suggestion"])
                            
                            r["operator_notes"] = req_body.get("operator_notes", "Diperbarui via Web Dashboard.")
                            updated = True
                        records.append(r)
                
                if updated:
                    # Tulis kembali CSV & XLSX
                    write_csv_report(records, queue_csv_path, REVIEW_COLUMNS)
                    convert_csv_to_xlsx(queue_csv_path, queue_csv_path.replace(".csv", ".xlsx"))
                    logger.info(f"[API] Sukses memperbarui berkas {file_id} menjadi {action}")
                    self._set_headers(200)
                    self.wfile.write(json.dumps({"status": "success", "message": f"Berkas {file_id} berhasil diubah ke {action}."}).encode('utf-8'))
                else:
                    self._set_headers(404)
                    self.wfile.write(json.dumps({"status": "failed", "message": f"ID berkas {file_id} tidak ditemukan."}).encode('utf-8'))
            except Exception as e:
                logger.error(f"[API] Gagal memperbarui draf: {e}")
                self._set_headers(500)
                self.wfile.write(json.dumps({"status": "failed", "message": f"Server error: {e}"}).encode('utf-8'))
            return

        # ── Endpoint API: POST /api/apply (Eksekusi modifikasi fisik) ──────
        elif path == "/api/apply":
            logger.info("[API] Operator memicu eksekusi apply persetujuan massal...")
            try:
                # Panggil skrip apply_approved_changes secara aman di memori
                res = apply_approved_changes(
                    final_output_dir=_FINAL_OUTPUT_DIR,
                    logs_dir=_LOGS_DIR
                )
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "status": "success", 
                    "message": "Siklus modifikasi fisik selesai.",
                    "total_processed": res.get("total_processed", 0),
                    "success_count": res.get("success_count", 0),
                    "failed_count": res.get("failed_count", 0)
                }).encode('utf-8'))
            except Exception as e:
                logger.error(f"[API] Gagal eksekusi apply: {e}")
                self._set_headers(500)
                self.wfile.write(json.dumps({"status": "failed", "message": f"Gagal mengeksekusi apply: {e}"}).encode('utf-8'))
            return

        # ── Endpoint API: POST /api/rollback (Eksekusi rollback file) ──────
        elif path == "/api/rollback":
            op_id = req_body.get("operation_id")
            if not op_id:
                self._set_headers(400)
                self.wfile.write(json.dumps({"status": "failed", "message": "operation_id wajib diisi."}).encode('utf-8'))
                return

            logger.info(f"[API] Operator memicu rollback untuk operasi: {op_id}")
            try:
                success, msg = execute_rollback_for_file(_LOGS_DIR, op_id)
                if success:
                    self._set_headers(200)
                    self.wfile.write(json.dumps({"status": "success", "message": msg}).encode('utf-8'))
                else:
                    self._set_headers(400)
                    self.wfile.write(json.dumps({"status": "failed", "message": msg}).encode('utf-8'))
            except Exception as e:
                logger.error(f"[API] Gagal eksekusi rollback: {e}")
                self._set_headers(500)
                self.wfile.write(json.dumps({"status": "failed", "message": f"Gagal mengeksekusi rollback: {e}"}).encode('utf-8'))
            return

        self.send_error(404, "Rute POST tidak ditemukan.")


def start_api_server():
    """Menjalankan backend API lokal stasiun radio."""
    setup_logger()
    server_address = ("", _PORT)
    httpd = HTTPServer(server_address, WebReviewAPIHandler)
    logger.info("======================================================================")
    logger.info(f"   BACKEND SERVER WEB REVIEW CLASSIFIER AKTIF DI PORT: {_PORT}")
    logger.info(f"   -> Buka peramban di: http://localhost:{_PORT}/ untuk visual UI!")
    logger.info("======================================================================")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("\n[SHUTDOWN] Menghentikan Backend API server secara aman...")
        httpd.server_close()
        logger.info("[SHUTDOWN] Server dihentikan. Sampai jumpa!")


if __name__ == "__main__":
    start_api_server()
