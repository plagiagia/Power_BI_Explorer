import os
from typing import Dict, List, Optional
from datetime import datetime
from models import PowerBIModel, Query, FileEmbedding
from utils.database import db
from utils.powerbi_parser import DataProcessor
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

def extract_context(model_data: Dict, query: str) -> Dict:
    """Extract relevant context from model data based on query"""
    data_processor = DataProcessor()
    
    # Initialize context
    context = {
        'relevant_measures': [],
        'relevant_tables': [],
        'dax_context': [],
        'relationships': [],
        'm_queries': []
    }
    
    # Process model data
    if isinstance(model_data, str):
        model_data = json.loads(model_data)
    
    # Extract measures and their context
    for table in model_data.get('tables', []):
        for measure in table.get('measures', []):
            measure_name = f"{table['name']}[{measure['name']}]"
            dax_context = data_processor.get_dax_context(measure_name)
            if dax_context['expression']:
                context['dax_context'].append(dax_context)
    
    # Extract relationships
    context['relationships'] = model_data.get('relationships', [])
    
    # Extract M queries
    context['m_queries'] = model_data.get('m_queries', [])
    
    return context

def store_embeddings(model_id: int, content: str):
    """Store content chunks and their embeddings"""
    try:
        # Parse the content to extract structured information
        data_processor = DataProcessor()
        model_data = json.loads(content)
        context = extract_context(model_data, "")  # Extract full context
        
        # Create chunks from structured data
        chunks = []
        
        # Add measure definitions and DAX expressions
        for dax_ctx in context['dax_context']:
            chunks.append(f"Measure: {dax_ctx['expression']}")
        
        # Add relationships
        for rel in context['relationships']:
            chunks.append(
                f"Relationship: {rel['fromTable']}.{rel['fromColumn']} -> "
                f"{rel['toTable']}.{rel['toColumn']}"
            )
        
        # Add M queries
        for query in context['m_queries']:
            chunks.append(f"M Query for {query['table_name']}: {query['query']}")
        
        # Generate and store embeddings
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

def get_completion(query: str, context: List[str]) -> str:
    """Get completion from OpenAI GPT model"""
    messages = [
        {"role": "system", "content": "You are a Power BI data analysis assistant. Use the provided context to answer queries about the Power BI model. Return responses in JSON format with 'explanation', 'chart_type', and 'data_suggestion' fields."},
        {"role": "user", "content": f"Context:\n{chr(10).join(context)}\n\nQuery: {query}"}
    ]
    
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0
    )
    return response.choices[0].message.content

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

        # Parse model data
        model_data = json.loads(latest_model.content)
        context = extract_context(model_data, query_text)
        
        # Find relevant content chunks
        similar_chunks = find_similar_chunks(query_text, latest_model.id)
        
        # Extract measure dependencies and DAX context
        relevant_measures = []
        for dax_ctx in context['dax_context']:
            if any(chunk for chunk in similar_chunks if dax_ctx['expression'] in chunk):
                relevant_measures.append(dax_ctx)
        
        # Generate response using GPT
        gpt_response = get_completion(
            query_text,
            similar_chunks + [
                f"Measure {i}: {m['expression']}" 
                for i, m in enumerate(relevant_measures, 1)
            ]
        )
        
        try:
            gpt_data = json.loads(gpt_response)
        except json.JSONDecodeError:
            gpt_data = {
                'explanation': gpt_response,
                'chart_type': 'bar',
                'data_suggestion': None
            }
        
        # Format response with actual model context
        response = {
            'type': 'data',
            'result': {
                'values': [float(x) for x in gpt_data.get('data_suggestion', [0, 0, 0, 0, 0])],
                'labels': [str(x) for x in range(len(gpt_data.get('data_suggestion', [0, 0, 0, 0, 0])))],
                'chart_type': gpt_data.get('chart_type', 'bar')
            },
            'explanation': gpt_data.get('explanation', 'Analysis based on available measures'),
            'context': {
                'measures': relevant_measures,
                'relationships': [rel for rel in context['relationships'] 
                                if any(chunk for chunk in similar_chunks 
                                      if rel['fromTable'] in chunk or rel['toTable'] in chunk)],
                'similar_chunks': similar_chunks
            }
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
