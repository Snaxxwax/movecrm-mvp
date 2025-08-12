from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import requests
import uuid
from src.models import db, DetectionJob, Quote, QuoteMedia, QuoteItem, ItemCatalog
from src.routes.auth import require_tenant, require_auth, require_role

detection_bp = Blueprint('detection', __name__)

def create_detection_job(tenant_id, quote_id, media_ids, job_type, prompt=None):
    """Create a new detection job"""
    job = DetectionJob(
        tenant_id=tenant_id,
        quote_id=quote_id,
        media_ids=media_ids,
        job_type=job_type,
        prompt=prompt,
        status='pending'
    )
    
    db.session.add(job)
    db.session.flush()
    return job

def call_yoloe_service(endpoint, data, files=None):
    """Call YOLOE service endpoint"""
    try:
        yoloe_url = current_app.config.get('YOLOE_SERVICE_URL', 'http://localhost:8001')
        url = f"{yoloe_url}{endpoint}"
        
        if files:
            response = requests.post(url, data=data, files=files, timeout=300)
        else:
            response = requests.post(url, json=data, timeout=300)
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"YOLOE service error: {str(e)}")

def map_detections_to_catalog(detections, tenant_id):
    """Map YOLOE detections to item catalog"""
    mapped_items = []
    
    # Get all catalog items for the tenant
    catalog_items = ItemCatalog.query.filter_by(
        tenant_id=tenant_id,
        is_active=True
    ).all()
    
    for detection in detections:
        detected_name = detection.get('name', '').lower()
        confidence = detection.get('confidence', 0)
        
        # Try to find matching catalog item
        matched_item = None
        best_match_score = 0
        
        for catalog_item in catalog_items:
            # Check exact name match
            if catalog_item.name.lower() == detected_name:
                matched_item = catalog_item
                best_match_score = 1.0
                break
            
            # Check aliases
            if catalog_item.aliases:
                for alias in catalog_item.aliases:
                    if alias.lower() == detected_name:
                        matched_item = catalog_item
                        best_match_score = 0.9
                        break
                    elif detected_name in alias.lower() or alias.lower() in detected_name:
                        if best_match_score < 0.7:
                            matched_item = catalog_item
                            best_match_score = 0.7
        
        # Create mapped item
        mapped_item = {
            'detected_name': detection.get('name'),
            'confidence_score': confidence,
            'quantity': detection.get('quantity', 1),
            'bounding_box': detection.get('bbox'),
            'catalog_item_id': str(matched_item.id) if matched_item else None,
            'catalog_item_name': matched_item.name if matched_item else None,
            'cubic_feet': float(matched_item.base_cubic_feet) if matched_item and matched_item.base_cubic_feet else None,
            'labor_multiplier': float(matched_item.labor_multiplier) if matched_item and matched_item.labor_multiplier else 1.0,
            'category': matched_item.category if matched_item else 'Unknown'
        }
        
        mapped_items.append(mapped_item)
    
    return mapped_items

@detection_bp.route('/text', methods=['POST'])
@require_tenant
@require_auth
@require_role(['admin', 'staff'])
def detect_text():
    """Text-based item detection with prompt"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('quote_id'):
            return jsonify({'error': 'Quote ID is required'}), 400
        
        if not data.get('prompt'):
            return jsonify({'error': 'Detection prompt is required'}), 400
        
        # Get quote and verify ownership
        quote = Quote.query.filter_by(
            id=data['quote_id'],
            tenant_id=request.tenant.id
        ).first()
        
        if not quote:
            return jsonify({'error': 'Quote not found'}), 404
        
        # Get media files for the quote
        media_files = QuoteMedia.query.filter_by(quote_id=quote.id).all()
        
        if not media_files:
            return jsonify({'error': 'No media files found for quote'}), 400
        
        # Create detection job
        media_ids = [media.id for media in media_files]
        job = create_detection_job(
            tenant_id=request.tenant.id,
            quote_id=quote.id,
            media_ids=media_ids,
            job_type='text',
            prompt=data['prompt']
        )
        
        # Prepare data for YOLOE service
        yoloe_data = {
            'prompt': data['prompt'],
            'job_id': str(job.id)
        }
        
        # Prepare files for upload
        files = []
        for media in media_files:
            # For now, we'll pass file paths. In production, you'd need to
            # handle file access properly (download from S3, etc.)
            files.append({
                'file_id': str(media.id),
                'file_path': media.file_path,
                'file_name': media.file_name
            })
        
        yoloe_data['files'] = files
        
        try:
            # Call YOLOE service
            job.status = 'processing'
            db.session.commit()
            
            result = call_yoloe_service('/detect/text', yoloe_data)
            
            # Process results
            if result.get('success'):
                detections = result.get('detections', [])
                mapped_items = map_detections_to_catalog(detections, request.tenant.id)
                
                job.status = 'completed'
                job.results = {
                    'detections': detections,
                    'mapped_items': mapped_items
                }
                job.completed_at = datetime.now()
                
                # Optionally auto-add items to quote
                if data.get('auto_add_items', False):
                    for item in mapped_items:
                        if item['catalog_item_id'] and item['confidence_score'] > 0.7:
                            quote_item = QuoteItem(
                                quote_id=quote.id,
                                item_catalog_id=item['catalog_item_id'],
                                detected_name=item['detected_name'],
                                quantity=item['quantity'],
                                cubic_feet=item['cubic_feet'],
                                confidence_score=item['confidence_score']
                            )
                            db.session.add(quote_item)
                
            else:
                job.status = 'failed'
                job.error_message = result.get('error', 'Unknown error')
            
            db.session.commit()
            
            return jsonify({
                'job_id': str(job.id),
                'status': job.status,
                'results': job.results,
                'error': job.error_message
            })
            
        except Exception as e:
            job.status = 'failed'
            job.error_message = str(e)
            db.session.commit()
            raise
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Detection failed', 'details': str(e)}), 500

@detection_bp.route('/auto', methods=['POST'])
@require_tenant
@require_auth
@require_role(['admin', 'staff'])
def detect_auto():
    """Automatic item detection without prompt"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('quote_id'):
            return jsonify({'error': 'Quote ID is required'}), 400
        
        # Get quote and verify ownership
        quote = Quote.query.filter_by(
            id=data['quote_id'],
            tenant_id=request.tenant.id
        ).first()
        
        if not quote:
            return jsonify({'error': 'Quote not found'}), 404
        
        # Get media files for the quote
        media_files = QuoteMedia.query.filter_by(quote_id=quote.id).all()
        
        if not media_files:
            return jsonify({'error': 'No media files found for quote'}), 400
        
        # Create detection job
        media_ids = [media.id for media in media_files]
        job = create_detection_job(
            tenant_id=request.tenant.id,
            quote_id=quote.id,
            media_ids=media_ids,
            job_type='auto'
        )
        
        # Prepare data for YOLOE service
        yoloe_data = {
            'job_id': str(job.id)
        }
        
        # Prepare files
        files = []
        for media in media_files:
            files.append({
                'file_id': str(media.id),
                'file_path': media.file_path,
                'file_name': media.file_name
            })
        
        yoloe_data['files'] = files
        
        try:
            # Call YOLOE service
            job.status = 'processing'
            db.session.commit()
            
            result = call_yoloe_service('/detect/auto', yoloe_data)
            
            # Process results
            if result.get('success'):
                detections = result.get('detections', [])
                mapped_items = map_detections_to_catalog(detections, request.tenant.id)
                
                job.status = 'completed'
                job.results = {
                    'detections': detections,
                    'mapped_items': mapped_items
                }
                job.completed_at = datetime.now()
                
                # Auto-add high-confidence items
                for item in mapped_items:
                    if item['catalog_item_id'] and item['confidence_score'] > 0.8:
                        quote_item = QuoteItem(
                            quote_id=quote.id,
                            item_catalog_id=item['catalog_item_id'],
                            detected_name=item['detected_name'],
                            quantity=item['quantity'],
                            cubic_feet=item['cubic_feet'],
                            confidence_score=item['confidence_score']
                        )
                        db.session.add(quote_item)
                
            else:
                job.status = 'failed'
                job.error_message = result.get('error', 'Unknown error')
            
            db.session.commit()
            
            return jsonify({
                'job_id': str(job.id),
                'status': job.status,
                'results': job.results,
                'error': job.error_message
            })
            
        except Exception as e:
            job.status = 'failed'
            job.error_message = str(e)
            db.session.commit()
            raise
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Detection failed', 'details': str(e)}), 500

@detection_bp.route('/jobs/<job_id>', methods=['GET'])
@require_tenant
@require_auth
@require_role(['admin', 'staff'])
def get_detection_job(job_id):
    """Get detection job status and results"""
    try:
        job = DetectionJob.query.filter_by(
            id=job_id,
            tenant_id=request.tenant.id
        ).first()
        
        if not job:
            return jsonify({'error': 'Detection job not found'}), 404
        
        return jsonify(job.to_dict())
        
    except Exception as e:
        return jsonify({'error': 'Failed to get detection job', 'details': str(e)}), 500

@detection_bp.route('/jobs', methods=['GET'])
@require_tenant
@require_auth
@require_role(['admin', 'staff'])
def list_detection_jobs():
    """List detection jobs for the tenant"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status')
        
        query = DetectionJob.query.filter_by(tenant_id=request.tenant.id)
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        jobs = query.order_by(DetectionJob.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'jobs': [job.to_dict() for job in jobs.items],
            'total': jobs.total,
            'pages': jobs.pages,
            'current_page': page,
            'per_page': per_page
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to list detection jobs', 'details': str(e)}), 500

