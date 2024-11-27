import re
from typing import Dict, List, Optional, Union
from models import PowerBIModel, Query
from utils.database import db
from flask import current_app
import json

class QueryProcessor:
    def __init__(self, model_data: Dict):
        self.model_data = model_data
        self.tables = {table['name'].lower(): table for table in model_data.get('tables', [])}
        self.relationships = model_data.get('relationships', [])

    def extract_entities(self, query_text: str) -> Dict:
        """Extract relevant entities from the query text."""
        query_text = query_text.lower()
        
        # Define patterns for different query types
        patterns = {
            'show_table': r'show|display|list|get\s+(?:all\s+)?(?:data\s+from\s+)?(\w+)',
            'column_query': r'(?:show|display|list|get)\s+(\w+)\s+(?:from|in)\s+(\w+)',
            'aggregate': r'(?:total|sum|average|count)\s+(?:of\s+)?(\w+)\s+(?:from|in)\s+(\w+)',
            'filter': r'(?:where|with)\s+(\w+)\s*(=|>|<|>=|<=)\s*(\w+)',
        }
        
        entities = {
            'intent': None,
            'table': None,
            'column': None,
            'aggregate': None,
            'filter': None
        }
        
        # Check for table queries
        for intent, pattern in patterns.items():
            matches = re.search(pattern, query_text)
            if matches:
                if intent == 'show_table':
                    entities['intent'] = 'show_table'
                    entities['table'] = matches.group(1)
                elif intent == 'column_query':
                    entities['intent'] = 'column_query'
                    entities['column'] = matches.group(1)
                    entities['table'] = matches.group(2)
                elif intent == 'aggregate':
                    entities['intent'] = 'aggregate'
                    entities['column'] = matches.group(1)
                    entities['table'] = matches.group(2)
                    entities['aggregate'] = matches.group(0).split()[0]
                elif intent == 'filter':
                    entities['filter'] = {
                        'column': matches.group(1),
                        'operator': matches.group(2),
                        'value': matches.group(3)
                    }
        
        return entities

    def validate_query(self, entities: Dict) -> Optional[str]:
        """Validate extracted entities against the model structure."""
        if not entities['intent']:
            return "Could not understand the query intent. Please rephrase your question."
        
        if entities['table'] and entities['table'] not in self.tables:
            return f"Table '{entities['table']}' not found in the model."
        
        if entities['column']:
            table = self.tables.get(entities['table'], {})
            if entities['column'] not in [col.lower() for col in table.get('columns', [])]:
                return f"Column '{entities['column']}' not found in table '{entities['table']}'."
        
        return None

    def generate_response(self, entities: Dict) -> Dict:
        """Generate a response based on the validated entities."""
        # Mock data generation (in real implementation, this would query the actual Power BI model)
        if entities['intent'] == 'show_table':
            table = self.tables[entities['table']]
            return {
                'type': 'data',
                'result': {
                    'values': range(len(table['columns'])),
                    'labels': table['columns'],
                    'chart_type': 'table'
                },
                'explanation': f"Showing columns from table '{entities['table']}'"
            }
        elif entities['intent'] in ['column_query', 'aggregate']:
            return {
                'type': 'data',
                'result': {
                    'values': [10, 20, 30, 40, 50],  # Mock values
                    'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
                    'chart_type': 'bar' if entities['aggregate'] else 'line'
                },
                'explanation': f"Showing {entities['aggregate'] or ''} {entities['column']} from {entities['table']}"
            }

def process_query(query_text: str) -> Dict:
    """
    Process natural language query against the Power BI model structure
    """
    try:
        # In a real implementation, this would retrieve the current model from the database
        # For now, we'll use a simple mock model structure
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
            ]
        }
        
        processor = QueryProcessor(model_data)
        entities = processor.extract_entities(query_text)
        
        # Validate the query
        error = processor.validate_query(entities)
        if error:
            return {
                'type': 'error',
                'explanation': error
            }
        
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
            'explanation': f"Error processing query: {str(e)}"
        }
