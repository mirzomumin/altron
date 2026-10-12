from fastapi import APIRouter

from src.db.session import SessionDep
from src.schemas.norm_document import (
    CreateNormDocumentRequest,
    CreateNormDocumentResponse,
)
from src.services.norm_document import NormDocumentService

router = APIRouter(
    prefix="/norm-documents",
    tags=["Norm Document"],
)


@router.post("")
async def create_norm_document(
    data: CreateNormDocumentRequest,
    db: SessionDep,
) -> CreateNormDocumentResponse:
    return await NormDocumentService.add(data, db)
