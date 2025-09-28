from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import base64
import io
import numpy as np
import cv2
from PIL import Image

# Import our face analyzer
from face_analyzer import get_face_analyzer, FaceAnalysisResult

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Smart Face Analytics API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic Models
class FaceAnalysisResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    faces_detected: int
    total_confidence: float
    results: List[Dict[str, Any]]
    processing_time_ms: float
    image_info: Dict[str, Any]

class AnalysisHistory(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    faces_count: int
    avg_age: float
    emotions: List[str]
    races: List[str]
    processing_time_ms: float
    session_id: Optional[str] = None

class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

class ImageAnalysisRequest(BaseModel):
    image_data: str  # base64 encoded image
    session_id: Optional[str] = None

# Initialize face analyzer
logger.info("Initializing Face Analyzer...")
analyzer = get_face_analyzer()
logger.info("Face Analyzer initialized successfully!")

# Original routes
@api_router.get("/")
async def root():
    return {"message": "Smart Face Analytics API is running!", "status": "healthy"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Face Analysis Routes
@api_router.post("/analyze-image", response_model=FaceAnalysisResponse)
async def analyze_image_endpoint(request: ImageAnalysisRequest):
    """Analyze faces in uploaded image"""
    try:
        import time
        start_time = time.time()
        
        logger.info("Starting image analysis...")
        
        # Analyze image using our face analyzer
        analysis_results = analyzer.analyze_image_from_base64(request.image_data)
        
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Process results
        faces_detected = len(analysis_results)
        total_confidence = sum(result.confidence for result in analysis_results) if analysis_results else 0
        
        # Convert results to dictionary format
        results_data = []
        for i, result in enumerate(analysis_results):
            result_dict = {
                "face_id": i + 1,
                "bbox": {
                    "x": result.bbox[0],
                    "y": result.bbox[1], 
                    "width": result.bbox[2],
                    "height": result.bbox[3]
                },
                "confidence": result.confidence,
                "age": {
                    "value": result.age,
                    "confidence": result.age_confidence
                },
                "race": {
                    "value": result.race,
                    "confidence": result.race_confidence
                },
                "emotion": {
                    "value": result.emotion,
                    "confidence": result.emotion_confidence
                },
                "landmarks_count": len(result.landmarks)
            }
            results_data.append(result_dict)
        
        # Create response
        response = FaceAnalysisResponse(
            faces_detected=faces_detected,
            total_confidence=total_confidence,
            results=results_data,
            processing_time_ms=processing_time,
            image_info={
                "format": "base64",
                "faces_found": faces_detected
            }
        )
        
        # Store analysis history
        if faces_detected > 0:
            avg_age = sum(result.age for result in analysis_results) / faces_detected
            emotions = [result.emotion for result in analysis_results]
            races = [result.race for result in analysis_results]
            
            history_entry = AnalysisHistory(
                faces_count=faces_detected,
                avg_age=avg_age,
                emotions=emotions,
                races=races,
                processing_time_ms=processing_time,
                session_id=request.session_id
            )
            
            await db.analysis_history.insert_one(history_entry.dict())
        
        logger.info(f"Analysis completed: {faces_detected} faces detected in {processing_time:.2f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Error in image analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@api_router.post("/analyze-upload")
async def analyze_uploaded_file(file: UploadFile = File(...), session_id: str = Form(None)):
    """Analyze faces in uploaded file"""
    try:
        import time
        start_time = time.time()
        
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read file contents
        file_contents = await file.read()
        
        # Analyze image
        analysis_results = analyzer.analyze_image_from_bytes(file_contents)
        
        processing_time = (time.time() - start_time) * 1000
        
        # Process results (same as above)
        faces_detected = len(analysis_results)
        total_confidence = sum(result.confidence for result in analysis_results) if analysis_results else 0
        
        results_data = []
        for i, result in enumerate(analysis_results):
            result_dict = {
                "face_id": i + 1,
                "bbox": {
                    "x": result.bbox[0],
                    "y": result.bbox[1], 
                    "width": result.bbox[2],
                    "height": result.bbox[3]
                },
                "confidence": result.confidence,
                "age": {
                    "value": result.age,
                    "confidence": result.age_confidence
                },
                "race": {
                    "value": result.race,
                    "confidence": result.race_confidence
                },
                "emotion": {
                    "value": result.emotion,
                    "confidence": result.emotion_confidence
                },
                "landmarks_count": len(result.landmarks)
            }
            results_data.append(result_dict)
        
        response = FaceAnalysisResponse(
            faces_detected=faces_detected,
            total_confidence=total_confidence,
            results=results_data,
            processing_time_ms=processing_time,
            image_info={
                "filename": file.filename,
                "size": len(file_contents),
                "content_type": file.content_type,
                "faces_found": faces_detected
            }
        )
        
        # Store history
        if faces_detected > 0:
            avg_age = sum(result.age for result in analysis_results) / faces_detected
            emotions = [result.emotion for result in analysis_results]
            races = [result.race for result in analysis_results]
            
            history_entry = AnalysisHistory(
                faces_count=faces_detected,
                avg_age=avg_age,
                emotions=emotions,
                races=races,
                processing_time_ms=processing_time,
                session_id=session_id
            )
            
            await db.analysis_history.insert_one(history_entry.dict())
        
        return response
        
    except Exception as e:
        logger.error(f"Error in file analysis: {e}")
        raise HTTPException(status_code=500, detail=f"File analysis failed: {str(e)}")

@api_router.get("/analysis-history", response_model=List[AnalysisHistory])
async def get_analysis_history(session_id: Optional[str] = None, limit: int = 100):
    """Get analysis history"""
    try:
        query = {}
        if session_id:
            query["session_id"] = session_id
        
        history = await db.analysis_history.find(query).sort("timestamp", -1).limit(limit).to_list(limit)
        return [AnalysisHistory(**item) for item in history]
        
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch history")

@api_router.get("/analytics/summary")
async def get_analytics_summary(session_id: Optional[str] = None):
    """Get analytics summary"""
    try:
        query = {}
        if session_id:
            query["session_id"] = session_id
        
        # Get all history records
        history = await db.analysis_history.find(query).to_list(1000)
        
        if not history:
            return {
                "total_analyses": 0,
                "total_faces": 0,
                "avg_age": 0,
                "emotion_distribution": {},
                "race_distribution": {},
                "avg_processing_time": 0
            }
        
        # Calculate statistics
        total_analyses = len(history)
        total_faces = sum(item['faces_count'] for item in history)
        
        # Average age calculation
        all_ages = []
        all_emotions = []
        all_races = []
        processing_times = []
        
        for item in history:
            if item.get('avg_age'):
                all_ages.append(item['avg_age'])
            if item.get('emotions'):
                all_emotions.extend(item['emotions'])
            if item.get('races'):
                all_races.extend(item['races'])
            if item.get('processing_time_ms'):
                processing_times.append(item['processing_time_ms'])
        
        avg_age = sum(all_ages) / len(all_ages) if all_ages else 0
        
        # Emotion distribution
        emotion_dist = {}
        for emotion in all_emotions:
            emotion_dist[emotion] = emotion_dist.get(emotion, 0) + 1
        
        # Race distribution
        race_dist = {}
        for race in all_races:
            race_dist[race] = race_dist.get(race, 0) + 1
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        return {
            "total_analyses": total_analyses,
            "total_faces": total_faces,
            "avg_age": round(avg_age, 1),
            "emotion_distribution": emotion_dist,
            "race_distribution": race_dist,
            "avg_processing_time": round(avg_processing_time, 2)
        }
        
    except Exception as e:
        logger.error(f"Error generating analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate analytics")

@api_router.delete("/analysis-history")
async def clear_analysis_history(session_id: Optional[str] = None):
    """Clear analysis history"""
    try:
        query = {}
        if session_id:
            query["session_id"] = session_id
        
        result = await db.analysis_history.delete_many(query)
        
        return {
            "deleted_count": result.deleted_count,
            "message": f"Cleared {result.deleted_count} history entries"
        }
        
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear history")

# Model info endpoint
@api_router.get("/models/info")
async def get_model_info():
    """Get information about loaded models"""
    return {
        "face_detection": "MediaPipe Face Detection",
        "age_estimation": "HuggingFace ViT Age Classifier",
        "emotion_recognition": "HuggingFace Emotion Classification",
        "race_classification": "HuggingFace Gender/Demographics Classification",
        "landmarks": "MediaPipe Face Mesh",
        "device": analyzer.device,
        "status": "loaded"
    }

# Health check endpoint
@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "models_loaded": True,
        "database_connected": True
    }

# Include the router in the main app
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Smart Face Analytics API starting up...")
    logger.info("Models loaded and ready for analysis!")