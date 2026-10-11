from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from src.schemas.customer import CustomerResponse
from src.schemas.user import GetUserListResponse


################### Create Application #####################
class Submitter(BaseModel):
    id: UUID


class CreateApplicationRequest(BaseModel):
    cid: int = Field(..., title="ID in the certification body")
    number: str = Field(..., min_length=1, max_length=20)
    customer_id: UUID
    qty: int = Field(..., ge=1, le=32767, title="Number of preparations")
    received_date: date
    submitters: list[Submitter] = Field(default_factory=list)


################### Get Application List ###################
class GetApplicationListResponse(BaseModel):
    id: UUID
    cid: int
    number: str
    qty: int
    received_date: date
    customer: CustomerResponse


################## Get Application Detail ##################
class GetApplicationDetailResponse(GetApplicationListResponse):
    submitters: list[GetUserListResponse]


class CreateApplicationResponse(GetApplicationDetailResponse):
    pass


################### Update Application #####################
class UpdateApplicationRequest(CreateApplicationRequest):
    pass


class UpdateApplicationResponse(GetApplicationDetailResponse):
    pass
