import os
import cv2
import numpy as np
from typing import List, Dict, Any, Optional
import logging
import time
from PIL import Image
import torch

try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False
    logging.warning("Ultralytics not available, using mock detector")

from .models import Detection, BoundingBox, YOLOEConfig, MovingItemClasses, DetectionMetrics

logger = logging.getLogger(__name__)

class YOLOEDetector:
    """YOLOE-based item detector for moving quotes"""
    
    def __init__(self, config: Optional[YOLOEConfig] = None):
        self.config = config or YOLOEConfig()
        self.model = None
        self.moving_classes = MovingItemClasses()
        self.class_mapping = self._build_class_mapping()
        
        # Initialize model
        self._load_model()
    
    def _load_model(self):
        """Load YOLOE model"""
        try:
            if not ULTRALYTICS_AVAILABLE:
                logger.warning("Using mock detector - Ultralytics not available")
                return
            
            # Check if custom model exists, otherwise use default
            model_path = self.config.model_path
            if not os.path.exists(model_path):
                logger.info(f"Model {model_path} not found, using YOLOv8n")
                model_path = "yolov8n.pt"
            
            self.model = YOLO(model_path)
            
            # Set device
            if self.config.device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                device = self.config.device
            
            self.model.to(device)
            logger.info(f"YOLOE model loaded successfully on {device}")
            
        except Exception as e:
            logger.error(f"Failed to load YOLOE model: {str(e)}")
            self.model = None
    
    def _build_class_mapping(self) -> Dict[str, str]:
        """Build mapping from YOLO classes to moving item categories"""
        mapping = {}
        
        # Map furniture items
        for item in self.moving_classes.furniture:
            mapping[item.lower()] = "Furniture"
        
        # Map appliances
        for item in self.moving_classes.appliances:
            mapping[item.lower()] = "Appliances"
        
        # Map electronics
        for item in self.moving_classes.electronics:
            mapping[item.lower()] = "Electronics"
        
        # Map boxes
        for item in self.moving_classes.boxes:
            mapping[item.lower()] = "Boxes"
        
        # Map miscellaneous
        for item in self.moving_classes.miscellaneous:
            mapping[item.lower()] = "Miscellaneous"
        
        return mapping
    
    def _is_moving_related(self, class_name: str) -> bool:
        """Check if detected class is relevant for moving"""
        class_name_lower = class_name.lower()
        
        # Check direct mapping
        if class_name_lower in self.class_mapping:
            return True
        
        # Check partial matches
        moving_keywords = [
            "furniture", "chair", "table", "sofa", "bed", "dresser", "cabinet",
            "refrigerator", "washing", "dryer", "microwave", "oven", "tv",
            "computer", "box", "container", "lamp", "mirror", "bicycle"
        ]
        
        return any(keyword in class_name_lower for keyword in moving_keywords)
    
    def _get_category(self, class_name: str) -> str:
        """Get category for detected item"""
        class_name_lower = class_name.lower()
        return self.class_mapping.get(class_name_lower, "Miscellaneous")
    
    def _estimate_quantity(self, detections: List[Dict]) -> List[Dict]:
        """Estimate quantity of similar items"""
        # Group similar detections
        grouped = {}
        
        for detection in detections:
            class_name = detection["name"].lower()
            if class_name not in grouped:
                grouped[class_name] = []
            grouped[class_name].append(detection)
        
        # Update quantities
        result = []
        for class_name, group in grouped.items():
            if len(group) == 1:
                # Single item
                group[0]["quantity"] = 1
                result.append(group[0])
            else:
                # Multiple similar items - merge or keep separate based on confidence
                high_conf = [d for d in group if d["confidence"] > 0.8]
                if high_conf:
                    # Use highest confidence detection and set quantity
                    best = max(high_conf, key=lambda x: x["confidence"])
                    best["quantity"] = len(group)
                    result.append(best)
                else:
                    # Keep all detections
                    for detection in group:
                        detection["quantity"] = 1
                        result.append(detection)
        
        return result
    
    async def detect_items(self, image_path: str) -> List[Detection]:
        """Detect items in image without prompt"""
        try:
            start_time = time.time()
            
            if not self.model:
                # Mock detection for testing
                return self._mock_detection(image_path)
            
            # Load and preprocess image
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Run inference
            results = self.model(
                image_path,
                conf=self.config.confidence_threshold,
                iou=self.config.iou_threshold,
                max_det=self.config.max_detections
            )
            
            detections = []
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get class name
                        class_id = int(box.cls[0])
                        class_name = self.model.names[class_id]
                        
                        # Filter for moving-related items
                        if not self._is_moving_related(class_name):
                            continue
                        
                        # Get bounding box
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        img_height, img_width = result.orig_shape
                        
                        # Normalize coordinates
                        bbox = BoundingBox(
                            x=x1 / img_width,
                            y=y1 / img_height,
                            width=(x2 - x1) / img_width,
                            height=(y2 - y1) / img_height
                        )
                        
                        detection = Detection(
                            name=class_name,
                            confidence=float(box.conf[0]),
                            bbox=bbox,
                            quantity=1,
                            category=self._get_category(class_name)
                        )
                        
                        detections.append(detection)
            
            # Estimate quantities
            detection_dicts = [d.dict() for d in detections]
            detection_dicts = self._estimate_quantity(detection_dicts)
            
            # Convert back to Detection objects
            final_detections = [Detection(**d) for d in detection_dicts]
            
            processing_time = time.time() - start_time
            logger.info(f"Detected {len(final_detections)} items in {processing_time:.2f}s")
            
            return final_detections
            
        except Exception as e:
            logger.error(f"Detection failed for {image_path}: {str(e)}")
            raise
    
    async def detect_items_with_prompt(self, image_path: str, prompt: str) -> List[Detection]:
        """Detect items in image with text prompt"""
        try:
            # For now, use regular detection and filter by prompt keywords
            # In a full implementation, this would use a vision-language model
            detections = await self.detect_items(image_path)
            
            # Filter detections based on prompt keywords
            prompt_lower = prompt.lower()
            prompt_keywords = prompt_lower.split()
            
            filtered_detections = []
            for detection in detections:
                # Check if detection name matches prompt keywords
                detection_name_lower = detection.name.lower()
                
                # Exact match
                if detection_name_lower in prompt_lower:
                    filtered_detections.append(detection)
                    continue
                
                # Keyword match
                if any(keyword in detection_name_lower for keyword in prompt_keywords):
                    filtered_detections.append(detection)
                    continue
                
                # Category match
                if detection.category and detection.category.lower() in prompt_lower:
                    filtered_detections.append(detection)
            
            logger.info(f"Filtered {len(filtered_detections)} items matching prompt: {prompt}")
            return filtered_detections
            
        except Exception as e:
            logger.error(f"Prompted detection failed for {image_path}: {str(e)}")
            raise
    
    def _mock_detection(self, image_path: str) -> List[Detection]:
        """Mock detection for testing when YOLO is not available"""
        logger.info(f"Using mock detection for {image_path}")
        
        # Return some mock detections
        mock_detections = [
            Detection(
                name="sofa",
                confidence=0.85,
                bbox=BoundingBox(x=0.1, y=0.2, width=0.4, height=0.3),
                quantity=1,
                category="Furniture"
            ),
            Detection(
                name="dining table",
                confidence=0.78,
                bbox=BoundingBox(x=0.5, y=0.4, width=0.3, height=0.2),
                quantity=1,
                category="Furniture"
            ),
            Detection(
                name="chair",
                confidence=0.72,
                bbox=BoundingBox(x=0.2, y=0.6, width=0.15, height=0.25),
                quantity=4,
                category="Furniture"
            )
        ]
        
        return mock_detections
    
    def get_metrics(self) -> DetectionMetrics:
        """Get detection performance metrics"""
        # This would track actual metrics in a real implementation
        return DetectionMetrics(
            total_detections=0,
            high_confidence_detections=0,
            processing_time_seconds=0.0,
            average_confidence=0.0,
            files_processed=0,
            files_failed=0
        )
    
    def update_config(self, config: YOLOEConfig):
        """Update detector configuration"""
        self.config = config
        # Reload model if needed
        if self.model:
            self._load_model()

