import json
import re
from typing import Dict, List, Optional, Tuple
from .lineage_view import LineageView

class DataProcessor:
    def __init__(self):
        self.tables = []
        self.relationships = []
        self.measures = []
        self.m_queries = []
        self.lineage_view = LineageView()

    def _extract_m_queries(self, data: Dict) -> None:
        """Extract M queries from model data"""
        if 'model' not in data:
            return

        for table in data['model'].get('tables', []):
            for partition in table.get('partitions', []):
                source = partition.get('source', {})
                if source.get('type') == 'm':
                    m_query = '\n'.join(source.get('expression', []))
                    if m_query.strip().lower().startswith('let'):
                        self.m_queries.append({
                            'table_name': table['name'],
                            'query': m_query,
                            'type': 'table_source'
                        })

        # Extract M expressions
        for expression in data['model'].get('expressions', []):
            if expression.get('kind') == 'm':
                m_query = '\n'.join(expression.get('expression', []))
                if m_query.strip().lower().startswith('let'):
                    self.m_queries.append({
                        'name': expression['name'],
                        'query': m_query,
                        'type': 'expression'
                    })

    def parse_bim_file(self, content: str) -> Dict:
        """
        Parse .bim file content with enhanced extraction of measures, relationships,
        and M queries
        """
        try:
            data = json.loads(content)
            model = {
                'tables': [],
                'relationships': [],
                'measures': [],
                'm_queries': []
            }
            
            if 'model' in data:
                # Extract tables with enhanced metadata
                if 'tables' in data['model']:
                    model['tables'] = [
                        {
                            'name': table.get('name', ''),
                            'columns': [
                                {
                                    'name': col.get('name', ''),
                                    'dataType': col.get('dataType', ''),
                                    'sourceColumn': col.get('sourceColumn', '')
                                }
                                for col in table.get('columns', [])
                            ],
                            'measures': [
                                {
                                    'name': measure.get('name', ''),
                                    'expression': measure.get('expression', '')
                                }
                                for measure in table.get('measures', [])
                            ]
                        }
                        for table in data['model']['tables']
                    ]
                
                # Extract relationships with additional metadata
                if 'relationships' in data['model']:
                    model['relationships'] = [
                        {
                            'fromTable': rel.get('fromTable', ''),
                            'fromColumn': rel.get('fromColumn', ''),
                            'toTable': rel.get('toTable', ''),
                            'toColumn': rel.get('toColumn', ''),
                            'crossFilteringBehavior': rel.get('crossFilteringBehavior', 'automatic')
                        }
                        for rel in data['model']['relationships']
                    ]

                # Process model data for lineage tracking
                self.lineage_view.process_model_data(data)
                
                # Extract M queries
                self._extract_m_queries(data)
                model['m_queries'] = self.m_queries

            return model
        except Exception as e:
            raise ValueError(f"Invalid .bim file format: {str(e)}")

    def parse_report_file(self, content: str) -> Dict:
        """
        Parse report.json file content with enhanced visualization metadata
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
                        'visuals': [
                            {
                                'name': v.get('name', ''),
                                'type': v.get('type', ''),
                                'dataRoles': v.get('dataRoles', []),
                                'prototypeQuery': self._extract_prototype_query(v)
                            }
                            for v in page.get('visuals', [])
                        ]
                    }
                    for page in data['pages']
                ]
            
            return report
        except Exception as e:
            raise ValueError(f"Invalid report.json file format: {str(e)}")

    def _extract_prototype_query(self, visual: Dict) -> Optional[str]:
        """Extract and analyze the prototype query from a visual"""
        if 'dataTransforms' in visual:
            transforms = visual['dataTransforms']
            if isinstance(transforms, dict) and 'queryDefinition' in transforms:
                return transforms['queryDefinition']
        return None

    def get_dax_context(self, measure_name: str) -> Dict:
        """Get DAX expression context for a measure"""
        expression = self.lineage_view.get_measure_expression(measure_name)
        dependencies = self.lineage_view.get_measure_dependencies(measure_name)
        
        return {
            'expression': expression,
            'dependencies': list(dependencies),
            'tables': [table['name'] for table in self.tables if any(
                measure_name in m['name'] for m in table.get('measures', [])
            )]
        }
