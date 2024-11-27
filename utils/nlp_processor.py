from typing import Dict, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, model_validator
from models import PowerBIModel, Query
from utils.database import db
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import json
import os

class QueryResult(BaseModel):
    type: str = Field(default="data")
    result: Optional[Dict] = None
    explanation: str
    suggestions: Optional[List[str]] = None

    @model_validator(mode='before')
    @classmethod
    def validate_result_type(cls, data):
        if data.get('type') == 'data' and not data.get('result'):
            raise ValueError("Result field is required when type is 'data'")
        return data

class PowerBIModelStructure(BaseModel):
    tables: List[Dict[str, Union[str, List[str]]]]
    relationships: List[Dict[str, str]]
    measures: List[str]

class QueryProcessor:
    def __init__(self, model_data: Dict):
        """Initialize the query processor with model data"""
        try:
            self.model_structure = PowerBIModelStructure(
                tables=model_data.get('tables', []),
                relationships=model_data.get('relationships', []),
                measures=model_data.get('measures', [])
            )
            
            self.llm = ChatOpenAI(
                temperature=0.7,
                model="gpt-3.5-turbo"
            )
            
            self.output_parser = JsonOutputParser(pydantic_object=QueryResult)
            
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a Power BI query assistant. Analyze queries and provide visualization recommendations.
                Model Structure:
                Tables: {tables}
                Relationships: {relationships}
                Measures: {measures}
                
                Provide responses in the following format:
                {format_instructions}
                """),
                ("user", "{query}")
            ])
            
        except Exception as e:
            raise ValueError(f"Error initializing QueryProcessor: {str(e)}")

    def _format_model_info(self) -> Dict[str, str]:
        """Format model structure for prompt"""
        try:
            tables = "\n".join([
                f"- {table['name']}: {', '.join(table['columns'])}"
                for table in self.model_structure.tables
            ])
            
            relationships = "\n".join([
                f"- {rel['fromTable']}.{rel['fromColumn']} -> {rel['toTable']}.{rel['toColumn']}"
                for rel in self.model_structure.relationships
            ])
            
            measures = ", ".join(self.model_structure.measures)
            
            return {
                "tables": tables or "No tables defined",
                "relationships": relationships or "No relationships defined",
                "measures": measures or "No measures defined"
            }
        except Exception as e:
            raise ValueError(f"Error formatting model info: {str(e)}")

    def process_query(self, query_text: str) -> Dict:
        """Process natural language query"""
        try:
            # Format model information
            model_info = self._format_model_info()
            
            # Create and run the chain
            chain = self.prompt | self.llm | self.output_parser
            
            # For the initial prototype, we'll use mock data but with proper structure
            mock_response = QueryResult(
                type="data",
                result={
                    'values': [120, 150, 180, 210, 240],
                    'labels': ['Q1', 'Q2', 'Q3', 'Q4', 'Q5'],
                    'chart_type': 'bar'
                },
                explanation="Showing quarterly sales trend with mock data."
            )
            
            return mock_response.model_dump()
            
        except Exception as e:
            error_response = QueryResult(
                type="error",
                explanation=f"Error processing query: {str(e)}",
                suggestions=[
                    "Try simplifying your query",
                    "Make sure all column and measure names are correct",
                    "Check the query syntax and try again"
                ]
            )
            return error_response.model_dump()

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
        query = Query(
            text=query_text,
            result=json.dumps(response)
        )
        db.session.add(query)
        db.session.commit()
        
        return response
        
    except Exception as e:
        error_response = QueryResult(
            type="error",
            explanation=f"Error processing query: {str(e)}",
            suggestions=[
                "Try simplifying your query",
                "Make sure all column and measure names are correct",
                "Check the query syntax and try again"
            ]
        )
        return error_response.model_dump()
