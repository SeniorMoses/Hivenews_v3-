from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import math
from datetime import datetime 

from database import get_db
from models import NewsModel, Comment
from schemas import PaginatedNewsResponse, NewsResponse, Comments, ReadComments, UpdateNews
from auth import get_current_user
import os
from typing import Annotated

import uuid
import json
from cache import redis_client 

router = APIRouter(prefix="", tags=["News"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/post")
async def post_news(
    date: Annotated[datetime, Form()],
    title: Annotated[str, Form()],
    content: Annotated[str, Form()],
    image: UploadFile | None = File(None),
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user["role"] != "admin": 
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to use this feature"
        )

    image_name = None
    
    if image:
    

        ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}

        ext = os.path.splitext(image.filename)[1].lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
            status_code=400,
            detail="Unsupported file type."
        )
        
        image_name = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(UPLOAD_DIR, image_name)

        MAX_SIZE = 5 * 1024 * 1024  

        contents = await image.read()

        if len(contents) > MAX_SIZE:
            raise HTTPException(
                status_code=400,
                detail="Image is too large."
            )

        with open(file_path, "wb") as buffer:
            buffer.write(contents)

    post = NewsModel(
        date=date,
        title=title,
        content=content,
        image=image_name
    )

    db.add(post)
    db.commit()
    db.refresh(post)
    for key in redis_client.scan_iter("news:*"):
        redis_client.delete(key)
    return {
        "message": "News posted successfully 🎉",
        "news": post
        } 



@router.get("/read", response_model=PaginatedNewsResponse)
async def read_news(
    page: int = 1,
    limit: int = 10,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cache_key = f"news:{page}:{limit}"

    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached) 
   
    posts = db.query(NewsModel).offset((page - 1) * limit).limit(limit).all()

    response = PaginatedNewsResponse(
        total_items=db.query(NewsModel).count(),
        total_pages=math.ceil(db.query(NewsModel).count() / limit),
        current_page=page,
        limit=limit,
        data=posts,
    )

    redis_client.setex(
        cache_key,
        300,  
        response.model_dump_json()
    )

    return response

@router.get("/posts/{post_title}", response_model=list[NewsResponse])
async def search_news(
    post_title: str,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    found = db.query(NewsModel).filter(
        NewsModel.title.ilike(f"%{post_title}%")
    ).all()

    if not found:
        raise HTTPException(
        status_code=404, 
        detail="News not found"
        )
    return found
    
@router.post("/comments/")
async def comment(data:Comments,
 db: Session = Depends(get_db),
 user = Depends(get_current_user)
 ):
     news = db.query(NewsModel).filter(NewsModel.id ==data.news_id).first() 
     if not news:
         raise HTTPException(
         status_code = 404,
         detail = "news not found"
         )
     new_comment = Comment(
     news_id = data.news_id,
     user_id = user["id"],
    
     comment = data.comment
     )
     db.add(new_comment)
     db.commit()
     db.refresh(new_comment)  
     return {"message" : "comments added"}
@router.get("/read_comment/{news_id}", response_model = list[ReadComments]) 
async def read_comment(
news_id:int,
user = Depends(get_current_user),
db: Session = Depends(get_db) 
):
    comments = db.query(Comment).filter(Comment.news_id == news_id).all() 
    return comments
    
@router.delete("/delete_news/{news_id}")
async def delete_news(
news_id:int,
db:Session = Depends(get_db),
user=Depends(get_current_user)
):
    if user["role"] != "admin":
        raise HTTPException(
        status_code = 403,
        detail = "user forbidden"
        )
    news = db.query(NewsModel).filter(NewsModel.id==news_id).first()
    if not news:
        raise HTTPException(
        status_code=404,
        detail = "news not found"
        )
    if news.image:
        
        image_path = os.path.join(UPLOAD_DIR, news.image)
        if os.path.exists(image_path):
            os.remove(image_path)


    db.delete(news)
    db.commit() 
    for key in redis_client.scan_iter("news:*"):
        redis_client.delete(key)
    return{"message":"news deleted"} 
    
@router.put("/update_news/")
async def update_news(
data:UpdateNews,
db:Session = Depends(get_db),
user = Depends(get_current_user)
):
    if user["role"] != "admin":
        raise HTTPException(
        status_code = 403,
        detail = "user forbidden"
        )
    news = db.query(NewsModel).filter(NewsModel.id==data.news_id).first()
    if not news:
            raise HTTPException(
            status_code=404,
            detail="news not found"
            )
    news.title=data.new_title
    news.content=data.new_content
    db.commit() 
    db.refresh(news)
    for key in redis_client.scan_iter("news:*"):
        redis_client.delete(key) 
    return {"message":"news updated"}