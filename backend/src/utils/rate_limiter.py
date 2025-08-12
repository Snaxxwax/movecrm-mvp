from datetime import datetime, timedelta
from src.models import db, RateLimit
import ipaddress

# Rate limiting configuration
RATE_LIMIT_WINDOW_MINUTES = 60  # 1 hour window
RATE_LIMIT_MAX_REQUESTS = 100   # Max requests per window
RATE_LIMIT_CLEANUP_INTERVAL = 3600  # Clean up old records every hour

def check_rate_limit(tenant_id, ip_address, endpoint, max_requests=None, window_minutes=None):
    """
    Check if the request should be rate limited
    
    Args:
        tenant_id: UUID of the tenant
        ip_address: Client IP address
        endpoint: API endpoint being accessed
        max_requests: Maximum requests allowed (defaults to global config)
        window_minutes: Time window in minutes (defaults to global config)
    
    Returns:
        bool: True if request is allowed, False if rate limited
    """
    try:
        # Use provided limits or defaults
        max_requests = max_requests or RATE_LIMIT_MAX_REQUESTS
        window_minutes = window_minutes or RATE_LIMIT_WINDOW_MINUTES
        
        # Calculate window start time
        now = datetime.now()
        window_start = now.replace(minute=0, second=0, microsecond=0)
        
        # Normalize IP address
        try:
            normalized_ip = str(ipaddress.ip_address(ip_address))
        except ValueError:
            normalized_ip = ip_address
        
        # Find or create rate limit record
        rate_limit = RateLimit.query.filter_by(
            tenant_id=tenant_id,
            ip_address=normalized_ip,
            endpoint=endpoint,
            window_start=window_start
        ).first()
        
        if not rate_limit:
            # Create new rate limit record
            rate_limit = RateLimit(
                tenant_id=tenant_id,
                ip_address=normalized_ip,
                endpoint=endpoint,
                request_count=1,
                window_start=window_start
            )
            db.session.add(rate_limit)
            db.session.commit()
            return True
        
        # Check if limit exceeded
        if rate_limit.request_count >= max_requests:
            return False
        
        # Increment counter
        rate_limit.request_count += 1
        db.session.commit()
        
        return True
        
    except Exception as e:
        # Log error but don't block requests on rate limiter failures
        print(f"Rate limiter error: {str(e)}")
        return True

def cleanup_old_rate_limits():
    """Clean up old rate limit records"""
    try:
        # Delete records older than 24 hours
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        deleted_count = RateLimit.query.filter(
            RateLimit.window_start < cutoff_time
        ).delete()
        
        db.session.commit()
        
        print(f"Cleaned up {deleted_count} old rate limit records")
        
    except Exception as e:
        db.session.rollback()
        print(f"Rate limit cleanup error: {str(e)}")

def get_rate_limit_status(tenant_id, ip_address, endpoint):
    """
    Get current rate limit status for debugging
    
    Returns:
        dict: Rate limit status information
    """
    try:
        # Normalize IP address
        try:
            normalized_ip = str(ipaddress.ip_address(ip_address))
        except ValueError:
            normalized_ip = ip_address
        
        # Get current window
        now = datetime.now()
        window_start = now.replace(minute=0, second=0, microsecond=0)
        
        rate_limit = RateLimit.query.filter_by(
            tenant_id=tenant_id,
            ip_address=normalized_ip,
            endpoint=endpoint,
            window_start=window_start
        ).first()
        
        if not rate_limit:
            return {
                'requests_made': 0,
                'requests_remaining': RATE_LIMIT_MAX_REQUESTS,
                'window_start': window_start.isoformat(),
                'window_end': (window_start + timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)).isoformat()
            }
        
        return {
            'requests_made': rate_limit.request_count,
            'requests_remaining': max(0, RATE_LIMIT_MAX_REQUESTS - rate_limit.request_count),
            'window_start': rate_limit.window_start.isoformat(),
            'window_end': (rate_limit.window_start + timedelta(minutes=RATE_LIMIT_WINDOW_MINUTES)).isoformat()
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'requests_made': 0,
            'requests_remaining': RATE_LIMIT_MAX_REQUESTS
        }

def reset_rate_limit(tenant_id, ip_address, endpoint):
    """
    Reset rate limit for specific tenant/IP/endpoint combination
    Useful for admin overrides
    """
    try:
        # Normalize IP address
        try:
            normalized_ip = str(ipaddress.ip_address(ip_address))
        except ValueError:
            normalized_ip = ip_address
        
        # Get current window
        now = datetime.now()
        window_start = now.replace(minute=0, second=0, microsecond=0)
        
        # Delete the rate limit record
        deleted_count = RateLimit.query.filter_by(
            tenant_id=tenant_id,
            ip_address=normalized_ip,
            endpoint=endpoint,
            window_start=window_start
        ).delete()
        
        db.session.commit()
        
        return deleted_count > 0
        
    except Exception as e:
        db.session.rollback()
        print(f"Rate limit reset error: {str(e)}")
        return False

