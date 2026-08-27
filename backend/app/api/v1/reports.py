"""Report routes — CSV and PDF export of pet history."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.services import report_service
from app.services.pet_service import _get_pet_or_404, _check_ownership
from app.models.user import User

router = APIRouter()


@router.get("/pets/{pet_id}/report")
async def get_report(
    pet_id: str,
    format: str = Query("csv", pattern="^(csv|pdf)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export pet history as CSV or PDF."""
    pet = await _get_pet_or_404(pet_id, db)
    _check_ownership(pet, current_user)

    if format == "pdf":
        content = await report_service.generate_pdf_report(pet_id, db)
        return Response(
            content=content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={pet.name}_report.pdf"},
        )
    else:
        content = await report_service.generate_csv_report(pet_id, db)
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={pet.name}_report.csv"},
        )
