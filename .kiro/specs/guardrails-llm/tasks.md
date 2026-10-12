# Implementation Plan: guardrails-llm

## Overview

Rencana implementasi membangun lapisan guardrail LLM terpusat di `backend/app/utils/guardrails.py` sebagai pure-function module (tanpa DB/HTTP), lalu mengintegrasikannya ke tiga Call_Site LLM yang sudah ada (BANT scoring, note polishing, project summary). Pendekatan bersifat inkremental: skeleton + config dulu, lalu tiap kemampuan guardrail (size clamp teks, size clamp dokumen, PII detection, prompt-injection mitigation, output validation) dibangun dengan property test di dekatnya, baru kemudian di-wire ke setiap Call_Site sambil mempertahankan jalur retry/fallback existing. Tidak ada perubahan model SQLAlchemy maupun migration Alembic.

Property test memakai Hypothesis (minimum 100 iterasi per property) dengan tag `# Feature: guardrails-llm, Property N`. Provider di-mock mengikuti pola `backend/tests/test_gemini_adapter.py`. Bahasa implementasi: Python (backend FastAPI).

## Tasks

- [ ] 1. Skeleton Guardrail_Module, data model, dan konfigurasi
  - [ ] 1.1 Buat skeleton `backend/app/utils/guardrails.py` + data model return terpadu
    - Buat file `backend/app/utils/guardrails.py` tanpa import model SQLAlchemy / session DB / client HTTP (hanya `logging`, `re`, `dataclasses`, `enum`, `typing`, `pydantic`)
    - Definisikan `PiiType` (Enum: `EMAIL`, `PHONE_ID`, `NIK`, `NPWP`, `CREDIT_CARD`), `PiiFlag` (frozen dataclass: `type`, `count`), dan `GuardrailResult` (dataclass generic: `safe_value`, `truncated`, `pii_flags`, `injection_hits`, `original_size`, `final_size`)
    - Siapkan stub signature `sanitize_text_input`, `check_document_size`, `detect_pii`, `validate_llm_json` serta logger module-level `logging.getLogger(__name__)`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  - [ ] 1.2 Tambahkan tiga setting guardrail ke config + `.env.example`
    - Tambahkan `LLM_MAX_INPUT_CHARS: int = 20000`, `LLM_MAX_DOCUMENT_BYTES: int = 10_485_760`, `GUARDRAIL_PII_DETECTION_ENABLED: bool = True` pada `Settings` di `backend/app/core/config.py`
    - Dokumentasikan ketiga setting di `.env.example` (root) dengan nilai default
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  - [ ] 1.3 Smoke test keberadaan module, data model, dan default config
    - Test import `guardrails.py`, keberadaan fungsi publik, dan absennya import model SQLAlchemy di module (Req 1.5)
    - Test default `LLM_MAX_INPUT_CHARS`/`LLM_MAX_DOCUMENT_BYTES`/`GUARDRAIL_PII_DETECTION_ENABLED` (Req 9.1-9.3) dan override via env var dengan `monkeypatch` (Req 9.4)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 9.1, 9.2, 9.3, 9.4_

- [ ] 2. Pembatasan ukuran input (teks & dokumen)
  - [ ] 2.1 Implementasi size clamp teks di `sanitize_text_input` + byte clamp dokumen di `check_document_size`
    - `sanitize_text_input`: jika `len(text) > settings.LLM_MAX_INPUT_CHARS` potong ke batas, set `truncated=True`, isi `original_size`/`final_size`, dan `logger.warning` berisi panjang asli + panjang terpotong; jika ≤ batas teruskan apa adanya (tahap size clamp dulu, orkestrasi penuh dilengkapi di task 3 & 4)
    - `check_document_size`: jika `len(content) > settings.LLM_MAX_DOCUMENT_BYTES` potong byte ke batas, set `truncated=True`, dan `logger.warning` berisi ukuran asli + ukuran terpotong + `filename`; jika ≤ batas teruskan apa adanya; `safe_value` bertipe `bytes`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4_
  - [ ] 2.2 Property test size clamp teks
    - **Property 1: Size clamp teks** — panjang size-clamp `safe_value` = `min(len(text), LLM_MAX_INPUT_CHARS)` dan `truncated` True iff `len(text) > LLM_MAX_INPUT_CHARS`
    - Hypothesis min 100 iterasi, tag `# Feature: guardrails-llm, Property 1`
    - **Validates: Requirements 2.1, 2.3, 2.4**
  - [ ] 2.3 Property test byte clamp dokumen
    - **Property 2: Size clamp dokumen (byte)** — `len(safe_value)` = `min(len(content), LLM_MAX_DOCUMENT_BYTES)` dan `truncated` True iff `len(content) > LLM_MAX_DOCUMENT_BYTES`
    - Hypothesis min 100 iterasi, tag `# Feature: guardrails-llm, Property 2`
    - **Validates: Requirements 3.1, 3.3, 3.4**
  - [ ] 2.4 Unit/edge test log warning truncate
    - Verifikasi isi `logger.warning` via `caplog` untuk truncate teks (Req 2.2) dan truncate dokumen termasuk `filename` (Req 3.2)
    - _Requirements: 2.2, 3.2_

- [ ] 3. PII detector Indonesia-centric (flag-and-log)
  - [ ] 3.1 Implementasi `detect_pii` dan integrasikan ke `sanitize_text_input`
    - Implementasi regex Indonesia-centric untuk `EMAIL`, `PHONE_ID`, `NIK`, `NPWP`, `CREDIT_CARD`; kembalikan `list[PiiFlag]` berisi `type` + `count` tanpa menyimpan nilai mentah
    - `logger.warning` hanya mencantumkan tipe + count (tanpa nilai mentah); non-blocking dan non-redacting pada `safe_value`
    - Toggle: bila `settings.GUARDRAIL_PII_DETECTION_ENABLED == False`, kembalikan list kosong tanpa scan dan `sanitize_text_input` tidak memanggil scan
    - Isi `pii_flags` pada `GuardrailResult` dari `sanitize_text_input`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_
  - [ ] 3.2 Property test deteksi tipe & jumlah PII
    - **Property 3: Deteksi PII melaporkan tipe dan jumlah** — teks dengan `k` kemunculan tipe `T` menghasilkan `PiiFlag(T, count=k)` saat deteksi aktif
    - Hypothesis min 100 iterasi, tag `# Feature: guardrails-llm, Property 3`
    - **Validates: Requirements 4.1, 4.2**
  - [ ] 3.3 Property test PII non-mutating & non-blocking
    - **Property 4: PII tidak mengubah dan tidak mem-blokir input** — `safe_value` tidak me-redact nilai PII (perubahan hanya size clamp, neutralize, delimiter wrap)
    - Hypothesis min 100 iterasi, tag `# Feature: guardrails-llm, Property 4`
    - **Validates: Requirements 4.4**
  - [ ] 3.4 Property test log PII tidak memuat nilai mentah
    - **Property 5: Log PII tidak memuat nilai mentah** — tidak ada nilai PII mentah di `PiiFlag` maupun record log
    - Hypothesis min 100 iterasi (via `caplog`), tag `# Feature: guardrails-llm, Property 5`
    - **Validates: Requirements 4.3**
  - [ ] 3.5 Property test toggle menonaktifkan deteksi
    - **Property 6: Toggle menonaktifkan deteksi PII** — saat `GUARDRAIL_PII_DETECTION_ENABLED=False`, `pii_flags` kosong dan konten teks tidak diubah oleh tahap PII
    - Hypothesis min 100 iterasi dengan `monkeypatch` settings, tag `# Feature: guardrails-llm, Property 6`
    - **Validates: Requirements 4.5**

- [ ] 4. Checkpoint — pastikan test input guardrail lolos
  - Jalankan test guardrail yang sudah ada; pastikan semua hijau. Ask the user if questions arise.

- [ ] 5. Prompt-injection mitigation & output validation
  - [ ] 5.1 Implementasi neutralize + delimiter wrap dalam `sanitize_text_input`
    - Helper `_neutralize_injection(text) -> tuple[str, int]`: netralkan pola seperti `ignore (all )?previous instructions`, `disregard the (above|system)`, `you are now`, `system:`/`assistant:` di awal baris; kembalikan teks + jumlah hit
    - Helper `_wrap_with_delimiter(text) -> str`: bungkus dengan konstanta modul `<<<USER_CONTENT_START>>>` / `<<<USER_CONTENT_END>>>`
    - Lengkapi orkestrasi `sanitize_text_input`: size clamp → PII detection → neutralize → delimiter wrap; isi `injection_hits`; `logger.warning` jumlah hit; fungsi tidak melempar exception
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  - [ ] 5.2 Implementasi `strip_code_fence`, Pydantic contracts, `validate_llm_json`, dan `is_nonempty_summary`
    - Helper shared `strip_code_fence(text)` untuk membersihkan ```` ```json ```` (dipakai ulang oleh `scoring_engine`)
    - Pydantic contracts: `BANTCriterion` (`score` clamp 0-25 via `field_validator` mode before, `evidence`), `BANTExtractionResult` (budget/authority/need/timeline + `use_case_tags` max 5), `ActionItem`, `PolishResult` (discussion_points + action_items)
    - `OutputValidationResult` dataclass (`valid`, `data`, `error`) + `validate_llm_json(content, contract)`: strip code-fence bila string → `json.loads` → validasi contract; sukses `valid=True`+data, gagal `valid=False`+`error` dan `logger.warning` alasan
    - `is_nonempty_summary(text) -> bool`: string non-kosong, non-whitespace, panjang wajar
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  - [ ] 5.3 Property test netralisasi prompt-injection
    - **Property 7: Netralisasi pola prompt-injection** — `safe_value` tidak lagi mengandung pola injeksi utuh dan `injection_hits` = jumlah pola yang disisipkan
    - Hypothesis min 100 iterasi, tag `# Feature: guardrails-llm, Property 7`
    - **Validates: Requirements 5.1, 5.3, 5.4**
  - [ ] 5.4 Property test delimiter wrap
    - **Property 8: Delimiter wrap membungkus konten user** — `safe_value` diawali penanda awal dan diakhiri penanda akhir (konstanta modul)
    - Hypothesis min 100 iterasi, tag `# Feature: guardrails-llm, Property 8`
    - **Validates: Requirements 5.2**
  - [ ] 5.5 Property test validasi output valid/invalid
    - **Property 9: Validasi output menerima yang valid dan menolak yang invalid** — objek sesuai kontrak → `valid=True`+data; objek melanggar kontrak → `valid=False`+`error`
    - Hypothesis min 100 iterasi, tag `# Feature: guardrails-llm, Property 9`
    - **Validates: Requirements 6.1, 6.2, 6.4**
  - [ ] 5.6 Property test clamp skor BANT 0-25
    - **Property 10: Clamp skor BANT ke rentang 0–25** — skor sub-kriteria (termasuk di luar rentang/non-numerik) selalu dalam 0–25 setelah validasi `BANTExtractionResult`
    - Hypothesis min 100 iterasi, tag `# Feature: guardrails-llm, Property 10`
    - **Validates: Requirements 6.1**
  - [ ] 5.7 Unit/edge test log warning injection & validasi gagal
    - Verifikasi `logger.warning` via `caplog` untuk jumlah injeksi (Req 5.3) dan alasan kegagalan validasi output (Req 6.3)
    - _Requirements: 5.3, 6.3_

- [ ] 6. Wire guardrail ke BANT scoring (`scoring_engine.py`)
  - [ ] 6.1 Integrasikan `check_document_size` dan `validate_llm_json` ke `_extract_bant_with_retry`
    - Sebelum `provider.parse_document(...)`, panggil `check_document_size(content, mime_type, filename)` dan kirim `result.safe_value`
    - Ganti `self._parse_llm_response(response.content)` dengan `validate_llm_json(response.content, BANTExtractionResult)`; refactor `_parse_llm_response` agar memakai `strip_code_fence` shared
    - Pertahankan jalur retry dan penanda **"Manual Review Required"** saat semua file gagal validasi
    - _Requirements: 8.1, 8.4, 8.5, 6.1_
  - [ ] 6.2 Integration test wiring BANT scoring (provider mock)
    - Mock provider pola `test_gemini_adapter.py`; verifikasi `check_document_size` dipanggil sebelum `parse_document` (Req 8.1), `validate_llm_json` dipakai pada response (Req 8.4), dan output invalid → "Manual Review Required" (Req 8.5)
    - _Requirements: 8.1, 8.4, 8.5_

- [ ] 7. Wire guardrail ke note polishing (`activity_logger.py`)
  - [ ] 7.1 Integrasikan `sanitize_text_input` dan `validate_llm_json` ke `polish_notes`
    - Sebelum `provider.structure_text(...)`, panggil `sanitize_text_input(raw_notes)` dan kirim `result.safe_value` sebagai `text`
    - Ganti pengecekan manual `"discussion_points" in content` dengan `validate_llm_json(response.content, PolishResult)`
    - Jika tidak valid kembalikan `None` (entry ditandai `needs_repolish` → dapat `retry_polish`), mempertahankan pola existing
    - _Requirements: 8.2, 8.4, 8.5_
  - [ ] 7.2 Integration test wiring note polishing (provider mock)
    - Verifikasi `sanitize_text_input` dipanggil sebelum `structure_text` (Req 8.2), `validate_llm_json` dipakai (Req 8.4), dan output invalid → `None`/`needs_repolish` (Req 8.5)
    - _Requirements: 8.2, 8.4, 8.5_

- [ ] 8. Wire guardrail ke project summary (`api/activity_logs.py`) + sentralisasi final
  - [ ] 8.1 Integrasikan `sanitize_text_input` dan `is_nonempty_summary` ke `summarize_project`
    - Setelah membangun `activity_data`, panggil `sanitize_text_input(activity_data)` sebelum `provider.complete_text(prompt, ...)` (teks via `safe_value`)
    - Setelah response, validasi ringan `is_nonempty_summary(summary_text)`; jika LLM gagal **atau** output tidak valid → jalankan **Fallback_Non_LLM** existing dan `logger.warning` alasan fallback
    - _Requirements: 8.3, 7.1, 7.2, 7.3_
  - [ ] 8.2 Export public API guardrail + verifikasi tidak ada Call_Site LLM yang bypass guardrail
    - Export fungsi/konstanta publik guardrail di `backend/app/utils/__init__.py` dengan docstring
    - Audit ketiga Call_Site: pastikan tidak ada pemanggilan `parse_document`/`structure_text`/`complete_text` di aplikasi SA yang melewati guardrail
    - _Requirements: 1.2, 1.3, 1.4, 8.1, 8.2, 8.3_
  - [ ] 8.3 Integration test wiring project summary & Fallback_Non_LLM (provider mock)
    - Verifikasi `sanitize_text_input` dipanggil sebelum `complete_text` (Req 8.3), dan output invalid/LLM gagal → Fallback_Non_LLM dengan log alasan (Req 7.1, 7.2, 7.3)
    - _Requirements: 8.3, 7.1, 7.2, 7.3_

- [ ] 9. Checkpoint akhir — verification gate backend & update roadmap
  - [ ] 9.1 Jalankan verification gate backend
    - Jalankan `pytest` di `backend/tests/` sampai hijau; pastikan app bisa di-import/start bersih (tanpa error)
    - Perbaiki regresi bila ada sebelum menandai selesai
    - _Requirements: 8.5_
  - [ ] 9.2 Update checkbox Fase 7 & status fitur 11 di `docs/ROADMAP.md`
    - Centang item Fase 7 (7.1–7.4) dan update status fitur 11 pada tabel ringkasan `docs/ROADMAP.md` di branch yang sama
    - _Requirements: 1.1_

## Notes

- Task bertanda `*` adalah test opsional dan dapat dilewati untuk MVP cepat; task inti (tanpa `*`) wajib diimplementasikan.
- Property test memakai Hypothesis minimum 100 iterasi, tiap test diberi tag `# Feature: guardrails-llm, Property N`, dan provider di-mock mengikuti pola `backend/tests/test_gemini_adapter.py`.
- Tidak ada perubahan model SQLAlchemy maupun migration Alembic (Req 1.5).
- Integrasi tiga Call_Site mempertahankan pola retry dan Fallback existing (Req 8.5): BANT → "Manual Review Required", Polish → `None`/`retry_polish`, Summary → Fallback_Non_LLM.
- Checkpoint memastikan validasi inkremental; verification gate backend wajib hijau sebelum PR (sesuai `CONTRIBUTING.md`).

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3"] },
    { "id": 2, "tasks": ["2.1"] },
    { "id": 3, "tasks": ["2.2", "2.3", "2.4"] },
    { "id": 4, "tasks": ["3.1"] },
    { "id": 5, "tasks": ["3.2", "3.3", "3.4", "3.5", "5.1", "5.2"] },
    { "id": 6, "tasks": ["5.3", "5.4", "5.5", "5.6", "5.7"] },
    { "id": 7, "tasks": ["6.1", "7.1", "8.1"] },
    { "id": 8, "tasks": ["6.2", "7.2", "8.2"] },
    { "id": 9, "tasks": ["8.3", "9.1"] },
    { "id": 10, "tasks": ["9.2"] }
  ]
}
```
