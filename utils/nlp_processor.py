from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel
from models import PowerBIModel, Query
from utils.database import db
import json
import os

class QueryResult(BaseModel):
    type: str = "data"
    result: Optional[Dict] = None
    explanation: str
    suggestions: Optional[List[str]] = None

def process_query(query_text: str) -> Dict:
    """Process natural language query against the Power BI model structure"""
    try:
        # Get the latest PowerBI model
        latest_model = PowerBIModel.query.order_by(PowerBIModel.created_at.desc()).first()
        if not latest_model:
            raise ValueError("No Power BI model found. Please upload a file first.")

        model_data = json.loads(latest_model.content)
        
        # For the initial prototype, return mock data with proper structure
        response = {
            'type': 'data',
            'result': {
                'values': [120, 150, 180, 210, 240],
                'labels': ['Q1', 'Q2', 'Q3', 'Q4', 'Q5'],
                'chart_type': 'bar'
            },
            'explanation': f"Showing quarterly data trend for {query_text}"
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
        error_response = {
            'type': 'error',
            'explanation': f"Error processing query: {str(e)}",
            'suggestions': [
                "Try simplifying your query",
                "Make sure all column and measure names are correct",
                "Check the query syntax and try again"
            ]
        }
        return error_response