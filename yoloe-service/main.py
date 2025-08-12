#!/usr/bin/env python3
"""
YOLOE Detection Service - Simplified Mock Version
This is a mock service that returns fake detection results for development.
Replace with actual YOLO implementation when ready.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import os
import random
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="YOLOE Detection Service",
    description="Mock object detection service for MoveCRM",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock items that could be detected
MOCK_ITEMS = [
    {"name": "sofa", "category": "furniture", "cubic_feet": 35.0},
    {"name": "dining table", "category": "furniture", "cubic_feet": 25.0},
    {"name": "chair", "category": "furniture", "cubic_feet": 5.0},
    {"name": "refrigerator", "category": "appliance", "cubic_feet": 45.0},
    {"name": "washing machine", "category": "appliance", "cubic_feet": 15.0},
    {"name": "mattress", "category": "bedroom", "cubic_feet": 20.0},
    {"name": "dresser", "category": "bedroom", "cubic_feet": 25.0},
    {"name": "box", "category": "packing", "cubic_feet": 3.0},
    {"name": "television", "category": "electronics", "cubic_feet": 8.0},
    {"name": "desk", "category": "furniture", "cubic_feet": 20.0},
]

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "YOLOE Detection Service",
        "status": "running",
        "version": "1.0.0",
        "mode": "mock"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "yoloe",
        "timestamp": datetime.utcnow().isoformat(),
        "mode": "mock"
    }

@app.post("/detect")
async def detect_objects(file: UploadFile = File(...)):
    """
    Mock object detection endpoint
    Returns fake detection results for development
    """
    try:
        # Log the upload
        logger.info(f"Received file: {file.filename}, size: {file.size if hasattr(file, 'size') else 'unknown'}")
        
        # Generate random mock detections
        num_detections = random.randint(3, 8)
        detections = []
        
        for _ in range(num_detections):
            item = random.choice(MOCK_ITEMS)
            detection = {
                "item": item["name"],
                "category": item["category"],
                "confidence": round(random.uniform(0.7, 0.99), 2),
                "cubic_feet": item["cubic_feet"],
                "quantity": random.randint(1, 3),
                "bbox": {
                    "x": random.randint(50, 400),
                    "y": random.randint(50, 400),
                    "width": random.randint(100, 200),
                    "height": random.randint(100, 200)
                }
            }
            detections.append(detection)
        
        # Calculate totals
        total_items = sum(d["quantity"] for d in detections)
        total_cubic_feet = sum(d["cubic_feet"] * d["quantity"] for d in detections)
        
        response = {
            "status": "success",
            "mode": "mock",
            "filename": file.filename,
            "detections": detections,
            "summary": {
                "total_items": total_items,
                "unique_items": len(detections),
                "total_cubic_feet": round(total_cubic_feet, 2),
                "processing_time": round(random.uniform(0.5, 2.0), 2)
            },
            "message": "Mock detection results - replace with actual YOLO when ready"
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Error in detection: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/detect/batch")
async def detect_batch(files: List[UploadFile] = File(...)):
    """
    Batch detection endpoint for multiple files
    """
    results = []
    for file in files:
        result = await detect_objects(file)
        results.append(result)
    
    return {
        "status": "success",
        "mode": "mock",
        "total_files": len(files),
        "results": results
    }

@app.post("/detect/text")
async def detect_from_text(description: str):
    """
    Mock text-based detection
    Parse text description and return estimated items
    """
    # Simple keyword matching for mock
    detected_items = []
    description_lower = description.lower()
    
    for item in MOCK_ITEMS:
        if item["name"] in description_lower:
            detected_items.append({
                "item": item["name"],
                "category": item["category"],
                "confidence": 0.95,
                "cubic_feet": item["cubic_feet"],
                "quantity": 1,
                "source": "text"
            })
    
    # If no items detected, add some default items
    if not detected_items:
        detected_items = [
            {
                "item": "box",
                "category": "packing",
                "confidence": 0.8,
                "cubic_feet": 3.0,
                "quantity": 5,
                "source": "text"
            }
        ]
    
    return {
        "status": "success",
        "mode": "mock",
        "source": "text",
        "detections": detected_items,
        "original_text": description
    }

@app.get("/stats")
async def get_stats():
    """Get service statistics"""
    return {
        "service": "yoloe",
        "mode": "mock",
        "available_items": len(MOCK_ITEMS),
        "categories": list(set(item["category"] for item in MOCK_ITEMS)),
        "status": "operational"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SERVICE_PORT", "8001"))
    host = os.getenv("SERVICE_HOST", "0.0.0.0")
    
    logger.info(f"Starting YOLOE Mock Service on {host}:{port}")
    uvicorn.run(app, host=host, port=port, reload=True)
