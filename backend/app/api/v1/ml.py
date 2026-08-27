"""ML routes — image recognition endpoint."""

from fastapi import APIRouter, UploadFile, File, Depends

from app.schemas.ml import RecognitionResult
from app.services.ml_service import ml_service
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/ml/recognize", response_model=RecognitionResult)
async def recognize_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a pet image for AI recognition.
    Returns species, breed, confidence, and health symptom tags.
    """
    image_bytes = await file.read()
    result = await ml_service.recognize(image_bytes, filename=file.filename)
    return result

