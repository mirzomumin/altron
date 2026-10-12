from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.norm_document import NormDocument
from src.repositories.lab_test import LabTestRepository
from src.repositories.norm_document import NormDocumentRepository
from src.schemas.norm_document import CreateNormDocumentRequest


class NormDocumentService:
    @staticmethod
    async def add(
        data: CreateNormDocumentRequest,
        db: AsyncSession,
    ) -> NormDocument:
        norm_document_data = data.model_dump(exclude={"lab_tests"})
        norm_document = await NormDocumentRepository.add(norm_document_data, db)
        if data.lab_tests:
            await LabTestRepository.bulk_add(
                [
                    {"norm_document_id": norm_document.id, **lab_test.model_dump()}
                    for lab_test in data.lab_tests
                ],
                db,
            )

        await db.commit()
        return await NormDocumentRepository.get_by_id(norm_document.id, db)

    @staticmethod
    async def get(id: UUID, db: AsyncSession) -> NormDocument:
        norm_document = await NormDocumentRepository.get_by_id(id, db)
        if norm_document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Norm document not found",
            )

        return norm_document
