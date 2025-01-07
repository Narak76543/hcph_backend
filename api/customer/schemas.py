from pydantic import BaseModel, EmailStr, validator

class CustomerBase(BaseModel):
    id          : str
    first_name  : str
    last_name   : EmailStr
    email       : str
    phone_number: str

class CustomerModel(CustomerBase):
    @validator("first_name")
    def validate_name(cls, v):
        if not v:
            raise ValueError("First name is required")
        elif len(v) < 3:
            raise ValueError("First name must be longer than 3 characters")
        return v
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "00000208",
                "first_name": "Sovanchannara",
                "last_name": "Nen",
                "email": "sovanchannara125@gmail.com",
                "phone_number": "088382321"
            }
        }
