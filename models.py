from datetime import datetime
from utils.database import db

class PowerBIModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PowerBIModel {self.name}>'

class Query(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(512), nullable=False)
    result = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    model_id = db.Column(db.Integer, db.ForeignKey('power_bi_model.id'))
    
    def __repr__(self):
        return f'<Query {self.text}>'
