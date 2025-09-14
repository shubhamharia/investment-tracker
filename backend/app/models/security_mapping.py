from sqlalchemy.orm import relationship
from . import db, BaseModel

class SecurityMapping(BaseModel):
    """Model for mapping securities to platform-specific identifiers"""
    __tablename__ = 'security_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    security_id = db.Column(db.Integer, db.ForeignKey('securities.id'), nullable=False)
    platform_identifier = db.Column(db.String(50), nullable=False)
    platform_name = db.Column(db.String(50), nullable=False)
    
    # Relationships
    security = relationship('app.models.security.Security',
                          back_populates='platform_mappings', lazy='select', uselist=False,
                          foreign_keys=[security_id])
    
    __table_args__ = (
        db.UniqueConstraint('security_id', 'platform_name', name='_security_platform_uc'),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f'<SecurityMapping {self.platform_name}:{self.platform_identifier}>'
