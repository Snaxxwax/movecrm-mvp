from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB, INET
from sqlalchemy import func
import uuid

db = SQLAlchemy()

class Tenant(db.Model):
    __tablename__ = 'tenants'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    domain = db.Column(db.String(255))
    logo_url = db.Column(db.Text)
    brand_colors = db.Column(JSONB, default={})
    settings = db.Column(JSONB, default={})
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    users = db.relationship('User', backref='tenant', lazy=True, cascade='all, delete-orphan')
    item_catalog = db.relationship('ItemCatalog', backref='tenant', lazy=True, cascade='all, delete-orphan')
    pricing_rules = db.relationship('PricingRule', backref='tenant', lazy=True, cascade='all, delete-orphan')
    quotes = db.relationship('Quote', backref='tenant', lazy=True, cascade='all, delete-orphan')
    detection_jobs = db.relationship('DetectionJob', backref='tenant', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'slug': self.slug,
            'name': self.name,
            'domain': self.domain,
            'logo_url': self.logo_url,
            'brand_colors': self.brand_colors,
            'settings': self.settings,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    supertokens_user_id = db.Column(db.String(255), unique=True)
    email = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(50), default='customer')  # admin, staff, customer
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (db.UniqueConstraint('tenant_id', 'email'),)
    
    # Relationships
    quotes = db.relationship('Quote', backref='customer', lazy=True)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'supertokens_user_id': self.supertokens_user_id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ItemCatalog(db.Model):
    __tablename__ = 'item_catalog'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    aliases = db.Column(ARRAY(db.Text))
    category = db.Column(db.String(100))
    base_cubic_feet = db.Column(db.Numeric(8, 2))
    labor_multiplier = db.Column(db.Numeric(4, 2), default=1.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    quote_items = db.relationship('QuoteItem', backref='catalog_item', lazy=True)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'name': self.name,
            'aliases': self.aliases,
            'category': self.category,
            'base_cubic_feet': float(self.base_cubic_feet) if self.base_cubic_feet else None,
            'labor_multiplier': float(self.labor_multiplier) if self.labor_multiplier else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class PricingRule(db.Model):
    __tablename__ = 'pricing_rules'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    rate_per_cubic_foot = db.Column(db.Numeric(8, 2), nullable=False)
    labor_rate_per_hour = db.Column(db.Numeric(8, 2), nullable=False)
    minimum_charge = db.Column(db.Numeric(8, 2), default=0)
    distance_rate_per_mile = db.Column(db.Numeric(8, 2), default=0)
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    quotes = db.relationship('Quote', backref='pricing_rule', lazy=True)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'name': self.name,
            'rate_per_cubic_foot': float(self.rate_per_cubic_foot) if self.rate_per_cubic_foot else None,
            'labor_rate_per_hour': float(self.labor_rate_per_hour) if self.labor_rate_per_hour else None,
            'minimum_charge': float(self.minimum_charge) if self.minimum_charge else None,
            'distance_rate_per_mile': float(self.distance_rate_per_mile) if self.distance_rate_per_mile else None,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Quote(db.Model):
    __tablename__ = 'quotes'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    customer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))
    quote_number = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, approved, rejected, expired
    customer_email = db.Column(db.String(255), nullable=False)
    customer_phone = db.Column(db.String(20))
    customer_name = db.Column(db.String(255))
    pickup_address = db.Column(db.Text)
    delivery_address = db.Column(db.Text)
    move_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    total_cubic_feet = db.Column(db.Numeric(10, 2), default=0)
    total_labor_hours = db.Column(db.Numeric(6, 2), default=0)
    distance_miles = db.Column(db.Numeric(8, 2), default=0)
    subtotal = db.Column(db.Numeric(10, 2), default=0)
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(10, 2), default=0)
    pricing_rule_id = db.Column(UUID(as_uuid=True), db.ForeignKey('pricing_rules.id'))
    expires_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    quote_items = db.relationship('QuoteItem', backref='quote', lazy=True, cascade='all, delete-orphan')
    quote_media = db.relationship('QuoteMedia', backref='quote', lazy=True, cascade='all, delete-orphan')
    detection_jobs = db.relationship('DetectionJob', backref='quote', lazy=True)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'customer_id': str(self.customer_id) if self.customer_id else None,
            'quote_number': self.quote_number,
            'status': self.status,
            'customer_email': self.customer_email,
            'customer_phone': self.customer_phone,
            'customer_name': self.customer_name,
            'pickup_address': self.pickup_address,
            'delivery_address': self.delivery_address,
            'move_date': self.move_date.isoformat() if self.move_date else None,
            'notes': self.notes,
            'total_cubic_feet': float(self.total_cubic_feet) if self.total_cubic_feet else None,
            'total_labor_hours': float(self.total_labor_hours) if self.total_labor_hours else None,
            'distance_miles': float(self.distance_miles) if self.distance_miles else None,
            'subtotal': float(self.subtotal) if self.subtotal else None,
            'tax_amount': float(self.tax_amount) if self.tax_amount else None,
            'total_amount': float(self.total_amount) if self.total_amount else None,
            'pricing_rule_id': str(self.pricing_rule_id) if self.pricing_rule_id else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class QuoteItem(db.Model):
    __tablename__ = 'quote_items'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_id = db.Column(UUID(as_uuid=True), db.ForeignKey('quotes.id', ondelete='CASCADE'), nullable=False)
    item_catalog_id = db.Column(UUID(as_uuid=True), db.ForeignKey('item_catalog.id'))
    detected_name = db.Column(db.String(255))
    quantity = db.Column(db.Integer, default=1)
    cubic_feet = db.Column(db.Numeric(8, 2))
    labor_hours = db.Column(db.Numeric(6, 2))
    unit_price = db.Column(db.Numeric(8, 2))
    total_price = db.Column(db.Numeric(8, 2))
    confidence_score = db.Column(db.Numeric(4, 3))
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'quote_id': str(self.quote_id),
            'item_catalog_id': str(self.item_catalog_id) if self.item_catalog_id else None,
            'detected_name': self.detected_name,
            'quantity': self.quantity,
            'cubic_feet': float(self.cubic_feet) if self.cubic_feet else None,
            'labor_hours': float(self.labor_hours) if self.labor_hours else None,
            'unit_price': float(self.unit_price) if self.unit_price else None,
            'total_price': float(self.total_price) if self.total_price else None,
            'confidence_score': float(self.confidence_score) if self.confidence_score else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class QuoteMedia(db.Model):
    __tablename__ = 'quote_media'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_id = db.Column(UUID(as_uuid=True), db.ForeignKey('quotes.id', ondelete='CASCADE'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.Text, nullable=False)
    file_size = db.Column(db.BigInteger)
    mime_type = db.Column(db.String(100))
    is_processed = db.Column(db.Boolean, default=False)
    yoloe_results = db.Column(JSONB)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'quote_id': str(self.quote_id),
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'is_processed': self.is_processed,
            'yoloe_results': self.yoloe_results,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class DetectionJob(db.Model):
    __tablename__ = 'detection_jobs'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    quote_id = db.Column(UUID(as_uuid=True), db.ForeignKey('quotes.id'))
    media_ids = db.Column(ARRAY(UUID(as_uuid=True)))
    job_type = db.Column(db.String(50), nullable=False)  # 'auto' or 'text'
    prompt = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    runpod_job_id = db.Column(db.String(255))
    results = db.Column(JSONB)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    completed_at = db.Column(db.DateTime(timezone=True))
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'quote_id': str(self.quote_id) if self.quote_id else None,
            'media_ids': [str(mid) for mid in self.media_ids] if self.media_ids else [],
            'job_type': self.job_type,
            'prompt': self.prompt,
            'status': self.status,
            'runpod_job_id': self.runpod_job_id,
            'results': self.results,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class RateLimit(db.Model):
    __tablename__ = 'rate_limits'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = db.Column(UUID(as_uuid=True), db.ForeignKey('tenants.id'))
    ip_address = db.Column(INET)
    endpoint = db.Column(db.String(255), nullable=False)
    request_count = db.Column(db.Integer, default=1)
    window_start = db.Column(db.DateTime(timezone=True), server_default=func.now())
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (db.UniqueConstraint('tenant_id', 'ip_address', 'endpoint', 'window_start'),)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id) if self.tenant_id else None,
            'ip_address': str(self.ip_address) if self.ip_address else None,
            'endpoint': self.endpoint,
            'request_count': self.request_count,
            'window_start': self.window_start.isoformat() if self.window_start else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

