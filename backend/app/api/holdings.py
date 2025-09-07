from flask import Blueprint, jsonify, request
from app.models import Holding
from app.extensions import db

bp = Blueprint('holdings', __name__, url_prefix='/api/holdings')

@bp.route('/', methods=['GET'])
def get_holdings():
    holdings = Holding.query.all()
    return jsonify([holding.to_dict() for holding in holdings])

@bp.route('/<int:id>', methods=['GET'])
def get_holding(id):
    holding = Holding.query.get_or_404(id)
    return jsonify(holding.to_dict())

@bp.route('/', methods=['POST'])
def create_holding():
    data = request.get_json()
    new_holding = Holding(**data)
    db.session.add(new_holding)
    db.session.commit()
    return jsonify(new_holding.to_dict()), 201

@bp.route('/<int:id>', methods=['PUT'])
def update_holding(id):
    holding = Holding.query.get_or_404(id)
    data = request.get_json()
    for key, value in data.items():
        setattr(holding, key, value)
    db.session.commit()
    return jsonify(holding.to_dict())

@bp.route('/<int:id>', methods=['DELETE'])
def delete_holding(id):
    holding = Holding.query.get_or_404(id)
    db.session.delete(holding)
    db.session.commit()
    return '', 204