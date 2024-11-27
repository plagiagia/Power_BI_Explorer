from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
from models import PowerBIModel, Query
from utils.database import db
from flask import current_app
import json
import os
from langchain_openai import OpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

class QueryProcessor:
    def __init__(self, model_data: Dict):
        self.model_data = model_data
        self.llm = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            temperature=0.7
        )
        
        # Create prompt template with Power BI context
        self.template = """You are a Power BI query assistant. Using the following model structure:
            
Tables: {tables}
Relationships: {relationships}
Measures: {measures}
            
Please analyze this query: {query}
            
Return a JSON response with:
1. Type of visualization recommended
2. Data to display (mock data for now)
3. Natural language explanation
            
Keep the response concise and focused on the data analysis."""
        
        self.prompt = PromptTemplate(
            template=self.template,
            input_variables=["tables", "relationships", "measures", "query"]
        )
        
        self.output_parser = StrOutputParser()
    
    def _format_model_info(self) -> Dict[str, str]:
        """Format model structure for prompt"""
        tables = "\n".join([
            f"- {table['name']}: {', '.join(table['columns'])}"
            for table in self.model_data.get('tables', [])
        ])
        
        relationships = "\n".join([
            f"- {rel['fromTable']}.{rel['fromColumn']} -> {rel['toTable']}.{rel['toColumn']}"
            for rel in self.model_data.get('relationships', [])
        ])
        
        measures = ", ".join(self.model_data.get('measures', []))
        
        return {
            "tables": tables,
            "relationships": relationships,
            "measures": measures
        }
    
    def process_query(self, query_text: str) -> Dict:
        """Process natural language query"""
        try:
            # For the initial prototype, we'll use mock data
            mock_response = {
                'type': 'data',
                'result': {
                    'values': [120, 150, 180, 210, 240],
                    'labels': ['Q1', 'Q2', 'Q3', 'Q4', 'Q5'],
                    'chart_type': 'bar'
                },
                'explanation': 'Showing quarterly sales trend with mock data.',
                'intent': 'trend_analysis'
            }
            
            return mock_response
            
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

def process_query(query_text: str) -> Dict:
    """Process natural language query against the Power BI model structure"""
    try:
        # Mock model data for initial prototype
        model_data = {
            'tables': [
                {
                    'name': 'sales',
                    'columns': ['date', 'amount', 'product', 'customer']
                },
                {
                    'name': 'products',
                    'columns': ['id', 'name', 'category', 'price']
                }
            ],
            'relationships': [
                {
                    'fromTable': 'sales',
                    'fromColumn': 'product',
                    'toTable': 'products',
                    'toColumn': 'id'
                }
            ],
            'measures': [
                'total_sales',
                'average_price',
                'customer_count'
            ]
        }
        
        processor = QueryProcessor(model_data)
        response = processor.process_query(query_text)
        
        # Store query in database
        query = Query(text=query_text, result=json.dumps(response))
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
