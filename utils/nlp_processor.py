import re
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
from models import PowerBIModel, Query
from utils.database import db
from flask import current_app
import json
import os

class QueryProcessor:
    def __init__(self, model_data: Dict):
        self.model_data = model_data
        self.tables = {table['name'].lower(): table for table in model_data.get('tables', [])}
        self.relationships = model_data.get('relationships', [])
        self.measures = model_data.get('measures', [])

    def _format_model_structure(self) -> str:
        """Format model structure for prompt template"""
        structure = []
        structure.append("Tables:")
        for table in self.model_data.get('tables', []):
            structure.append(f"- {table['name']}")
            structure.append("  Columns: " + ", ".join(table['columns']))
        
        structure.append("\nMeasures:")
        for measure in self.measures:
            structure.append(f"- {measure}")
            
        return "\n".join(structure)

    def analyze_query(self, query_text: str) -> Dict:
        """Analyze query and extract key information"""
        try:
            # Simple query analysis for initial prototype
            entities = {
                'intent': 'data_analysis',
                'metrics': [],
                'time_analysis': None,
                'grouping': [],
                'filters': [],
                'visualization': 'bar'
            }
            
            # Extract metrics
            if 'sales' in query_text.lower():
                entities['metrics'].append('total_sales')
            if 'average' in query_text.lower() and 'price' in query_text.lower():
                entities['metrics'].append('average_price')
            if 'customer' in query_text.lower():
                entities['metrics'].append('customer_count')
                
            # Detect time analysis
            if any(term in query_text.lower() for term in ['year', 'month', 'daily']):
                entities['time_analysis'] = 'trend'
                
            # Detect grouping
            if 'category' in query_text.lower():
                entities['grouping'].append('category')
            if 'product' in query_text.lower():
                entities['grouping'].append('product')
                
            # Determine visualization
            if 'trend' in query_text.lower() or entities['time_analysis']:
                entities['visualization'] = 'line'
            elif len(entities['metrics']) > 1:
                entities['visualization'] = 'bar'
                
            return entities
            
        except Exception as e:
            raise Exception(f"Error analyzing query: {str(e)}")

    def generate_response(self, entities: Dict) -> Dict:
        """Generate response based on analyzed entities"""
        try:
            # Mock data generation (in real implementation, this would execute a DAX query)
            data = {
                'values': [10, 20, 30, 40, 50],
                'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May']
            }
            
            # Determine visualization type
            viz_type = entities.get('visualization', 'bar')
            
            return {
                'type': 'data',
                'result': {
                    'values': data['values'],
                    'labels': data['labels'],
                    'chart_type': viz_type
                },
                'explanation': self._generate_explanation(entities),
                'intent': entities.get('intent', '')
            }
            
        except Exception as e:
            return {
                'type': 'error',
                'explanation': str(e),
                'suggestions': self._generate_error_suggestions(str(e))
            }

    def _generate_explanation(self, entities: Dict) -> str:
        """Generate human-readable explanation of the query and results"""
        parts = []
        if entities.get('metrics'):
            parts.append(f"Showing {', '.join(entities['metrics'])}")
        if entities.get('time_analysis'):
            parts.append(f"with {entities['time_analysis']} analysis")
        if entities.get('grouping'):
            parts.append(f"grouped by {', '.join(entities['grouping'])}")
        return ' '.join(parts)

    def _generate_error_suggestions(self, error_message: str) -> List[str]:
        """Generate helpful suggestions based on error message"""
        suggestions = []
        if 'column not found' in error_message.lower():
            suggestions.append("Check column names and ensure they exist in the model")
        if 'measure' in error_message.lower():
            suggestions.append("Verify measure names and syntax")
        if 'relationship' in error_message.lower():
            suggestions.append("Ensure tables are properly related in the model")
        return suggestions

def process_query(query_text: str) -> Dict:
    """Process natural language query against the Power BI model structure"""
    try:
        # In a real implementation, this would retrieve the current model from the database
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
        
        # Create query processor
        processor = QueryProcessor(model_data)
        
        # Analyze query
        entities = processor.analyze_query(query_text)
        
        # Generate response
        response = processor.generate_response(entities)
        
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