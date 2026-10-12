from datetime import date
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from src.models.norm_document import LabType


################## Create Norm Document ####################
class CreateLabTest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    method: str = Field(..., min_length=1, max_length=255)
    lab_type: LabType


class CreateNormDocumentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    approved_date: date
    expiry_date: date | None = None
    lab_tests: list[CreateLabTest] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_lab_tests(self) -> Self:
        if self.expiry_date is not None and self.expiry_date < self.approved_date:
            raise ValueError("expiry_date must not be earlier than approved_date")

        names = [lab_test.name for lab_test in self.lab_tests]
        if len(names) != len(set(names)):
            raise ValueError("Lab test names must be unique")
        return self


class LabTestResponse(BaseModel):
    id: UUID
    name: str
    method: str
    lab_type: LabType


class CreateNormDocumentResponse(BaseModel):
    id: UUID
    name: str
    approved_date: date
    expiry_date: date | None
    lab_tests: list[LabTestResponse]
