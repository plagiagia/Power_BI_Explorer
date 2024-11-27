import json

def parse_bim_file(content):
    """
    Parse .bim file content and extract relevant information
    """
    try:
        data = json.loads(content)
        model = {
            'tables': [],
            'relationships': [],
            'measures': []
        }
        
        if 'model' in data:
            if 'tables' in data['model']:
                model['tables'] = [
                    {
                        'name': table.get('name', ''),
                        'columns': [col.get('name', '') for col in table.get('columns', [])]
                    }
                    for table in data['model']['tables']
                ]
            
            if 'relationships' in data['model']:
                model['relationships'] = data['model']['relationships']
        
        return model
    except Exception as e:
        raise ValueError(f"Invalid .bim file format: {str(e)}")

def parse_report_file(content):
    """
    Parse report.json file content and extract relevant information
    """
    try:
        data = json.loads(content)
        report = {
            'name': data.get('name', ''),
            'pages': [],
            'visualizations': []
        }
        
        if 'pages' in data:
            report['pages'] = [
                {
                    'name': page.get('name', ''),
                    'visuals': [v.get('name', '') for v in page.get('visuals', [])]
                }
                for page in data['pages']
            ]
        
        return report
    except Exception as e:
        raise ValueError(f"Invalid report.json file format: {str(e)}")
