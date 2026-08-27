"""
API endpoints untuk assignment SA ke proyek oleh Lead_SA.
Menangani penugasan SA, daftar proyek pending, dan ketersediaan SA.
"""

import logging
import random
import string
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.notification_log import NotificationLog
from app.models.project import Project
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.schemas.assignment import (
    AssignmentResponse,
    AssignRequest,
    ProjectBrief,
    SAAvailability,
)
from app.schemas.response import error_response, success_response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Assignment"])


def _generate_notification_id() -> str:
    """Generate ID notifikasi unik dengan format NOTIF-{timestamp}-{random}."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"NOTIF-{ts}-{random_part}"


def _require_lead_sa(current_user: User) -> None:
    """Validasi bahwa user saat ini memiliki role Lead_SA."""
    if current_user.role != "Lead_SA":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya Lead_SA yang dapat melakukan operasi ini.",
        )


async def _trigger_folder_provisioner(
    project_id: str,
    sa_email: str,
    lead_sa_email: str,
    sales_pic_id: str,
) -> None:
    """
    Background task: trigger Folder_Provisioner setelah assignment.
    Membuat folder proyek di Google Drive secara async.

    Args:
        project_id: ID proyek yang baru di-assign.
        sa_email: Email SA yang ditugaskan.
        lead_sa_email: Email Lead_SA yang melakukan assignment.
        sales_pic_id: ID Sales PIC proyek.
    """
    logger.info(
        f"[FolderProvisioner] Trigger provisioning untuk proyek {project_id} "
        f"(SA: {sa_email}, Lead: {lead_sa_email})"
    )
    # TODO: Implementasi lengkap di task 7.2 (Folder_Provisioner)
    # Saat ini hanya log — folder provisioner akan diimplementasikan terpisah
    try:
        # Placeholder: akan memanggil FolderProvisioner.provision_project_folder()
        pass
    except Exception as e:
        logger.error(f"[FolderProvisioner] Gagal provision folder proyek {project_id}: {e}")


@router.get(
    "/projects/pending-assignment",
    summary="Daftar proyek yang menunggu assignment",
    description=(
        "Menampilkan proyek-proyek berstatus 'Pending Assignment' "
        "yang siap ditugaskan ke SA. Hanya untuk Lead_SA."
    ),
)
async def get_pending_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Ambil daftar proyek yang berstatus 'Pending Assignment'.
    Hanya Lead_SA yang bisa mengakses endpoint ini.
    """
    _require_lead_sa(current_user)

    # Query proyek dengan status "Pending Assignment"
    result = await db.execute(
        select(Project)
        .where(Project.status == "Pending Assignment")
        .order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()

    # Format response
    projects_data = [
        ProjectBrief(
            id_project=p.id_project,
            project_name=p.project_name,
            customer_name=p.customer_name,
            status=p.status,
            bant_score=p.bant_score,
            use_case_tags=p.use_case_tags,
            assigned_sa=p.assigned_sa,
            assigned_at=p.assigned_at,
            target_submit=p.target_submit,
            gdrive_folder_id=p.gdrive_folder_id,
        ).model_dump(mode="json")
        for p in projects
    ]

    return success_response(
        data=projects_data,
        message=f"Ditemukan {len(projects_data)} proyek menunggu assignment.",
    )


@router.get(
    "/sa/available",
    summary="Daftar SA yang tersedia dengan workload",
    description=(
        "Menampilkan semua SA yang terdaftar di sistem beserta "
        "jumlah proyek aktif masing-masing. Hanya untuk Lead_SA."
    ),
)
async def get_available_sa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Ambil daftar SA beserta jumlah proyek aktif (status bukan terminal).
    Hanya Lead_SA yang bisa mengakses endpoint ini.
    """
    _require_lead_sa(current_user)

    # Status terminal — proyek yang sudah selesai/tidak aktif
    terminal_statuses = ("Closed-Win", "Handover Complete", "Lost")

    # Query semua user dengan role SA
    sa_result = await db.execute(
        select(User).where(User.role == "SA").order_by(User.name)
    )
    sa_users = sa_result.scalars().all()

    # Hitung jumlah proyek aktif per SA menggunakan subquery
    active_count_subquery = (
        select(
            Project.assigned_sa,
            func.count(Project.id_project).label("active_count"),
        )
        .where(Project.status.notin_(terminal_statuses))
        .where(Project.assigned_sa.isnot(None))
        .group_by(Project.assigned_sa)
    )
    active_count_result = await db.execute(active_count_subquery)
    active_counts = {row[0]: row[1] for row in active_count_result.all()}

    # Format response
    sa_data = [
        SAAvailability(
            id=sa.id,
            name=sa.name,
            email=sa.email,
            active_project_count=active_counts.get(sa.id, 0),
        ).model_dump(mode="json")
        for sa in sa_users
    ]

    return success_response(
        data=sa_data,
        message=f"Ditemukan {len(sa_data)} SA tersedia.",
    )


@router.get(
    "/sa/utilization",
    summary="Utilisasi SA per bulan",
    description=(
        "Menampilkan total jam kerja (dari activity logs) per SA per bulan. "
        "Mendukung filter per tahun dan per individu SA. Hanya untuk Lead_SA."
    ),
)
async def get_sa_utilization(
    year: int | None = None,
    sa_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Ambil data utilisasi SA per bulan berdasarkan activity logs.

    Mengembalikan:
    - Total jam per SA per bulan (berdasarkan created_at di ActivityLog)
    - Jika year tidak diisi, default tahun berjalan
    - Jika sa_id diisi, filter untuk SA tertentu saja

    Response format:
    {
      "year": 2026,
      "monthly_data": [
        {
          "sa_id": "...",
          "sa_name": "...",
          "months": {
            "1": 40.5, "2": 35.0, ... "12": 0
          },
          "total_hours": 320.5
        }
      ],
      "summary": {
        "months": {"1": 80.5, "2": 70.0, ...},
        "total_hours": 640.5,
        "sa_count": 3
      }
    }
    """
    _require_lead_sa(current_user)

    from datetime import date as date_type

    # Default tahun berjalan
    target_year = year or date_type.today().year

    # Query semua SA (atau filter per sa_id)
    sa_query = select(User).where(User.role == "SA").order_by(User.name)
    if sa_id:
        try:
            sa_uuid = uuid.UUID(sa_id)
            sa_query = sa_query.where(User.id == sa_uuid)
        except ValueError:
            pass  # Abaikan filter jika format uuid tidak valid

    sa_result = await db.execute(sa_query)
    sa_users = sa_result.scalars().all()

    # Query activity logs untuk tahun target, grouped by SA + bulan
    utilization_query = (
        select(
            ActivityLog.sa_id,
            func.extract("month", ActivityLog.created_at).label("month"),
            func.sum(ActivityLog.duration_hours).label("total_hours"),
        )
        .where(func.extract("year", ActivityLog.created_at) == target_year)
    )

    if sa_id:
        try:
            sa_uuid = uuid.UUID(sa_id)
            utilization_query = utilization_query.where(ActivityLog.sa_id == sa_uuid)
        except ValueError:
            pass

    utilization_query = utilization_query.group_by(
        ActivityLog.sa_id,
        func.extract("month", ActivityLog.created_at),
    )

    util_result = await db.execute(utilization_query)
    util_rows = util_result.all()

    # Build lookup: {sa_id: {month: total_hours}}
    sa_monthly: dict[uuid.UUID, dict[int, float]] = {}
    for row in util_rows:
        sid = row[0]
        month = int(row[1])
        hours = float(row[2])
        if sid not in sa_monthly:
            sa_monthly[sid] = {}
        sa_monthly[sid][month] = hours

    # Format response per SA
    monthly_data = []
    summary_months: dict[int, float] = {m: 0.0 for m in range(1, 13)}

    for sa in sa_users:
        months_data = sa_monthly.get(sa.id, {})
        sa_months = {str(m): months_data.get(m, 0.0) for m in range(1, 13)}
        sa_total = sum(months_data.values())

        monthly_data.append({
            "sa_id": str(sa.id),
            "sa_name": sa.name,
            "months": sa_months,
            "total_hours": round(sa_total, 2),
        })

        # Akumulasi summary
        for m in range(1, 13):
            summary_months[m] += months_data.get(m, 0.0)

    # Summary all SA
    summary = {
        "months": {str(m): round(v, 2) for m, v in summary_months.items()},
        "total_hours": round(sum(summary_months.values()), 2),
        "sa_count": len(sa_users),
    }

    return success_response(
        data={
            "year": target_year,
            "monthly_data": monthly_data,
            "summary": summary,
        },
        message=f"Data utilisasi SA untuk tahun {target_year}.",
    )


@router.get(
    "/projects/utilization",
    summary="Utilisasi per proyek",
    description=(
        "Menampilkan total jam kerja per proyek beserta personel SA. "
        "Berguna untuk melihat effort distribution antar proyek. Hanya untuk Lead_SA."
    ),
)
async def get_project_utilization(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Ambil data utilisasi per proyek:
    - Total jam kerja yang sudah di-log per proyek
    - Siapa saja SA yang mengerjakan (dari activity logs)
    - Status proyek saat ini

    Response:
    [
      {
        "id_project": "PRJ-001",
        "project_name": "...",
        "customer_name": "...",
        "status": "Assigned",
        "total_hours": 16.5,
        "sa_personnel": [{"sa_id": "...", "sa_name": "...", "hours": 10.0}, ...]
      }
    ]
    """
    _require_lead_sa(current_user)

    # Query: total jam per proyek
    from sqlalchemy import text as sa_text

    # Subquery: jam per SA per proyek
    sa_hours_query = (
        select(
            ActivityLog.id_project,
            ActivityLog.sa_id,
            func.sum(ActivityLog.duration_hours).label("hours"),
        )
        .group_by(ActivityLog.id_project, ActivityLog.sa_id)
    )
    sa_hours_result = await db.execute(sa_hours_query)
    sa_hours_rows = sa_hours_result.all()

    # Build lookup: {project_id: [{sa_id, hours}, ...]}
    project_sa_map: dict[str, list[dict]] = {}
    for row in sa_hours_rows:
        pid = row[0]
        if pid not in project_sa_map:
            project_sa_map[pid] = []
        project_sa_map[pid].append({"sa_id": row[1], "hours": float(row[2])})

    # Query semua proyek yang punya activity logs
    project_ids = list(project_sa_map.keys())
    if not project_ids:
        return success_response(data=[], message="Belum ada data activity log.")

    projects_result = await db.execute(
        select(Project).where(Project.id_project.in_(project_ids))
    )
    projects = {p.id_project: p for p in projects_result.scalars().all()}

    # Query semua SA users untuk nama
    all_sa_ids = set()
    for entries in project_sa_map.values():
        for entry in entries:
            all_sa_ids.add(entry["sa_id"])

    sa_users_result = await db.execute(
        select(User).where(User.id.in_(list(all_sa_ids)))
    )
    sa_name_map = {u.id: u.name for u in sa_users_result.scalars().all()}

    # Build response
    result_data = []
    for pid, sa_entries in project_sa_map.items():
        project = projects.get(pid)
        if not project:
            continue

        total_hours = sum(e["hours"] for e in sa_entries)
        personnel = [
            {
                "sa_id": str(e["sa_id"]),
                "sa_name": sa_name_map.get(e["sa_id"], "Unknown"),
                "hours": round(e["hours"], 2),
            }
            for e in sa_entries
        ]
        # Sort personnel by hours descending
        personnel.sort(key=lambda x: x["hours"], reverse=True)

        result_data.append({
            "id_project": pid,
            "project_name": project.project_name,
            "customer_name": project.customer_name,
            "status": project.status,
            "total_hours": round(total_hours, 2),
            "sa_personnel": personnel,
        })

    # Sort by total_hours descending
    result_data.sort(key=lambda x: x["total_hours"], reverse=True)

    return success_response(
        data=result_data,
        message=f"Data utilisasi untuk {len(result_data)} proyek.",
    )


@router.post(
    "/projects/{project_id}/assign",
    summary="Assign SA ke proyek",
    description=(
        "Menugaskan SA ke proyek yang berstatus 'Pending Assignment'. "
        "Update status menjadi 'Assigned', kirim notifikasi ke SA, "
        "dan trigger folder provisioning. Hanya untuk Lead_SA."
    ),
)
async def assign_sa_to_project(
    project_id: str,
    body: AssignRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Assign SA ke proyek tertentu.

    Flow:
    1. Validasi role Lead_SA
    2. Validasi proyek ada dan berstatus "Pending Assignment"
    3. Validasi SA ada dan role-nya "SA"
    4. Update proyek: status="Assigned", assigned_sa, assigned_at
    5. Insert notifikasi ke SA yang ditugaskan
    6. Trigger Folder_Provisioner async
    """
    _require_lead_sa(current_user)

    # === 1. Validasi proyek ada dan berstatus "Pending Assignment" ===
    project_result = await db.execute(
        select(Project).where(Project.id_project == project_id)
    )
    project = project_result.scalar_one_or_none()

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proyek dengan ID '{project_id}' tidak ditemukan.",
        )

    if project.status != "Pending Assignment":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Proyek tidak bisa di-assign karena statusnya '{project.status}'. "
                f"Hanya proyek berstatus 'Pending Assignment' yang bisa di-assign."
            ),
        )

    # === 2. Validasi SA ada dan role-nya SA ===
    sa_result = await db.execute(
        select(User).where(User.id == body.sa_id)
    )
    sa_user = sa_result.scalar_one_or_none()

    if sa_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SA dengan ID '{body.sa_id}' tidak ditemukan.",
        )

    if sa_user.role != "SA":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"User '{sa_user.name}' memiliki role '{sa_user.role}', "
                f"bukan 'SA'. Hanya user dengan role SA yang bisa ditugaskan."
            ),
        )

    # === 3. Update proyek ===
    now = datetime.now(timezone.utc)
    project.status = "Assigned"
    project.assigned_sa = body.sa_id
    project.assigned_at = now
    project.updated_at = now

    # === 4. Insert notifikasi ke SA ===
    notification = NotificationLog(
        id=_generate_notification_id(),
        event_type="assignment",
        recipient_user_id=body.sa_id,
        channel="in-app",
        status="sent",
        reference_id=project_id,
        metadata={
            "project_name": project.project_name,
            "customer_name": project.customer_name,
            "bant_score": project.bant_score,
            "use_case_tags": project.use_case_tags or [],
            "assigned_by": current_user.name,
        },
        created_at=now,
    )
    db.add(notification)

    # Commit perubahan
    await db.commit()
    await db.refresh(project)

    logger.info(
        f"Proyek {project_id} di-assign ke SA {sa_user.email} "
        f"oleh {current_user.email}"
    )

    # === 5. Trigger Folder_Provisioner async ===
    background_tasks.add_task(
        _trigger_folder_provisioner,
        project_id,
        sa_user.email,
        current_user.email,
        str(project.sales_pic),
    )

    # === 6. Build response ===
    response_data = AssignmentResponse(
        project=ProjectBrief(
            id_project=project.id_project,
            project_name=project.project_name,
            customer_name=project.customer_name,
            status=project.status,
            bant_score=project.bant_score,
            use_case_tags=project.use_case_tags,
            assigned_sa=project.assigned_sa,
            assigned_at=project.assigned_at,
            target_submit=project.target_submit,
            gdrive_folder_id=project.gdrive_folder_id,
        ),
        assigned_sa_name=sa_user.name,
        notification_sent=True,
        folder_provisioning_triggered=True,
    )

    return success_response(
        data=response_data.model_dump(mode="json"),
        message=f"Proyek '{project.project_name}' berhasil ditugaskan ke {sa_user.name}.",
    )
