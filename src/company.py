from typing import Optional
from pydantic import BaseModel, HttpUrl, Field

class Company(BaseModel):
    url: HttpUrl = Field(description="The company's website url")
    name: Optional[str] = Field(default=None, description="The name of the company")
    description: Optional[str] = Field(default=None, description="The description of the company")
    source: Optional[str] = Field(default=None, description="The website where the data was extracted from")
    country: Optional[str] = Field(default=None, description="The country where the company is located")
    city: Optional[str] = Field(default=None, description="The city where the company is located")
    email: Optional[str] = Field(default=None, description="The email address of the company")