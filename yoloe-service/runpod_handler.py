import os
import uuid
import requests
import runpod
from src.yoloe_detector import YOLOEDetector, YOLOEConfig

# ----------------- Configuration ----------------- #
# Load configuration from environment variables
config = YOLOEConfig(
    model_path=os.environ.get("YOLOE_MODEL_PATH", "yolov8n.pt"),
    confidence_threshold=float(os.environ.get("CONFIDENCE_THRESHOLD", 0.5)),
    iou_threshold=float(os.environ.get("IOU_THRESHOLD", 0.45)),
    max_detections=int(os.environ.get("MAX_DETECTIONS", 100)),
    device=os.environ.get("DEVICE", "auto")
)

# ------------------ Model Loading ------------------ #
# Initialize the detector once when the worker starts.
# This is crucial for performance as the model will be loaded into GPU
# memory and reused for subsequent requests.
print("Initializing YOLOE Detector...")
detector = YOLOEDetector(config)
print("YOLOE Detector initialized successfully.")


# ------------------ Handler Function ------------------ #
def download_image(url, temp_dir="/tmp"):
    """Downloads an image from a URL and saves it to a temporary file."""
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Generate a unique filename
        filename = f"{uuid.uuid4().hex}.jpg"
        filepath = os.path.join(temp_dir, filename)

        # Save the image
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return filepath
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image: {e}")
        return None


async def handler(job):
    """
    The handler function that will be called by the RunPod serverless worker.
    """
    job_input = job['input']

    # Validate input
    if 'image_url' not in job_input:
        return {"error": "Missing 'image_url' in input"}

    image_url = job_input['image_url']
    prompt = job_input.get('prompt') # Optional prompt

    print(f"Processing job for image: {image_url}")

    # 1. Download the image from the provided URL
    temp_image_path = download_image(image_url)
    if not temp_image_path:
        return {"error": f"Failed to download image from {image_url}"}

    try:
        # 2. Run detection using the pre-loaded model
        if prompt:
            print(f"Running detection with prompt: {prompt}")
            detections = await detector.detect_items_with_prompt(temp_image_path, prompt)
        else:
            print("Running standard detection.")
            detections = await detector.detect_items(temp_image_path)

        # 3. Format the response
        # Convert Pydantic models to dictionaries for JSON serialization
        results = [d.dict() for d in detections]

        return {"detections": results}

    except Exception as e:
        print(f"An error occurred during detection: {e}")
        return {"error": str(e)}

    finally:
        # 4. Clean up the temporary file
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
            print(f"Cleaned up temporary file: {temp_image_path}")


# ------------------ Start Worker ------------------ #
# This starts the RunPod worker, which will listen for jobs
# and call the handler function.
if __name__ == "__main__":
    print("Starting RunPod worker...")
    runpod.serverless.start({"handler": handler})
