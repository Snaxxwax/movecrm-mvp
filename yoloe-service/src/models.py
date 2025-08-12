from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class FileInfo(BaseModel):
    """File information for detection"""
    file_id: Optional[str] = None
    file_path: str
    file_name: str

class DetectionRequest(BaseModel):
    """Request model for text-based detection"""
    job_id: Optional[str] = None
    prompt: str = Field(..., description="Text prompt for item detection")
    files: List[FileInfo] = Field(..., description="List of files to process")

class BoundingBox(BaseModel):
    """Bounding box coordinates"""
    x: float = Field(..., description="X coordinate (normalized 0-1)")
    y: float = Field(..., description="Y coordinate (normalized 0-1)")
    width: float = Field(..., description="Width (normalized 0-1)")
    height: float = Field(..., description="Height (normalized 0-1)")

class Detection(BaseModel):
    """Single item detection result"""
    name: str = Field(..., description="Detected item name")
    confidence: float = Field(..., description="Detection confidence (0-1)")
    bbox: Optional[BoundingBox] = Field(None, description="Bounding box coordinates")
    quantity: int = Field(default=1, description="Estimated quantity")
    category: Optional[str] = Field(None, description="Item category")
    file_path: Optional[str] = Field(None, description="Source file path")
    file_name: Optional[str] = Field(None, description="Source file name")
    file_id: Optional[str] = Field(None, description="Source file ID")

class DetectionResponse(BaseModel):
    """Response model for detection requests"""
    success: bool = Field(..., description="Whether the request was successful")
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Job status (processing, completed, failed)")
    message: Optional[str] = Field(None, description="Status message")
    detections: Optional[List[Detection]] = Field(None, description="Detection results")
    error: Optional[str] = Field(None, description="Error message if failed")

class JobStatus(BaseModel):
    """Job status and results"""
    job_id: str = Field(..., description="Job identifier")
    status: str = Field(..., description="Job status")
    created_at: str = Field(..., description="Job creation timestamp")
    completed_at: Optional[str] = Field(None, description="Job completion timestamp")
    files_count: int = Field(default=0, description="Number of files processed")
    detections: List[Detection] = Field(default=[], description="Detection results")
    error: Optional[str] = Field(None, description="Error message if failed")

class RunPodJobRequest(BaseModel):
    """RunPod job request model"""
    template_id: str = Field(..., description="RunPod template ID")
    job_type: str = Field(..., description="Job type (auto or text)")
    files: List[FileInfo] = Field(..., description="Files to process")
    prompt: Optional[str] = Field(None, description="Detection prompt for text jobs")
    webhook_url: Optional[str] = Field(None, description="Webhook URL for results")

class RunPodJobResponse(BaseModel):
    """RunPod job response model"""
    job_id: str = Field(..., description="RunPod job ID")
    status: str = Field(..., description="Job status")
    created_at: str = Field(..., description="Job creation timestamp")

class YOLOEConfig(BaseModel):
    """YOLOE model configuration"""
    model_path: str = Field(default="yolov8n.pt", description="Path to YOLOE model")
    confidence_threshold: float = Field(default=0.5, description="Minimum confidence threshold")
    iou_threshold: float = Field(default=0.45, description="IoU threshold for NMS")
    max_detections: int = Field(default=100, description="Maximum detections per image")
    device: str = Field(default="auto", description="Device to run inference on")

class MovingItemClasses(BaseModel):
    """Moving-specific item classes mapping"""
    furniture: List[str] = Field(default=[
        "chair", "table", "sofa", "bed", "dresser", "bookshelf", "desk",
        "cabinet", "wardrobe", "nightstand", "dining table", "coffee table"
    ])
    appliances: List[str] = Field(default=[
        "refrigerator", "washing machine", "dryer", "dishwasher", "microwave",
        "oven", "stove", "air conditioner", "water heater"
    ])
    electronics: List[str] = Field(default=[
        "tv", "computer", "laptop", "monitor", "printer", "stereo", "speaker"
    ])
    boxes: List[str] = Field(default=[
        "box", "cardboard box", "moving box", "storage box", "container"
    ])
    miscellaneous: List[str] = Field(default=[
        "lamp", "mirror", "picture", "plant", "bicycle", "exercise equipment"
    ])

class DetectionMetrics(BaseModel):
    """Detection performance metrics"""
    total_detections: int = Field(default=0)
    high_confidence_detections: int = Field(default=0)
    processing_time_seconds: float = Field(default=0.0)
    average_confidence: float = Field(default=0.0)
    files_processed: int = Field(default=0)
    files_failed: int = Field(default=0)

