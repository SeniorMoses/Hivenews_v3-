from pydantic import BaseModel, EmailStr, field_validator
from typing import List
from datetime import datetime

class Signup(BaseModel):
    username: str
    email: EmailStr
    password: str
    
    class Config:
        from_attributes= True
        
    @field_validator("username")
    @classmethod
    def validate_username(cls, val):
        if len(val) < 3:
            raise ValueError("username must be at least 3 characters")
        if not val.isalnum():
            raise ValueError("username can only contain letters and numbers.")
        return val

    @field_validator("password")
    @classmethod
    def validate_password(cls, pas):
        if len(pas) < 8:
            raise ValueError("password must be at least 8 characters")
        return pas

class News(BaseModel):
    date: datetime
    title: str
    content: str

class NewsResponse(BaseModel):
    id: int
    date: datetime
    title: str
    content: str
    image : str | None=None
    class Config:
        from_attributes = True

class PaginatedNewsResponse(BaseModel):
    total_items: int
    total_pages: int
    current_page: int
    limit: int
    data: List[NewsResponse]

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    message: str

class RefreshRequest(BaseModel):
    refresh_token: str
    
class UpdateNews(BaseModel):
    news_id : int
    new_title : str
    new_content: str
    
    

class LogoutRequest(BaseModel):
    refresh_token: str
    
class Comments(BaseModel):
    news_id : int
    comment : str
class ReadComments(BaseModel):
    id : int
    news_id : int
    user_id : int
    
    date : datetime
    comment : str
    class Config:
        from_attributes = True