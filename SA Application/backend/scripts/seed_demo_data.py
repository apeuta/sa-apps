"""
Seed Demo Data — Script untuk mengisi database dengan dummy data.

Jalankan:
    docker compose exec backend python -m scripts.seed_demo_data

Script ini idempotent — bisa dijalankan berkali-kali tanpa duplikat.
Setiap insert dicek terlebih dahulu apakah data sudah ada.
"""

import asyncio
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.project import Project
from app.models.document import Document
from app.models.activity_log import ActivityLog


# ============================================================
# DATA DEMO
# ============================================================

DEMO_USERS = [
    {
        "email": "demo-sales@portal-sa.local",
        "name": "Demo Sales",
        "role": "Sales",
        "google_id": "demo-google-id-sales-001",
    },
    {
        "email": "demo-sa@portal-sa.local",
        "name": "Demo SA",
        "role": "SA",
        "google_id": "demo-google-id-sa-001",
    },
    {
        "email": "demo-lead@portal-sa.local",
        "name": "Demo Lead",
        "role": "Lead_SA",
        "google_id": "demo-google-id-lead-001",
    },
    {
        "email": "demo-admin@portal-sa.local",
        "name": "Demo Admin",
        "role": "Admin",
        "google_id": "demo-google-id-admin-001",
    },
]


async def get_or_create_user(db: AsyncSession, user_data: dict) -> User:
    """Cek user berdasarkan email, buat jika belum ada."""
    result = await db.execute(
        select(User).where(User.email == user_data["email"])
    )
    existing = result.scalar_one_or_none()

    if existing:
        print(f"  ✓ User sudah ada: {user_data['email']}")
        return existing

    user = User(
        id=uuid.uuid4(),
        email=user_data["email"],
        name=user_data["name"],
        role=user_data["role"],
        google_id=user_data["google_id"],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()
    print(f"  + User dibuat: {user_data['email']} ({user_data['role']})")
    return user


async def get_or_create_project(
    db: AsyncSession,
    project_data: dict,
    sales_id: uuid.UUID,
    sa_id: uuid.UUID | None = None,
) -> Project:
    """Cek proyek berdasarkan id_project, buat jika belum ada."""
    result = await db.execute(
        select(Project).where(Project.id_project == project_data["id_project"])
    )
    existing = result.scalar_one_or_none()

    if existing:
        print(f"  ✓ Proyek sudah ada: {project_data['project_name']}")
        return existing

    now = datetime.now(timezone.utc)
    project = Project(
        id_project=project_data["id_project"],
        project_name=project_data["project_name"],
        customer_name=project_data["customer_name"],
        sales_pic=sales_id,
        assigned_sa=sa_id,
        status=project_data["status"],
        target_submit=project_data["target_submit"],
        bant_score=project_data["bant_score"],
        bant_detail=project_data["bant_detail"],
        use_case_tags=project_data["use_case_tags"],
        dq_number=project_data.get("dq_number"),
        assigned_at=now if sa_id else None,
        created_at=now,
        updated_at=now,
    )
    db.add(project)
    await db.flush()
    print(f"  + Proyek dibuat: {project_data['project_name']} ({project_data['status']})")
    return project


async def get_or_create_document(
    db: AsyncSession,
    doc_data: dict,
    created_by: uuid.UUID,
) -> Document:
    """Cek dokumen berdasarkan id_doc, buat jika belum ada."""
    result = await db.execute(
        select(Document).where(Document.id_doc == doc_data["id_doc"])
    )
    existing = result.scalar_one_or_none()

    if existing:
        print(f"  ✓ Dokumen sudah ada: {doc_data['id_doc']}")
        return existing

    now = datetime.now(timezone.utc)
    doc = Document(
        id_doc=doc_data["id_doc"],
        id_project=doc_data["id_project"],
        doc_type=doc_data["doc_type"],
        status=doc_data["status"],
        gdrive_link=doc_data["gdrive_link"],
        folder_type=doc_data["folder_type"],
        notes=doc_data.get("notes"),
        created_by=created_by,
        created_at=now,
        updated_at=now,
    )
    db.add(doc)
    await db.flush()
    print(f"  + Dokumen dibuat: {doc_data['id_doc']} ({doc_data['doc_type']})")
    return doc


async def get_or_create_activity_log(
    db: AsyncSession,
    log_data: dict,
    sa_id: uuid.UUID,
) -> ActivityLog:
    """Cek activity log berdasarkan id_log, buat jika belum ada."""
    result = await db.execute(
        select(ActivityLog).where(ActivityLog.id_log == log_data["id_log"])
    )
    existing = result.scalar_one_or_none()

    if existing:
        print(f"  ✓ Activity log sudah ada: {log_data['id_log']}")
        return existing

    log = ActivityLog(
        id_log=log_data["id_log"],
        id_project=log_data["id_project"],
        sa_id=sa_id,
        subtask_category=log_data["subtask_category"],
        duration_hours=Decimal(str(log_data["duration_hours"])),
        raw_notes=log_data["raw_notes"],
        created_at=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.flush()
    print(f"  + Activity log dibuat: {log_data['subtask_category']} ({log_data['duration_hours']}h)")
    return log


async def seed_all():
    """Jalankan seluruh proses seeding."""
    print("=" * 60)
    print("🌱 SEED DEMO DATA — Portal SA MVP")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        try:
            # ── 1. Buat Users ──
            print("\n📁 [1/4] Membuat demo users...")
            users = {}
            for user_data in DEMO_USERS:
                user = await get_or_create_user(db, user_data)
                users[user_data["role"]] = user

            sales_id = users["Sales"].id
            sa_id = users["SA"].id

            # ── 2. Buat Projects ──
            print("\n📁 [2/4] Membuat demo projects...")

            projects_data = [
                {
                    "id_project": "PRJ-DEMO-001",
                    "project_name": "Migrasi Data Warehouse ke AWS",
                    "customer_name": "PT Nusantara Digital",
                    "status": "Assigned",
                    "target_submit": date(2025, 8, 15),
                    "bant_score": 75,
                    "bant_detail": {"budget": 25, "authority": 20, "need": 15, "timeline": 15},
                    "use_case_tags": ["data-warehouse", "redshift"],
                    "assign_sa": True,
                    "dq_number": None,
                },
                {
                    "id_project": "PRJ-DEMO-002",
                    "project_name": "Cloud Native App Modernization",
                    "customer_name": "PT Maju Bersama Tech",
                    "status": "Ready",
                    "target_submit": date(2025, 7, 30),
                    "bant_score": 85,
                    "bant_detail": {"budget": 25, "authority": 25, "need": 20, "timeline": 15},
                    "use_case_tags": ["kubernetes", "app-mod"],
                    "assign_sa": True,
                    "dq_number": "DQ-2025-00234",
                },
                {
                    "id_project": "PRJ-DEMO-003",
                    "project_name": "AI Platform Development",
                    "customer_name": "PT Cerdas Teknologi",
                    "status": "Pending Assignment",
                    "target_submit": date(2025, 9, 1),
                    "bant_score": 62,
                    "bant_detail": {"budget": 20, "authority": 17, "need": 15, "timeline": 10},
                    "use_case_tags": ["machine-learning", "sagemaker"],
                    "assign_sa": False,
                    "dq_number": None,
                },
                {
                    "id_project": "PRJ-DEMO-004",
                    "project_name": "Disaster Recovery Setup",
                    "customer_name": "PT Aman Sentosa",
                    "status": "Need Clarification",
                    "target_submit": date(2025, 10, 15),
                    "bant_score": 45,
                    "bant_detail": {"budget": 10, "authority": 15, "need": 10, "timeline": 10},
                    "use_case_tags": ["dr", "backup"],
                    "assign_sa": False,
                    "dq_number": None,
                },
                {
                    "id_project": "PRJ-DEMO-005",
                    "project_name": "IoT Data Pipeline",
                    "customer_name": "PT Koneksi Pintar",
                    "status": "Closed-Win",
                    "target_submit": date(2025, 6, 1),
                    "bant_score": 90,
                    "bant_detail": {"budget": 25, "authority": 25, "need": 20, "timeline": 20},
                    "use_case_tags": ["iot", "kinesis", "data-pipeline"],
                    "assign_sa": True,
                    "dq_number": "DQ-2025-00189",
                },
            ]

            for proj_data in projects_data:
                assign_sa = proj_data.pop("assign_sa")
                await get_or_create_project(
                    db,
                    proj_data,
                    sales_id=sales_id,
                    sa_id=sa_id if assign_sa else None,
                )

            # ── 3. Buat Documents (untuk proyek Assigned dan Ready) ──
            print("\n📁 [3/4] Membuat demo documents...")

            documents_data = [
                # Proyek 1 - Assigned
                {
                    "id_doc": "DOC-DEMO-001",
                    "id_project": "PRJ-DEMO-001",
                    "doc_type": "PropTek",
                    "status": "Draft",
                    "gdrive_link": "https://drive.google.com/file/d/demo-proptek-001",
                    "folder_type": "Solutions",
                    "notes": "Draft PropTek untuk migrasi data warehouse",
                },
                {
                    "id_doc": "DOC-DEMO-002",
                    "id_project": "PRJ-DEMO-001",
                    "doc_type": "BOQ",
                    "status": "Draft",
                    "gdrive_link": "https://drive.google.com/file/d/demo-boq-001",
                    "folder_type": "Solutions",
                    "notes": "Estimasi BOQ Redshift + S3 + Glue",
                },
                # Proyek 2 - Ready
                {
                    "id_doc": "DOC-DEMO-003",
                    "id_project": "PRJ-DEMO-002",
                    "doc_type": "PropTek",
                    "status": "Reviewed",
                    "gdrive_link": "https://drive.google.com/file/d/demo-proptek-002",
                    "folder_type": "Solutions",
                    "notes": "PropTek sudah di-review lead SA",
                },
                {
                    "id_doc": "DOC-DEMO-004",
                    "id_project": "PRJ-DEMO-002",
                    "doc_type": "BOQ",
                    "status": "Draft",
                    "gdrive_link": "https://drive.google.com/file/d/demo-boq-002",
                    "folder_type": "Solutions",
                    "notes": "BOQ EKS cluster + networking",
                },
            ]

            for doc_data in documents_data:
                await get_or_create_document(db, doc_data, created_by=sa_id)

            # ── 4. Buat Activity Logs (untuk proyek yang assigned ke SA) ──
            print("\n📁 [4/4] Membuat demo activity logs...")

            activity_logs_data = [
                {
                    "id_log": "LOG-DEMO-001",
                    "id_project": "PRJ-DEMO-001",
                    "subtask_category": "Meeting Pre-Sales",
                    "duration_hours": 2.0,
                    "raw_notes": "Meeting Pre-Sales dengan customer PT Nusantara Digital. Diskusi kebutuhan migrasi data warehouse dari on-premise ke AWS Redshift.",
                },
                {
                    "id_log": "LOG-DEMO-002",
                    "id_project": "PRJ-DEMO-001",
                    "subtask_category": "Create PropTek",
                    "duration_hours": 4.0,
                    "raw_notes": "Menyusun draft PropTek untuk arsitektur Redshift Serverless + S3 data lake. Termasuk diagram arsitektur dan sizing.",
                },
                {
                    "id_log": "LOG-DEMO-003",
                    "id_project": "PRJ-DEMO-002",
                    "subtask_category": "Peer Review",
                    "duration_hours": 1.5,
                    "raw_notes": "Peer Review dengan tim SA untuk PropTek Cloud Native App Modernization. Feedback: perlu tambah detail migration plan dari monolith ke microservices.",
                },
                {
                    "id_log": "LOG-DEMO-004",
                    "id_project": "PRJ-DEMO-001",
                    "subtask_category": "Internal Discussion",
                    "duration_hours": 2.0,
                    "raw_notes": "Internal Discussion arsitektur data pipeline. Diskusi alternatif antara Glue ETL vs custom Spark di EMR untuk ingestion layer.",
                },
                {
                    "id_log": "LOG-DEMO-005",
                    "id_project": "PRJ-DEMO-002",
                    "subtask_category": "Customer Workshop",
                    "duration_hours": 3.0,
                    "raw_notes": "Customer Workshop hands-on EKS deployment. Demo containerization workflow dan CI/CD pipeline menggunakan CodePipeline.",
                },
            ]

            for log_data in activity_logs_data:
                await get_or_create_activity_log(db, log_data, sa_id=sa_id)

            # Commit semua perubahan
            await db.commit()

            print("\n" + "=" * 60)
            print("✅ SEEDING SELESAI!")
            print("=" * 60)
            print(f"   Users     : {len(DEMO_USERS)}")
            print(f"   Projects  : {len(projects_data)}")
            print(f"   Documents : {len(documents_data)}")
            print(f"   Logs      : {len(activity_logs_data)}")
            print("=" * 60)

        except Exception as e:
            await db.rollback()
            print(f"\n❌ ERROR: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_all())
