# Portal SA

Portal internal untuk tim Solution Architect (SA) di alur pre-sales sampai handover PMO. Glossary ini mendefinisikan istilah domain yang spesifik untuk portal ini — bukan konsep pemrograman umum. Ground truth perilaku produk ada di `SA Application/Spesifikasi_Teknis_Portal_SA.md`.

## Peran

**Sales**:
Orang yang membuat opportunity dan mengisi kualifikasi awal. Bukan bagian dari tim SA; mendapat akses baca ke folder/dokumen tertentu.
_Avoid_: Account Executive, AE

**SA** (Solution Architect):
Orang yang ditugaskan mengerjakan sisi teknis sebuah proyek pre-sales: dokumen, scoring, activity.
_Avoid_: Engineer, Presales Engineer

**Lead SA**:
SA yang mengambil keputusan assignment proyek ke SA dan mengelola subtask. Pengambil keputusan assignment; tidak ada step "qualify" manual terpisah di atas gate BANT otomatis.
_Avoid_: SA Manager

**Backup SA**:
SA yang diberi akses baca Project Story sebuah proyek untuk handover saat SA utama berhalangan (mis. cuti). Bukan peran atau entity tersendiri — dipetakan sebagai *collaborator* lewat fitur Project Collaboration.
_Avoid_: Pengganti SA, substitute SA

## Proyek & status

**Opportunity**:
Peluang pre-sales yang dibuat Sales. Begitu masuk sistem, direpresentasikan sebagai `Project`.
_Avoid_: Deal, lead

**Project**:
Entity inti yang melacak satu opportunity dari intake sampai handover. Punya `status`, BANT score, dokumen, dan activity log.
_Avoid_: Case, ticket

**Pending DQ**:
Status proyek saat menunggu DQ Number diisi; milik Flow 2 (Dokumen, DQ Number & Gating). Status spec yang wajib dipertahankan meski status operasional lain mengikuti kode.

## Kualifikasi

**BANT score**:
Skor kualifikasi 0–100 (Budget, Authority, Need, Timeline). Gate otomatis: `≥ 60` → proyek lanjut ke assignment; `< 60` → `Need Clarification`. Threshold ditetapkan spec, bukan asumsi.
_Avoid_: Lead score, qualification score

**DQ Number**:
Nomor identifikasi proyek yang menjadi gate Flow 2: fungsi tertentu terkunci sampai DQ Number terisi.
_Avoid_: Deal number, project code

## Pekerjaan & aktivitas

**Subtask**:
Work item yang bisa ditugaskan dalam sebuah proyek, punya status open → in_progress → done (mis. "Create HLD", "Peer Review"). Berbeda dari `ActivityCategory`.
_Avoid_: Task, to-do, activity

**ActivityCategory**:
Taksonomi untuk mengelompokkan entri activity log (mis. Internal Meeting, Customer Meeting, Document Review). Dimensi pengelompokan, bukan work item yang ditugaskan. Berbeda dari `Subtask`.
_Avoid_: Subtask (keduanya berbeda peran), activity type

**Project Story**:
Catatan naratif/kronologis aktivitas sebuah proyek, dapat diakses Backup SA untuk handover.
_Avoid_: Timeline, log narasi

## Dokumen

**Requirement** (dokumen):
Ringkasan terstruktur kebutuhan customer yang **di-generate AI** dari MoM/RFP + field Sales — konten turunan, bukan file upload customer. Disimpan sebagai `Document` dengan `doc_type="Requirement"`, menjadi baseline perbandingan BoQ.
_Avoid_: Spec customer, dokumen kebutuhan upload

**BoQ** (Bill of Quantity):
Dokumen daftar item/kuantitas yang dibandingkan terhadap dokumen Requirement untuk analisis gap coverage.
_Avoid_: Quote, penawaran
