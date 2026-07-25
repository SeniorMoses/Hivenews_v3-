from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import authRouter, news
from fastapi.staticfiles import StaticFiles

 

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads") 
app.include_router(authRouter.router)
app.include_router(news.router)

@app.get("/")
def home():
    return {"message": "FastAPI server running"}