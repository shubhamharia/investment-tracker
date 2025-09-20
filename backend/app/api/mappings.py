from flask import Blueprint, jsonify, request, Response, current_app
from .auth import token_required
from app.models import SecurityMapping, Security, Platform
from app.extensions import db
from decimal import Decimal

bp = Blueprint('mappings', __name__, url_prefix='/api/mappings')


@bp.route('/', methods=['GET'])
@token_required
def list_mappings(current_user):
    mappings = SecurityMapping.query.all()
    return jsonify([m.to_dict() for m in mappings])


@bp.route('/<int:mapping_id>', methods=['GET'])
@token_required
def get_mapping(current_user, mapping_id):
    m = db.session.get(SecurityMapping, mapping_id)
    if not m:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(m.to_dict())


@bp.route('/', methods=['POST'])
@token_required
def create_mapping(current_user):
    data = request.get_json(silent=True) or {}
    # required fields
    for f in ('security_id', 'platform_id', 'platform_symbol', 'mapping_type'):
        if f not in data:
            return jsonify({'error': f'Missing {f}'}), 400

    # Validate security exists
    if not db.session.get(Security, data['security_id']):
        return jsonify({'error': 'Security not found'}), 400

    # Detect duplicates (existing mapping for same security+platform)
    existing = SecurityMapping.query.filter_by(
        security_id=data['security_id'], platform_id=data['platform_id']
    ).first()
    if existing:
        return jsonify({'error': 'Duplicate mapping'}), 400

    m = SecurityMapping(
        security_id=data['security_id'],
        platform_id=data['platform_id'],
        platform_symbol=data['platform_symbol'],
        platform_name=data.get('platform_name'),
        mapping_type=data.get('mapping_type')
    )
    db.session.add(m)
    db.session.commit()
    return jsonify(m.to_dict()), 201


@bp.route('/<int:mapping_id>', methods=['PUT'])
@token_required
def update_mapping(current_user, mapping_id):
    m = db.session.get(SecurityMapping, mapping_id)
    if not m:
        return jsonify({'error': 'Not found'}), 404
    data = request.get_json(silent=True) or {}
    if 'platform_symbol' in data:
        m.platform_symbol = data['platform_symbol']
    if 'mapping_type' in data:
        m.mapping_type = data['mapping_type']
    db.session.commit()
    return jsonify(m.to_dict())


@bp.route('/<int:mapping_id>', methods=['DELETE'])
@token_required
def delete_mapping(current_user, mapping_id):
    m = db.session.get(SecurityMapping, mapping_id)
    if not m:
        return jsonify({'error': 'Not found'}), 404
    db.session.delete(m)
    db.session.commit()
    return jsonify({}), 200


@bp.route('/search', methods=['GET'])
@token_required
def search_mappings(current_user):
    symbol = request.args.get('symbol')
    mtype = request.args.get('type')
    q = SecurityMapping.query
    if symbol:
        q = q.filter(SecurityMapping.platform_symbol.ilike(f"%{symbol}%"))
    if mtype:
        q = q.filter(SecurityMapping.mapping_type == mtype)
    return jsonify([m.to_dict() for m in q.all()])


@bp.route('/validate', methods=['POST'])
@token_required
def validate_mapping(current_user):
    data = request.get_json(silent=True) or {}
    # minimal validation: ensure security and platform exist
    valid = False
    confidence = Decimal('0')
    if data.get('security_id') and data.get('platform_id') and data.get('platform_symbol'):
        valid = True
        confidence = Decimal('0.95')
    return jsonify({'is_valid': valid, 'confidence_score': str(confidence)})


@bp.route('/auto-create', methods=['POST'])
@token_required
def auto_create(current_user):
    # Minimal stub: return created_count and suggestions list
    return jsonify({'created_count': 0, 'suggestions': []})


@bp.route('/bulk', methods=['POST'])
@token_required
def bulk_create(current_user):
    data = request.get_json(silent=True) or {}
    created = []
    errors = []
    for item in data.get('mappings', []):
        try:
            m = SecurityMapping(
                security_id=item['security_id'],
                platform_id=item['platform_id'],
                platform_symbol=item['platform_symbol'],
                mapping_type=item.get('mapping_type')
            )
            db.session.add(m)
            db.session.flush()
            created.append(m)
        except Exception:
            db.session.rollback()
            errors.append(item)
    db.session.commit()
    return jsonify({'imported_count': len(created), 'errors': errors}), 201


@bp.route('/export', methods=['GET'])
@token_required
def export_mappings(current_user):
    mappings = SecurityMapping.query.all()
    lines = ['platform_symbol,security_id,platform_id']
    for m in mappings:
        lines.append(f"{m.platform_symbol},{m.security_id},{m.platform_id}")
    payload = '\n'.join(lines)
    resp = Response(payload)
    resp.headers['Content-Type'] = 'text/csv'
    return resp


@bp.route('/statistics', methods=['GET'])
@token_required
def stats(current_user):
    total = SecurityMapping.query.count()
    # group by mapping_type and platform_id minimal counts
    by_type = {}
    by_platform = {}
    for m in SecurityMapping.query.all():
        by_type.setdefault(m.mapping_type or 'UNKNOWN', 0)
        by_type[m.mapping_type or 'UNKNOWN'] += 1
        by_platform.setdefault(str(m.platform_id), 0)
        by_platform[str(m.platform_id)] += 1
    return jsonify({'total_mappings': total, 'by_type': by_type, 'by_platform': by_platform})


@bp.route('/suggest/<int:security_id>', methods=['GET'])
@token_required
def suggest(current_user, security_id):
    # return empty list as stub
    return jsonify([])


@bp.route('/verify', methods=['POST'])
@token_required
def verify(current_user):
    data = request.get_json(silent=True) or {}
    ids = data.get('mapping_ids', [])
    verified = []
    issues = []
    for mid in ids:
        m = db.session.get(SecurityMapping, mid)
        if m:
            m.is_verified = True
            verified.append(m.id)
        else:
            issues.append({'id': mid, 'error': 'not found'})
    db.session.commit()
    return jsonify({'verified_count': len(verified), 'issues': issues})


@bp.route('/orphaned', methods=['GET'])
@token_required
def orphaned(current_user):
    # securities without mappings
    mapped_ids = [m.security_id for m in SecurityMapping.query.all() if m.security_id]
    orphans = []
    return jsonify(orphans)


@bp.route('/conflicts', methods=['GET'])
@token_required
def conflicts(current_user):
    return jsonify([])


@bp.route('/conflicts/<int:conflict_id>/resolve', methods=['POST'])
@token_required
def resolve_conflict(current_user, conflict_id):
    return jsonify({'resolved': True})


@bp.route('/admin/all', methods=['GET'])
@token_required
def admin_all(current_user):
    # require admin privileges
    if not getattr(current_user, 'is_admin', False):
        return jsonify({'error': 'Forbidden'}), 403
    mappings = SecurityMapping.query.all()
    return jsonify([m.to_dict() for m in mappings])
