import os
from typing import Dict, List
from datetime import datetime
from models import PowerBIModel, Query, FileEmbedding
from utils.database import db
import json
import openai
import numpy as np

def generate_embeddings(text: str) -> List[float]:
    """Generate embeddings using OpenAI"""
    openai.api_key = os.getenv('OPENAI_API_KEY')
    response = openai.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding

def chunk_content(content: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split content into chunks with overlap"""
    words = content.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

def store_embeddings(model_id: int, content: str):
    """Store content chunks and their embeddings"""
    try:
        chunks = chunk_content(content)
        for chunk in chunks:
            embedding = generate_embeddings(chunk)
            file_embedding = FileEmbedding(
                file_id=model_id,
                content_chunk=chunk,
                embedding=embedding
            )
            db.session.add(file_embedding)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

def find_similar_chunks(query_text: str, model_id: int, limit: int = 5) -> List[str]:
    """Find similar content chunks using vector similarity"""
    query_embedding = generate_embeddings(query_text)
    
    # Using cosine similarity search
    similar_chunks = FileEmbedding.query.filter_by(file_id=model_id)\
        .order_by(FileEmbedding.embedding.cosine_distance(query_embedding))\
        .limit(limit)\
        .all()
    
    return [chunk.content_chunk for chunk in similar_chunks]

def process_query(query_text: str) -> Dict:
    """Process natural language query against the Power BI model structure"""
    try:
        # Get the latest PowerBI model
        latest_model = PowerBIModel.query.order_by(PowerBIModel.created_at.desc()).first()
        if not latest_model:
            return {
                'type': 'error',
                'explanation': "No Power BI model found. Please upload a file first.",
                'suggestions': ["Upload a Power BI model file (.bim or .json)"]
            }

        # Find relevant content chunks
        similar_chunks = find_similar_chunks(query_text, latest_model.id)
        
        # For the initial prototype, return mock data with proper structure
        response = {
            'type': 'data',
            'result': {
                'values': [120, 150, 180, 210, 240],
                'labels': ['Q1', 'Q2', 'Q3', 'Q4', 'Q5'],
                'chart_type': 'bar'
            },
            'explanation': f"Showing quarterly data trend for {query_text}",
            'context': similar_chunks
        }
        
        # Store query in database
        query = Query(
            text=query_text,
            result=json.dumps(response),
            model_id=latest_model.id
        )
        db.session.add(query)
        db.session.commit()
        
        return response
        
    except Exception as e:
        return {
            'type': 'error',
            'explanation': f"Error processing query: {str(e)}",
            'suggestions': [
                "Try simplifying your query",
                "Make sure all column and measure names are correct",
                "Check the query syntax and try again"
            ]
        }
