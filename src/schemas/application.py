from datetime import date
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from src.schemas.customer import CustomerResponse
from src.schemas.user import GetUserListResponse


################### Create Application #####################
class Submitter(BaseModel):
    id: UUID


class CreateItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class ApplicationRequest(BaseModel):
    cid: int = Field(..., title="ID in the certification body")
    number: str = Field(..., min_length=1, max_length=20)
    customer_id: UUID
    qty: int = Field(..., ge=1, le=32767, title="Number of preparations")
    received_date: date
    submitters: list[Submitter] = Field(default_factory=list)


class CreateApplicationRequest(ApplicationRequest):
    items: list[CreateItem]

    @model_validator(mode="after")
    def check_items_match_qty(self) -> Self:
        if len(self.items) != self.qty:
            raise ValueError(
                f"Number of items ({len(self.items)}) must equal qty ({self.qty})"
            )
        return self


################### Get Application List ###################
class GetApplicationListResponse(BaseModel):
    id: UUID
    cid: int
    number: str
    qty: int
    received_date: date
    customer: CustomerResponse


################## Get Application Detail ##################
class ItemResponse(BaseModel):
    id: UUID
    name: str


class GetApplicationDetailResponse(GetApplicationListResponse):
    submitters: list[GetUserListResponse]
    items: list[ItemResponse]


class CreateApplicationResponse(GetApplicationDetailResponse):
    pass


################### Update Application #####################
class UpdateApplicationRequest(ApplicationRequest):
    pass


class UpdateApplicationResponse(GetApplicationDetailResponse):
    pass
