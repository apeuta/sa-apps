# SA Apps

Repository dokumentasi dan aplikasi internal untuk tim Solutions Architect (SA).

---

## Struktur Repository

```
sa-apps/
├── .kiro/specs/sa-portal-mvp/   # Spec MVP Portal SA (requirements & design)
├── SA Application/              # User Story & Spesifikasi Portal SA
│   ├── Spesifikasi_Teknis_Portal_SA.md
│   └── Portal Activity Mapping & Report.pdf
└── README.md
```

---

## SA Application (Portal SA)

Folder ini berisi dokumentasi user story dan spesifikasi teknis untuk **Portal Solutions Architect** — aplikasi pengganti Redmine yang mengelola:

- **Pre-Sales Request & AI Scoring** — Input opportunity dari Sales, scoring otomatis via Gemini AI (BANT), dan assignment ke SA.
- **Dokumen Management & DQ Gating** — Tracking deliverables (PropTek, BOQ, Mandays, HLD) dengan mekanisme lock/unlock berbasis DQ Number dan SLA 5 hari.
- **Activity Mapping & Project Story** — Sinkronisasi Google Calendar, mapping aktivitas ke subtask, dan AI-powered notes polishing.
- **Post-Sales & PMO Handover** — Automated handover dokumen final ke tim PMO & Delivery setelah Closed-Win.

### Tech Stack (Planned)

| Layer | Teknologi |
|-------|-----------|
| Frontend | PWA (Progressive Web App) |
| Backend | Serverless (AWS Lambda / Cloud Functions) |
| Database | PostgreSQL (Aurora Serverless) |
| AI | Google Gemini AI (Vertex AI) |
| Integration | Google Workspace (Drive, Calendar, Gmail) |

### Dokumen yang Tersedia

| File | Deskripsi |
|------|-----------|
| `Spesifikasi_Teknis_Portal_SA.md` | Detail teknis lengkap: workflow, struktur database, dan integrasi layanan |
| `Portal Activity Mapping & Report.pdf` | Dokumen visual alur aktivitas dan laporan |

---

## Status

🚧 **Dalam pengembangan** — Saat ini masih tahap spesifikasi dan desain MVP.

---

## Kontributor

- Solutions Architect Team
