import boto3
import os
import uuid
from botocore.exceptions import ClientError, NoCredentialsError
from werkzeug.utils import secure_filename

def get_s3_client(config):
    """Get configured S3 client"""
    try:
        # Check if S3 credentials are configured
        if not config.get('S3_ACCESS_KEY') or not config.get('S3_SECRET_KEY'):
            return None
        
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=config['S3_ACCESS_KEY'],
            aws_secret_access_key=config['S3_SECRET_KEY'],
            endpoint_url=config.get('S3_ENDPOINT'),
            region_name=config.get('S3_REGION', 'us-east-1')
        )
        
        return s3_client
        
    except Exception as e:
        print(f"S3 client creation error: {str(e)}")
        return None

def upload_file_to_s3(file, key, config):
    """
    Upload file to S3-compatible storage
    
    Args:
        file: File object to upload
        key: S3 object key (path)
        config: Flask app config
    
    Returns:
        str: File URL or local path
    """
    try:
        s3_client = get_s3_client(config)
        bucket_name = config.get('S3_BUCKET')
        
        if s3_client and bucket_name:
            # Upload to S3
            try:
                s3_client.upload_fileobj(
                    file,
                    bucket_name,
                    key,
                    ExtraArgs={
                        'ContentType': file.content_type or 'application/octet-stream'
                    }
                )
                
                # Return S3 URL
                if config.get('S3_ENDPOINT'):
                    # Custom S3 endpoint
                    endpoint = config['S3_ENDPOINT'].rstrip('/')
                    return f"{endpoint}/{bucket_name}/{key}"
                else:
                    # AWS S3
                    region = config.get('S3_REGION', 'us-east-1')
                    return f"https://{bucket_name}.s3.{region}.amazonaws.com/{key}"
                
            except ClientError as e:
                print(f"S3 upload error: {str(e)}")
                # Fall back to local storage
                return upload_file_locally(file, key, config)
        else:
            # No S3 configured, use local storage
            return upload_file_locally(file, key, config)
            
    except Exception as e:
        print(f"File upload error: {str(e)}")
        raise

def upload_file_locally(file, key, config):
    """
    Upload file to local storage as fallback
    
    Args:
        file: File object to upload
        key: File path
        config: Flask app config
    
    Returns:
        str: Local file path
    """
    try:
        # Create uploads directory
        upload_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Create subdirectories from key
        file_path = os.path.join(upload_dir, key)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save file
        file.save(file_path)
        
        # Return relative path for database storage
        return f"/uploads/{key}"
        
    except Exception as e:
        print(f"Local file upload error: {str(e)}")
        raise

def delete_file(file_path, config):
    """
    Delete file from storage
    
    Args:
        file_path: File path or URL
        config: Flask app config
    
    Returns:
        bool: Success status
    """
    try:
        if file_path.startswith('http'):
            # S3 file - extract key from URL
            s3_client = get_s3_client(config)
            bucket_name = config.get('S3_BUCKET')
            
            if s3_client and bucket_name:
                # Extract key from URL
                if config.get('S3_ENDPOINT'):
                    # Custom endpoint
                    endpoint = config['S3_ENDPOINT'].rstrip('/')
                    key = file_path.replace(f"{endpoint}/{bucket_name}/", "")
                else:
                    # AWS S3
                    region = config.get('S3_REGION', 'us-east-1')
                    key = file_path.replace(f"https://{bucket_name}.s3.{region}.amazonaws.com/", "")
                
                s3_client.delete_object(Bucket=bucket_name, Key=key)
                return True
        else:
            # Local file
            local_path = os.path.join(
                os.path.dirname(__file__), '..', '..', 
                file_path.lstrip('/')
            )
            
            if os.path.exists(local_path):
                os.remove(local_path)
                return True
        
        return False
        
    except Exception as e:
        print(f"File deletion error: {str(e)}")
        return False

def get_file_url(file_path, config):
    """
    Get public URL for file
    
    Args:
        file_path: File path from database
        config: Flask app config
    
    Returns:
        str: Public URL
    """
    try:
        if file_path.startswith('http'):
            # Already a URL
            return file_path
        elif file_path.startswith('/uploads/'):
            # Local file - return relative URL
            return file_path
        else:
            # Assume S3 key
            bucket_name = config.get('S3_BUCKET')
            if config.get('S3_ENDPOINT'):
                endpoint = config['S3_ENDPOINT'].rstrip('/')
                return f"{endpoint}/{bucket_name}/{file_path}"
            else:
                region = config.get('S3_REGION', 'us-east-1')
                return f"https://{bucket_name}.s3.{region}.amazonaws.com/{file_path}"
                
    except Exception as e:
        print(f"File URL generation error: {str(e)}")
        return file_path

def generate_unique_filename(original_filename):
    """Generate unique filename while preserving extension"""
    if not original_filename:
        return str(uuid.uuid4())
    
    name, ext = os.path.splitext(secure_filename(original_filename))
    unique_name = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
    return unique_name

def validate_file_type(filename, allowed_extensions):
    """Validate file type against allowed extensions"""
    if not filename:
        return False
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def get_file_size(file):
    """Get file size in bytes"""
    try:
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        return size
    except Exception:
        return 0

