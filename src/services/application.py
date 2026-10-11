from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.application import Application
from src.models.user import User
from src.repositories.application import ApplicationRepository
from src.repositories.user import UserRepository
from src.schemas.application import (
    CreateApplicationRequest,
    UpdateApplicationRequest,
)
from src.services.customer import CustomerService


class ApplicationService:
    @staticmethod
    async def _get_submitter_ids(
        data: CreateApplicationRequest,
        db: AsyncSession,
    ) -> set[UUID]:
        requested_ids = [submitter.id for submitter in data.submitters]
        if not requested_ids:
            return set()

        users = await UserRepository.list(db, filters=[User.id.in_(requested_ids)])
        return {user.id for user in users}

    @staticmethod
    async def add(
        data: CreateApplicationRequest,
        db: AsyncSession,
    ) -> Application:
        await CustomerService.get(data.customer_id, db)
        submitter_ids = await ApplicationService._get_submitter_ids(data, db)

        application_data = data.model_dump(exclude={"submitters"})
        application = await ApplicationRepository.add(application_data, db)
        if submitter_ids:
            await ApplicationRepository.add_submitters(application, submitter_ids, db)

        await db.commit()
        return await ApplicationRepository.get_by_id(application.id, db)

    @staticmethod
    async def list(
        db: AsyncSession,
        customer_id: UUID | None = None,
    ) -> list[Application]:
        filters = []
        if customer_id is not None:
            filters.append(Application.customer_id == customer_id)
        return await ApplicationRepository.list(db, filters=filters)

    @staticmethod
    async def get(id: UUID, db: AsyncSession) -> Application:
        application = await ApplicationRepository.get_by_id(id, db)
        if application is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found",
            )

        return application

    @staticmethod
    async def update(
        id: UUID,
        data: UpdateApplicationRequest,
        db: AsyncSession,
    ) -> Application:
        application = await ApplicationService.get(id, db)
        await CustomerService.get(data.customer_id, db)
        submitter_ids = await ApplicationService._get_submitter_ids(data, db)

        current_ids = {user.id for user in application.submitters}
        to_delete = current_ids - submitter_ids
        to_add = submitter_ids - current_ids

        if to_add:
            await ApplicationRepository.add_submitters(application, to_add, db)
        if to_delete:
            await ApplicationRepository.delete_submitters(application, to_delete, db)

        application_data = data.model_dump(exclude={"submitters"})
        await ApplicationRepository.update(application.id, application_data, db)
        await db.commit()

        db.expire(application)
        return await ApplicationRepository.get_by_id(id, db)

    @staticmethod
    async def delete(id: UUID, db: AsyncSession) -> None:
        await ApplicationService.get(id, db)
        await ApplicationRepository.delete(id, db)
        await db.commit()
