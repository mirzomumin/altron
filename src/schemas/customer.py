from uuid import UUID

from pydantic import BaseModel, Field


class CustomerResponse(BaseModel):
    id: UUID
    name: str


#################### Create Customer #######################
class CreateCustomerRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class CreateCustomerResponse(CustomerResponse):
    pass


#################### Update Customer #######################
class UpdateCustomerRequest(CreateCustomerRequest):
    pass


class UpdateCustomerResponse(CustomerResponse):
    pass
