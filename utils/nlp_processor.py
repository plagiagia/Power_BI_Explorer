import re
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
from models import PowerBIModel, Query
from utils.database import db
from flask import current_app
import json

class QueryProcessor:
    def __init__(self, model_data: Dict):
        self.model_data = model_data
        self.tables = {table['name'].lower(): table for table in model_data.get('tables', [])}
        self.relationships = model_data.get('relationships', [])
        self.measures = model_data.get('measures', [])
        
        # Define supported operations
        self.time_patterns = {
            'yoy': r'year[\s-]over[\s-]year|yoy',
            'mom': r'month[\s-]over[\s-]month|mom',
            'previous_period': r'previous|last|prior\s+(?:period|month|year)',
            'date_range': r'(?:from|between)\s+(\d{4}-\d{2}-\d{2})\s+(?:to|and)\s+(\d{4}-\d{2}-\d{2})'
        }
        
        self.aggregations = {
            'sum': 'SUM',
            'average': 'AVERAGE',
            'count': 'COUNT',
            'min': 'MIN',
            'max': 'MAX'
        }
        
        # Chart type suggestions based on query context
        self.chart_suggestions = {
            'time_series': 'line',
            'comparison': 'bar',
            'distribution': 'histogram',
            'correlation': 'scatter',
            'composition': 'pie',
            'hierarchy': 'treemap'
        }

    def extract_entities(self, query_text: str) -> Dict:
        """Extract relevant entities from the query text with enhanced pattern recognition."""
        query_text = query_text.lower()
        
        entities = {
            'intent': None,
            'tables': [],
            'columns': [],
            'metrics': [],
            'time_analysis': None,
            'grouping': [],
            'filters': [],
            'visualization': None
        }
        
        # Extract time-based analysis patterns
        for time_type, pattern in self.time_patterns.items():
            if re.search(pattern, query_text):
                entities['time_analysis'] = time_type
                break
        
        # Extract multiple metrics
        metric_pattern = r'(?:show|display|calculate)\s+(?:the\s+)?([a-zA-Z\s,]+)\s+(?:for|from|of)'
        metrics_match = re.search(metric_pattern, query_text)
        if metrics_match:
            metrics = metrics_match.group(1).split(',')
            entities['metrics'] = [m.strip() for m in metrics]
        
        # Extract grouping
        group_pattern = r'group\s+by\s+([a-zA-Z\s,]+)'
        group_match = re.search(group_pattern, query_text)
        if group_match:
            entities['grouping'] = [g.strip() for g in group_match.group(1).split(',')]
        
        # Extract visualization preferences
        viz_pattern = r'(?:show|display|visualize)\s+(?:as|in|using)\s+(?:a\s+)?([a-zA-Z\s]+)(?:\s+chart|\s+graph)?'
        viz_match = re.search(viz_pattern, query_text)
        if viz_match:
            entities['visualization'] = viz_match.group(1).strip()
        
        return entities

    def validate_query(self, entities: Dict) -> Optional[str]:
        """Enhanced query validation with detailed error messages and suggestions."""
        errors = []
        suggestions = []
        
        # Validate metrics
        for metric in entities['metrics']:
            if metric not in self.measures and not any(
                metric in table['columns'] for table in self.tables.values()
            ):
                errors.append(f"Metric '{metric}' not found")
                similar_metrics = self._find_similar_names(metric, self.measures)
                if similar_metrics:
                    suggestions.append(f"Did you mean: {', '.join(similar_metrics)}?")
        
        # Validate time analysis
        if entities['time_analysis']:
            date_columns = self._find_date_columns()
            if not date_columns:
                errors.append("No date columns found for time-based analysis")
                suggestions.append("Please ensure your model contains date columns")
        
        # Validate grouping
        for group in entities['grouping']:
            if not any(group in table['columns'] for table in self.tables.values()):
                errors.append(f"Grouping column '{group}' not found")
                similar_columns = self._find_similar_names(group, 
                    [col for table in self.tables.values() for col in table['columns']]
                )
                if similar_columns:
                    suggestions.append(f"Did you mean: {', '.join(similar_columns)}?")
        
        if errors:
            return {
                'errors': errors,
                'suggestions': suggestions
            }
        return None

    def _find_similar_names(self, name: str, options: List[str], threshold: float = 0.6) -> List[str]:
        """Find similar names using string similarity."""
        from difflib import SequenceMatcher
        
        similar = []
        for option in options:
            similarity = SequenceMatcher(None, name.lower(), option.lower()).ratio()
            if similarity >= threshold:
                similar.append(option)
        return similar[:3]  # Return top 3 suggestions

    def _find_date_columns(self) -> List[str]:
        """Find date columns in the model."""
        date_columns = []
        date_patterns = [r'date', r'time', r'year', r'month']
        
        for table in self.tables.values():
            for column in table['columns']:
                if any(re.search(pattern, column.lower()) for pattern in date_patterns):
                    date_columns.append(f"{table['name']}.{column}")
        return date_columns

    def _suggest_visualization(self, entities: Dict) -> str:
        """Suggest appropriate visualization based on query context."""
        if entities['time_analysis']:
            return 'line'
        elif len(entities['metrics']) > 1:
            return 'bar'
        elif entities['grouping']:
            return 'pie' if len(entities['grouping']) == 1 else 'treemap'
        return 'bar'  # Default visualization

    def generate_response(self, entities: Dict) -> Dict:
        """Generate enhanced response with DAX expressions and appropriate visualizations."""
        try:
            # Generate DAX expression
            dax_expression = self._generate_dax_expression(entities)
            
            # Mock data generation (in real implementation, this would execute the DAX query)
            data = self._execute_dax_query(dax_expression)
            
            # Determine visualization type
            viz_type = entities['visualization'] or self._suggest_visualization(entities)
            
            return {
                'type': 'data',
                'result': {
                    'values': data['values'],
                    'labels': data['labels'],
                    'chart_type': viz_type
                },
                'explanation': self._generate_explanation(entities, dax_expression),
                'dax_query': dax_expression
            }
            
        except Exception as e:
            return {
                'type': 'error',
                'explanation': str(e),
                'suggestions': self._generate_error_suggestions(str(e))
            }

    def _generate_dax_expression(self, entities: Dict) -> str:
        """Generate DAX expression based on query entities."""
        # This is a simplified version - in real implementation, this would generate actual DAX
        parts = []
        
        # Add EVALUATE
        parts.append("EVALUATE")
        
        # Add time intelligence if needed
        if entities['time_analysis']:
            if entities['time_analysis'] == 'yoy':
                parts.append("CALCULATETABLE(")
        
        # Add measures and columns
        metrics = ', '.join(entities['metrics']) if entities['metrics'] else '*'
        parts.append(f"SUMMARIZE({self.tables[0]['name']}, {metrics})")
        
        return ' '.join(parts)

    def _execute_dax_query(self, dax_expression: str) -> Dict:
        """Execute DAX query (mock implementation)."""
        # In real implementation, this would connect to Power BI and execute the query
        return {
            'values': [10, 20, 30, 40, 50],
            'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May']
        }

    def _generate_explanation(self, entities: Dict, dax_query: str) -> str:
        """Generate human-readable explanation of the query and results."""
        parts = []
        if entities['metrics']:
            parts.append(f"Showing {', '.join(entities['metrics'])}")
        if entities['time_analysis']:
            parts.append(f"with {entities['time_analysis']} analysis")
        if entities['grouping']:
            parts.append(f"grouped by {', '.join(entities['grouping'])}")
        return ' '.join(parts)

    def _generate_error_suggestions(self, error_message: str) -> List[str]:
        """Generate helpful suggestions based on error message."""
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
        
        processor = QueryProcessor(model_data)
        entities = processor.extract_entities(query_text)
        
        # Validate the query
        validation_result = processor.validate_query(entities)
        if validation_result:
            return {
                'type': 'error',
                'explanation': validation_result['errors'],
                'suggestions': validation_result['suggestions']
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
            'explanation': f"Error processing query: {str(e)}",
            'suggestions': [
                "Try simplifying your query",
                "Make sure all column and measure names are correct",
                "Check the query syntax and try again"
            ]
        }
