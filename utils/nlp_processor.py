def process_query(query_text):
    """
    Process natural language query and convert it to structured format
    Uses basic string processing instead of spaCy
    """
    # Basic tokenization by splitting on spaces
    tokens = query_text.lower().split()
    
    # Simple entity extraction based on common keywords
    entities = []
    keywords = ['show', 'display', 'find', 'sales', 'revenue', 'customers', 'products']
    
    for token in tokens:
        if token in keywords:
            entities.append((token, 'KEYWORD'))
    
    # Basic query processing logic
    processed_query = {
        'intent': 'query',
        'entities': entities,
        'tokens': tokens,
        'original_text': query_text
    }
    
    # Mock response for demonstration
    response = {
        'type': 'data',
        'result': {
            'values': [100, 200, 300],
            'labels': ['A', 'B', 'C'],
            'chart_type': 'bar'
        },
        'explanation': 'Based on your query, here are the results:'
    }
    
    return response
