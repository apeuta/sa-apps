# Requirements Document

## Introduction

Fitur **guardrails-llm** adalah lapisan keamanan terpusat yang membungkus semua pemanggilan LLM (Gemini) di backend Portal SA. Saat ini konten user — teks notes, dokumen upload, dan data aktivitas — dikirim mentah ke Gemini tanpa pemeriksaan input, dan response LLM tidak selalu divalidasi terhadap kontrak schema yang diharapkan. Fitur ini menutup gap tersebut (Fase 7 roadmap, fitur 11) dengan menyediakan satu module guardrail di `backend/app/utils/guardrails.py` yang dilewati oleh ketiga call site LLM di aplikasi SA:

1. **BANT scoring** — `backend/app/services/scoring_engine.py` memanggil `parse_document` untuk ekstraksi BANT dari dokumen PDF/DOCX.
2. **Note polishing** — `backend/app/services/activity_logger.py` memanggil `structure_text` untuk merapikan raw notes aktivitas.
3. **Project summary** — `backend/app/api/activity_logs.py` memanggil `complete_text` untuk menghasilkan ringkasan proyek.

Guardrail mencakup empat kemampuan: pembatasan ukuran input (truncate, bukan reject keras), deteksi PII berbasis regex Indonesia-centric (flag-and-log saja), mitigasi prompt-injection (neutralize + delimiter-wrap), dan validasi output terstruktur terhadap schema. Fitur ini **tidak menyentuh model atau schema database** (tidak ada migration Alembic), hanya menambah logika di layer utils, services, dan config.

## Glossary

- **Guardrail_Module**: Module terpusat di `backend/app/utils/guardrails.py` yang menyediakan fungsi guardrail input dan output yang dipakai semua call site LLM.
- **Input_Guardrail**: Komponen Guardrail_Module yang memproses input teks atau dokumen sebelum dikirim ke LLM (pembatasan ukuran, deteksi PII, mitigasi prompt-injection).
- **Output_Validator**: Komponen Guardrail_Module yang memvalidasi response terstruktur LLM terhadap schema JSON yang diharapkan.
- **PII_Detector**: Komponen Input_Guardrail yang mendeteksi Personally Identifiable Information memakai pola regex Indonesia-centric.
- **PII**: Personally Identifiable Information. Pada MVP mencakup email, nomor telepon Indonesia, NIK/KTP, NPWP, dan nomor kartu kredit.
- **Prompt_Injection_Mitigator**: Komponen Input_Guardrail yang menetralkan pola prompt-injection dan membungkus konten user dengan delimiter.
- **Call_Site**: Salah satu dari tiga titik pemanggilan LLM di aplikasi SA (BANT scoring, note polishing, project summary).
- **LLM_MAX_INPUT_CHARS**: Config batas jumlah karakter maksimum untuk input teks ke LLM. Default `20000`.
- **LLM_MAX_DOCUMENT_BYTES**: Config batas ukuran byte maksimum untuk dokumen yang dikirim ke LLM. Default `10485760` (10 MB).
- **GUARDRAIL_PII_DETECTION_ENABLED**: Config boolean yang mengaktifkan atau menonaktifkan PII_Detector. Default `True`.
- **Fallback_Non_LLM**: Mekanisme ringkasan sederhana non-LLM yang sudah ada di project summary (`activity_logs.py`), dipakai ketika LLM gagal atau output tidak valid.
- **Oversized_Input**: Input teks yang melebihi LLM_MAX_INPUT_CHARS, atau dokumen yang melebihi LLM_MAX_DOCUMENT_BYTES.
- **Delimiter_Wrap**: Teknik membungkus konten user dengan penanda batas eksplisit agar LLM memperlakukannya sebagai data, bukan instruksi.

## Requirements

### Requirement 1: Sentralisasi Guardrail Module

**User Story:** Sebagai developer backend, saya ingin semua logika guardrail terpusat di satu module, agar setiap call site LLM melewati guardrail yang sama tanpa duplikasi logika.

#### Acceptance Criteria

1. THE Guardrail_Module SHALL berada di file `backend/app/utils/guardrails.py`.
2. THE Guardrail_Module SHALL menyediakan fungsi Input_Guardrail untuk input teks yang dipanggil oleh note polishing dan project summary.
3. THE Guardrail_Module SHALL menyediakan fungsi Input_Guardrail untuk input dokumen yang dipanggil oleh BANT scoring.
4. THE Guardrail_Module SHALL menyediakan fungsi Output_Validator yang dipanggil oleh Call_Site yang menerima response terstruktur.
5. THE Guardrail_Module SHALL tidak mengubah model SQLAlchemy maupun schema database.

### Requirement 2: Pembatasan Ukuran Input Teks

**User Story:** Sebagai operator sistem, saya ingin input teks yang terlalu panjang dipotong (truncate) alih-alih ditolak, agar pemanggilan LLM tetap berjalan sambil mencegah payload berlebihan.

#### Acceptance Criteria

1. WHEN Input_Guardrail menerima input teks yang jumlah karakternya melebihi LLM_MAX_INPUT_CHARS, THE Input_Guardrail SHALL memotong teks hingga LLM_MAX_INPUT_CHARS karakter.
2. WHEN Input_Guardrail memotong input teks karena melebihi LLM_MAX_INPUT_CHARS, THE Input_Guardrail SHALL menulis log level warning yang mencantumkan panjang asli dan panjang setelah dipotong.
3. WHEN Input_Guardrail memotong input teks, THE Input_Guardrail SHALL mengembalikan teks hasil potong agar pemanggilan LLM tetap dilanjutkan.
4. WHILE jumlah karakter input teks berada pada atau di bawah LLM_MAX_INPUT_CHARS, THE Input_Guardrail SHALL meneruskan teks tanpa pemotongan.

### Requirement 3: Pembatasan Ukuran Input Dokumen

**User Story:** Sebagai operator sistem, saya ingin dokumen yang terlalu besar dibatasi sebelum dikirim ke LLM, agar pemanggilan multimodal tidak membawa payload byte yang berlebihan.

#### Acceptance Criteria

1. WHEN Input_Guardrail menerima dokumen yang ukuran byte-nya melebihi LLM_MAX_DOCUMENT_BYTES, THE Input_Guardrail SHALL memotong konten dokumen hingga LLM_MAX_DOCUMENT_BYTES byte.
2. WHEN Input_Guardrail memotong dokumen karena melebihi LLM_MAX_DOCUMENT_BYTES, THE Input_Guardrail SHALL menulis log level warning yang mencantumkan ukuran byte asli, ukuran byte setelah dipotong, dan nama file.
3. WHEN Input_Guardrail memotong dokumen, THE Input_Guardrail SHALL mengembalikan konten dokumen hasil potong agar pemanggilan LLM tetap dilanjutkan.
4. WHILE ukuran byte dokumen berada pada atau di bawah LLM_MAX_DOCUMENT_BYTES, THE Input_Guardrail SHALL meneruskan konten dokumen tanpa pemotongan.

### Requirement 4: Deteksi PII Indonesia-Centric (Flag-and-Log)

**User Story:** Sebagai pengelola kepatuhan data, saya ingin PII dalam input terdeteksi dan dicatat tanpa menghentikan pemanggilan, agar ada jejak audit tanpa mengganggu alur kerja MVP.

#### Acceptance Criteria

1. WHERE GUARDRAIL_PII_DETECTION_ENABLED bernilai `True`, THE PII_Detector SHALL memindai input teks untuk pola email, nomor telepon Indonesia, NIK/KTP, NPWP, dan nomor kartu kredit.
2. WHEN PII_Detector menemukan satu atau lebih kemunculan PII, THE PII_Detector SHALL menulis log level warning yang mencantumkan tipe PII dan jumlah kemunculan per tipe.
3. THE PII_Detector SHALL mencatat log PII tanpa menyertakan nilai mentah PII yang terdeteksi.
4. WHEN PII_Detector menemukan PII, THE Input_Guardrail SHALL meneruskan input ke LLM tanpa memblokir dan tanpa melakukan redaction terhadap nilai PII.
5. WHERE GUARDRAIL_PII_DETECTION_ENABLED bernilai `False`, THE PII_Detector SHALL melewati pemindaian PII dan meneruskan input tanpa perubahan.

### Requirement 5: Mitigasi Prompt-Injection

**User Story:** Sebagai pengelola keamanan, saya ingin konten user dinetralkan dan dibungkus delimiter sebelum masuk prompt LLM, agar instruksi berbahaya dari konten user tidak diperlakukan sebagai perintah oleh LLM.

#### Acceptance Criteria

1. WHEN Prompt_Injection_Mitigator memproses input teks, THE Prompt_Injection_Mitigator SHALL menetralkan pola prompt-injection yang terdeteksi di dalam teks.
2. WHEN Prompt_Injection_Mitigator memproses input teks, THE Prompt_Injection_Mitigator SHALL membungkus konten user dengan Delimiter_Wrap yang menandai batas awal dan akhir konten.
3. WHEN Prompt_Injection_Mitigator menetralkan satu atau lebih pola prompt-injection, THE Prompt_Injection_Mitigator SHALL menulis log level warning yang mencantumkan jumlah pola yang dinetralkan.
4. THE Prompt_Injection_Mitigator SHALL mengembalikan teks hasil neutralize dan Delimiter_Wrap agar pemanggilan LLM tetap dilanjutkan.

### Requirement 6: Validasi Output Terstruktur

**User Story:** Sebagai developer backend, saya ingin response terstruktur LLM divalidasi terhadap schema yang diharapkan, agar output malformed tidak diteruskan sebagai hasil yang valid.

#### Acceptance Criteria

1. WHEN Output_Validator menerima response terstruktur dari LLM, THE Output_Validator SHALL memvalidasi response terhadap schema JSON yang diharapkan oleh Call_Site.
2. IF response terstruktur gagal validasi terhadap schema yang diharapkan, THEN THE Output_Validator SHALL mengembalikan hasil validasi berstatus gagal kepada Call_Site.
3. WHEN Output_Validator mengembalikan hasil validasi berstatus gagal, THE Output_Validator SHALL menulis log level warning yang mencantumkan alasan kegagalan validasi.
4. WHEN response terstruktur lolos validasi schema, THE Output_Validator SHALL mengembalikan data terstruktur hasil validasi kepada Call_Site.

### Requirement 7: Fallback Project Summary saat Output Tidak Valid

**User Story:** Sebagai SA yang meminta ringkasan proyek, saya ingin ringkasan tetap muncul meski output LLM tidak valid, agar fitur ringkasan tidak gagal total.

#### Acceptance Criteria

1. IF validasi output pada project summary mengembalikan status gagal, THEN THE Project summary SHALL memicu Fallback_Non_LLM yang sudah ada di `backend/app/api/activity_logs.py`.
2. WHEN Project summary memicu Fallback_Non_LLM karena output tidak valid, THE Project summary SHALL mengembalikan ringkasan hasil Fallback_Non_LLM kepada pemanggil.
3. WHEN Project summary memicu Fallback_Non_LLM karena output tidak valid, THE Project summary SHALL menulis log level warning yang mencantumkan alasan fallback.

### Requirement 8: Integrasi Guardrail pada Tiga Call Site

**User Story:** Sebagai developer backend, saya ingin ketiga call site LLM memanggil Guardrail_Module sebelum dan sesudah pemanggilan LLM, agar tidak ada konten user yang sampai ke Gemini tanpa melewati guardrail.

#### Acceptance Criteria

1. WHEN BANT scoring memproses dokumen untuk `parse_document`, THE BANT scoring SHALL memanggil Input_Guardrail dokumen sebelum mengirim konten ke LLM.
2. WHEN note polishing memproses raw notes untuk `structure_text`, THE note polishing SHALL memanggil Input_Guardrail teks sebelum mengirim konten ke LLM.
3. WHEN project summary memproses data aktivitas untuk `complete_text`, THE project summary SHALL memanggil Input_Guardrail teks sebelum mengirim konten ke LLM.
4. WHEN note polishing dan BANT scoring menerima response terstruktur dari LLM, THE Call_Site SHALL memanggil Output_Validator terhadap response tersebut.
5. THE integrasi guardrail SHALL mempertahankan pola retry dan Fallback_Non_LLM yang sudah ada pada setiap Call_Site.

### Requirement 9: Konfigurasi Guardrail

**User Story:** Sebagai operator sistem, saya ingin batas dan toggle guardrail dapat dikonfigurasi lewat environment variable, agar perilaku guardrail dapat disesuaikan tanpa mengubah kode.

#### Acceptance Criteria

1. THE Config SHALL menyediakan setting LLM_MAX_INPUT_CHARS dengan nilai default `20000`.
2. THE Config SHALL menyediakan setting LLM_MAX_DOCUMENT_BYTES dengan nilai default `10485760`.
3. THE Config SHALL menyediakan setting GUARDRAIL_PII_DETECTION_ENABLED dengan nilai default `True`.
4. WHEN sebuah setting guardrail disediakan melalui environment variable, THE Config SHALL memakai nilai dari environment variable menggantikan nilai default.
