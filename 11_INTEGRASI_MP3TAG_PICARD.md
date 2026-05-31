# 11 — Integrasi Mp3tag dan MusicBrainz Picard

## 1. Tujuan

Tool Python melakukan pekerjaan awal:

- scan,
- rename,
- sortir,
- metadata dasar,
- laporan.

Mp3tag dan MusicBrainz Picard dipakai untuk finishing manual gratis.

## 2. Mp3tag

### Fungsi

Mp3tag cocok untuk:

- edit metadata massal,
- mengisi Artist/Title dari nama file,
- isi Album default,
- isi Genre,
- cek file sebelum masuk RadioBoss,
- rename dari tag jika perlu.

### Cara Pakai

1. Buka Mp3tag.
2. Pilih folder output:

```text
data/output/RADIO_AUDIO_LIBRARY/
```

3. Pilih file.
4. Gunakan fitur Convert Filename - Tag.
5. Format untuk lagu:

```text
%artist% - %title%
```

6. Isi album massal:

```text
Radio SBL Library
```

7. Simpan.

### Catatan

Jangan gunakan format `Artist - Title` untuk jingle/iklan secara sembarangan.

Untuk non-lagu, edit manual.

## 3. MusicBrainz Picard

### Fungsi

Picard cocok untuk:

- lagu resmi,
- album,
- single yang datanya tersedia,
- file dengan metadata kosong tetapi audio jelas.

### Tidak Cocok Untuk

```text
jingle
iklan
ILM
rekaman talkshow
file WhatsApp
audio lokal yang tidak ada di database
bumper program
```

### Cara Aman Pakai Picard

1. Pilih file dari `90_PERLU_DICEK`.
2. Jalankan scan/lookup.
3. Cek hasil match.
4. Jangan save jika ragu.
5. Simpan hanya file yang match jelas.
6. Setelah selesai, masukkan kembali ke pipeline atau folder final.

## 4. Alur Hybrid

```text
Python Cleaner
→ Output awal
→ Mp3tag finishing massal
→ Picard untuk file sulit
→ Cek manual
→ RadioBoss
```

## 5. Prinsip

Jangan mengejar semua file harus otomatis.

Untuk radio, lebih aman:

```text
80% file rapi otomatis
20% file dicek manual
```

daripada 100% dipaksa otomatis tetapi banyak metadata salah.
