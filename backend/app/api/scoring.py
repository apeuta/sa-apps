"""
API endpoints untuk BANT Scoring.
Menyediakan endpoints untuk scoring manual dan mengambil hasil scoring proyek.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.project import Project
from app.schemas.response import success_response
from app.schemas.scoring import ManualBANTInput
from app.services.scoring_engine import scoring_engine

router = APIRouter(prefix="/projects", tags=["Scoring"])


@router.post(
    "/{project_id}/score-manual",
    summary="Manual BANT Scoring",
    description="Input skor BANT manual dari Sales (4 kriteria, skala 0-25 per kriteria).",
)
async def score_manual(
    project_id: str,
    body: ManualBANTInput,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint scoring BANT manual.

    Sales mengisi 4 kriteria BANT (Budget, Authority, Need, Timeline)
    dengan skala 0-25 per kriteria. Total skor = jumlah 4 kriteria (0-100).
    Threshold: >= 60 → Pending Assignment, < 60 → Need Clarification.
    """
    # Validasi proyek ada
    result = await db.execute(
        select(Project).where(Project.id_project == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Proyek dengan ID '{project_id}' tidak ditemukan.",
        )

    # Lakukan scoring manual
    bant_result = await scoring_engine.score_manual(
        project_id=project_id,
        budget=body.budget,
        authority=body.authority,
        need=body.need,
        timeline=body.timeline,
        db=db,
    )

    # Simpan metadata deskriptif ke bant_detail (jika ada)
    # Metadata ini ditampilkan di halaman detail proyek
    metadata = {}
    if body.budget_detail and body.budget_detail.mrr is not None:
        metadata["budget_mrr"] = body.budget_detail.mrr
    if body.authority_detail:
        if body.authority_detail.name:
            metadata["pic_name"] = body.authority_detail.name
        if body.authority_detail.position:
            metadata["pic_position"] = body.authority_detail.position
        if body.authority_detail.email:
            metadata["pic_email"] = body.authority_detail.email
    if body.need_detail:
        metadata["need_description"] = body.need_detail
    if body.timeline_detail:
        metadata["timeline_target"] = body.timeline_detail

    if metadata:
        # Merge dengan existing bant_detail (sub-skor numerik)
        existing_detail = project.bant_detail or {}
        existing_detail.update(metadata)
        project.bant_detail = existing_detail
        await db.commit()

    return success_response(
        data=bant_result.model_dump(),
        message=f"BANT scoring manual berhasil. Total skor: {bant_result.total_score}.",
    )


@router.get(
    "/{project_id}/bant-result",
    summary="Get BANT Scoring Result",
    description="Mengambil hasil scoring BANT proyek (skor, sub-skor, tags, status).",
)
async def get_bant_result(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint untuk mengambil hasil BANT scoring proyek.
    Mengembalikan total skor, sub-skor per kriteria, use case tags, dan status.
    """
    # Ambil proyek dari database
    result = await db.execute(
        select(Project).where(Project.id_project == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Proyek dengan ID '{project_id}' tidak ditemukan.",
        )

    # Cek apakah sudah punya skor BANT
    if project.bant_score is None and project.bant_detail is None:
        return success_response(
            data=None,
            message="Proyek ini belum memiliki hasil BANT scoring.",
        )

    # Compose BANTResult dari data proyek
    bant_detail = project.bant_detail or {}
    sub_scores = {
        "budget": bant_detail.get("budget", 0),
        "authority": bant_detail.get("authority", 0),
        "need": bant_detail.get("need", 0),
        "timeline": bant_detail.get("timeline", 0),
    }

    bant_data = {
        "total_score": project.bant_score or 0,
        "sub_scores": sub_scores,
        "use_case_tags": project.use_case_tags or [],
        "status": project.status,
        "feedback": None,
    }

    # Generate feedback jika skor < 60
    if project.bant_score is not None and project.bant_score < 60:
        weak = []
        for name, score in sub_scores.items():
            if score < 15:
                weak.append(f"- {name.capitalize()} (skor: {score}/25)")
        if weak:
            bant_data["feedback"] = "Kriteria berikut perlu dilengkapi:\n" + "\n".join(weak)

    return success_response(
        data=bant_data,
        message="Hasil BANT scoring berhasil diambil.",
    )


@router.get(
    "/{project_id}/recommendations",
    summary="Get Similar Project Recommendations",
    description="Mencari proyek Closed-Win yang mirip berdasarkan use_case_tags (RAG).",
)
async def get_recommendations(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint RAG recommendation.
    Mencari proyek Closed-Win yang memiliki kecocokan use_case_tags.
    Diurutkan descending berdasarkan jumlah tag cocok, max 5 hasil.
    Menyertakan info dokumen (tipe, link GDrive) dari proyek referensi.
    """
    # Ambil proyek saat ini
    result = await db.execute(
        select(Project).where(Project.id_project == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Proyek dengan ID '{project_id}' tidak ditemukan.",
        )

    use_case_tags = project.use_case_tags or []

    # Req 15.7: Proyek belum punya use_case_tags (belum melalui scoring)
    if not use_case_tags:
        return success_response(
            data=[],
            message="Rekomendasi akan tersedia setelah scoring selesai.",
        )

    # Cari proyek serupa
    recommendations = await scoring_engine.search_similar_projects(
        use_case_tags=use_case_tags,
        exclude_project_id=project_id,
        db=db,
    )

    # Req 15.6: Tidak ada proyek Closed-Win dengan tag cocok
    if not recommendations:
        return success_response(
            data=[],
            message="Belum ada referensi serupa.",
        )

    return success_response(
        data=[r.model_dump() for r in recommendations],
        message=f"Ditemukan {len(recommendations)} proyek serupa.",
    )
