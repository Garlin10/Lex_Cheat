import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import io
import zipfile
from fastapi import Query
from fastapi.staticfiles import StaticFiles
# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Image and Text Storage API", description="API for storing images and text data")
app.mount("/lex", StaticFiles(directory="static", html=True), name="static")
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_URL = "sqlite:///./data_storage.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the database models
class ImageResponse(Base):
    __tablename__ = "image_responses"

    id = Column(Integer, primary_key=True, index=True)
    image_base64 = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class TextResponse(Base):
    __tablename__ = "text_responses"

    id = Column(Integer, primary_key=True, index=True)
    text_data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create the database tables
Base.metadata.create_all(bind=engine)

# Define the request models
class ImageRequest(BaseModel):
    base64_image: str

class TextRequest(BaseModel):
    text: str

# Security setup
security = HTTPBasic()
USERNAME = os.getenv("API_USERNAME", "admin")  # Set a default username if not in .env
PASSWORD = os.getenv("API_PASSWORD", "password")  # Set a default password if not in .env

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != USERNAME or credentials.password != PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return credentials
from fastapi import Depends

@app.get("/check-login", summary="Check if login credentials are valid")
async def check_login(credentials: HTTPBasicCredentials = Depends(authenticate)):
    return {"success": True}

# API endpoint to store images
@app.post("/store-image", summary="Store an image", response_description="The image has been stored successfully")
async def store_image(request: ImageRequest, credentials: HTTPBasicCredentials = Depends(authenticate)):
    try:
        db = SessionLocal()
        db_record = ImageResponse(image_base64=request.base64_image)
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        db.close()

        return {"message": "Image stored successfully", "id": db_record.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# API endpoint to store text
@app.post("/store-text", summary="Store text data", response_description="The text data has been stored successfully")
async def store_text(request: TextRequest, credentials: HTTPBasicCredentials = Depends(authenticate)):
    try:
        db = SessionLocal()
        db_record = TextResponse(text_data=request.text)
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        db.close()

        return {"message": "Text stored successfully", "id": db_record.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/get-latest-images", summary="Get latest images since a timestamp", response_description="Latest images")
async def get_latest_images(since: datetime = Query(...), credentials: HTTPBasicCredentials = Depends(authenticate)):
    db = SessionLocal()
    records = db.query(ImageResponse).filter(ImageResponse.created_at > since).all()
    db.close()
    return [{"id": record.id, "image_base64": record.image_base64, "created_at": record.created_at} for record in records]
# API endpoint to retrieve all images
@app.get("/get-all-images", summary="Get all stored images", response_description="All stored images")
async def get_all_images(credentials: HTTPBasicCredentials = Depends(authenticate)):
    db = SessionLocal()
    records = db.query(ImageResponse).all()
    db.close()
    return [{"id": record.id, "image_base64": record.image_base64, "created_at": record.created_at} for record in records]

# API endpoint to retrieve all texts
@app.get("/get-all-texts", summary="Get all stored texts", response_description="All stored texts")
async def get_all_texts(credentials: HTTPBasicCredentials = Depends(authenticate)):
    db = SessionLocal()
    records = db.query(TextResponse).all()
    db.close()
    return [{"id": record.id, "text_data": record.text_data, "created_at": record.created_at} for record in records]
# API endpoint to delete all images
@app.delete("/delete-all-images", summary="Delete all stored images", response_description="All images deleted")
async def delete_all_images(credentials: HTTPBasicCredentials = Depends(authenticate)):
    try:
        db = SessionLocal()
        deleted_count = db.query(ImageResponse).delete()
        db.commit()
        db.close()
        return {"message": f"All images deleted successfully. Total deleted: {deleted_count}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# API endpoint to delete all texts
@app.delete("/delete-all-texts", summary="Delete all stored texts", response_description="All texts deleted")
async def delete_all_texts(credentials: HTTPBasicCredentials = Depends(authenticate)):
    try:
        db = SessionLocal()
        deleted_count = db.query(TextResponse).delete()
        db.commit()
        db.close()
        return {"message": f"All texts deleted successfully. Total deleted: {deleted_count}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000
    )
