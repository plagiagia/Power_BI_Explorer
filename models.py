from datetime import datetime
from utils.database import db
from pgvector.sqlalchemy import Vector

class PowerBIModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    embeddings = db.relationship('FileEmbedding', backref='model', lazy=True)
    
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

class FileEmbedding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('power_bi_model.id'))
    content_chunk = db.Column(db.Text)
    embedding = db.Column(Vector(1536))  # OpenAI embedding dimension
    created_at = db.Column(db.DateTime, default=datetime.utcnow)