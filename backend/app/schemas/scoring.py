"""
Pydantic schemas untuk BANT Scoring.
Digunakan untuk validasi input/output API scoring endpoint.
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class BudgetDetail(BaseModel):
    """Detail budget dari input manual Sales."""
    mrr: Optional[float] = Field(default=None, description="Estimasi Monthly Recurring Revenue")


class AuthorityDetail(BaseModel):
    """Detail PIC (authority) dari input manual Sales."""
    name: str = Field(default="", description="Nama PIC customer")
    position: str = Field(default="", description="Jabatan PIC")
    email: str = Field(default="", description="Email PIC")


class BANTSubScores(BaseModel):
    """Detail sub-skor BANT per kriteria."""

    budget: int = Field(ge=0, le=25, description="Sub-skor Budget (0-25)")
    authority: int = Field(ge=0, le=25, description="Sub-skor Authority (0-25)")
    need: int = Field(ge=0, le=25, description="Sub-skor Need (0-25)")
    timeline: int = Field(ge=0, le=25, description="Sub-skor Timeline (0-25)")


class BANTResult(BaseModel):
    """Hasil scoring BANT — dikembalikan oleh ScoringEngine."""

    total_score: int = Field(ge=0, le=100, description="Total skor BANT (0-100)")
    sub_scores: BANTSubScores
    use_case_tags: list[str] = Field(default_factory=list, max_length=5)
    status: str = Field(description="Status proyek setelah scoring")
    feedback: Optional[str] = Field(
        default=None,
        description="Feedback untuk Sales jika skor < 60",
    )


class ManualBANTInput(BaseModel):
    """
    Input manual BANT dari Sales.
    Setiap kriteria bernilai integer 0-25.
    Termasuk metadata deskriptif (MRR, PIC, kebutuhan, timeline).
    """

    budget: int = Field(ge=0, le=25, description="Skor Budget (0-25)")
    authority: int = Field(ge=0, le=25, description="Skor Authority (0-25)")
    need: int = Field(ge=0, le=25, description="Skor Need (0-25)")
    timeline: int = Field(ge=0, le=25, description="Skor Timeline (0-25)")

    # Metadata deskriptif — disimpan ke bant_detail untuk ditampilkan di detail proyek
    budget_detail: Optional[BudgetDetail] = Field(default=None, description="Detail budget (MRR)")
    authority_detail: Optional[AuthorityDetail] = Field(default=None, description="Detail PIC customer")
    need_detail: Optional[str] = Field(default=None, description="Deskripsi kebutuhan teknis")
    timeline_detail: Optional[str] = Field(default=None, description="Target tanggal submit (YYYY-MM-DD)")

    @field_validator("budget", "authority", "need", "timeline")
    @classmethod
    def validate_integer_range(cls, v: int) -> int:
        """Pastikan setiap sub-skor adalah integer dalam rentang 0-25."""
        if not isinstance(v, int):
            raise ValueError("Sub-skor harus berupa integer")
        return v


class RecommendedDocumentInfo(BaseModel):
    """Info dokumen dari proyek Closed-Win yang direkomendasikan."""

    id_doc: str
    doc_type: str = Field(description="Tipe dokumen: PropTek, BOQ, Mandays, MoM, RFP, HLD")
    gdrive_link: str = Field(description="Link Google Drive dokumen")
    status: str = Field(description="Status dokumen: Draft, Reviewed, Final")


class SimilarProjectResult(BaseModel):
    """Hasil pencarian proyek serupa (RAG recommendation)."""

    id_project: str
    project_name: str
    customer_name: str
    use_case_tags: list[str] = Field(default_factory=list)
    matching_tags: int = Field(description="Jumlah tag yang cocok")
    status: str
    documents: list[RecommendedDocumentInfo] = Field(
        default_factory=list,
        description="Daftar dokumen dari proyek Closed-Win (PropTek, BOQ, HLD, dll.)",
    )
