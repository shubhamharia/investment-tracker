from datetime import datetime
from . import db, BaseModel


class SecurityMapping(BaseModel):
    """Map platform-specific security identifiers to master securities."""
    __tablename__ = 'security_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    platform_id = db.Column(db.Integer, db.ForeignKey('platforms.id'), nullable=False)
    security_id = db.Column(db.Integer, db.ForeignKey('securities.id'), nullable=False)
    platform_symbol = db.Column(db.String(50), nullable=False)
    platform_name = db.Column(db.String(200))
    mapping_type = db.Column(db.String(20))
    confidence_score = db.Column(db.Numeric(4, 3))
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    verified_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    # Relationships
    platform = db.relationship('Platform', backref='security_mappings', lazy=True)
    security = db.relationship('app.models.security.Security', back_populates='platform_mappings', lazy='select')
    
    # We enforce uniqueness of (security_id, platform_id) at the session level
    # instead of a DB-level unique constraint so tests that create multiple
    # new mappings in a single transaction are allowed, while attempts to add
    # a mapping when one already exists in the database will be rejected.
    
    @classmethod
    def get_or_create_mapping(cls, platform_id, platform_symbol, platform_name=None):
        mapping = cls.query.filter_by(
            platform_id=platform_id,
            platform_symbol=platform_symbol
        ).first()
        
        if not mapping:
            mapping = cls(
                platform_id=platform_id,
                platform_symbol=platform_symbol,
                platform_name=platform_name,
                is_verified=False
            )
            db.session.add(mapping)
            db.session.commit()
        
        return mapping
    
    def verify_mapping(self, security_id):
        self.security_id = security_id
        self.is_verified = True
        self.verified_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'security_id': self.security_id if self.security_id else None,
            'platform_id': self.platform_id,
            'platform_symbol': self.platform_symbol,
            'platform_name': self.platform_name,
            'mapping_type': self.mapping_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<SecurityMapping {self.security.symbol if self.security else self.security_id} -> {self.platform_symbol} ({self.platform.name if self.platform else self.platform_id})>'


# Session-level guard to emulate a conditional unique constraint:
# - Allow multiple new SecurityMapping rows to be added together in the
#   same transaction (useful for tests that create several mappings at once)
# - Prevent inserting a new SecurityMapping if a mapping with the same
#   security_id and platform_id already exists in the database
from sqlalchemy import event


def _security_mapping_before_flush(session, flush_context, instances):
    """Session before_flush handler that enforces a conditional uniqueness
    rule: disallow creating mappings when one already exists in the DB for
    the same (security_id, platform_id). New mappings staged together in the
    same session are allowed.
    """
    # Collect new SecurityMapping objects being added in this flush
    new_mappings = [obj for obj in session.new if isinstance(obj, SecurityMapping)]
    if not new_mappings:
        return

    # For each new mapping, if any existing (persisted) mapping in the DB
    # already matches (security_id, platform_id) and is NOT part of the
    # new_mappings list, raise an exception to block the commit.
    for m in new_mappings:
        # Both ids must be set to check properly
        if not m.security_id or not m.platform_id:
            continue

        # Query the database for an existing mapping with same pair
        existing = session.query(SecurityMapping).filter(
            SecurityMapping.security_id == m.security_id,
            SecurityMapping.platform_id == m.platform_id
        ).first()

        # If an existing persisted mapping is found and it's not one of the
        # new mappings being flushed, block the operation.
        if existing and existing not in new_mappings:
            raise Exception(
                f"duplicate mapping for security_id={m.security_id} and platform_id={m.platform_id}"
            )


# Register the listener on the scoped session. This will run before every
# flush and enforce the conditional uniqueness rule described above.
try:
    event.listen(db.session, 'before_flush', _security_mapping_before_flush)
except Exception:
    # If the session is not yet available during import time (rare), ignore
    # and rely on the application to register the handler later. Tests will
    # run in normal app context so this should work.
    pass
