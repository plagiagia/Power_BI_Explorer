import json
from typing import Set, Dict, List, Optional

class LineageView:
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.measure_dependencies = {}
        self.dax_expressions = {}

    def process_model_data(self, model_data: Dict) -> None:
        """Process model data to extract measure dependencies and DAX expressions"""
        if not isinstance(model_data, dict):
            model_data = json.loads(model_data)

        self._extract_measures(model_data)
        self._build_dependency_graph()

    def _extract_measures(self, model_data: Dict) -> None:
        """Extract measures and their DAX expressions from model data"""
        if 'model' not in model_data:
            return

        for table in model_data['model'].get('tables', []):
            table_name = table.get('name', '')
            for measure in table.get('measures', []):
                measure_name = measure.get('name', '')
                expression = measure.get('expression', '')
                
                if measure_name and expression:
                    self.dax_expressions[f"{table_name}[{measure_name}]"] = expression
                    self._analyze_dax_dependencies(table_name, measure_name, expression)

    def _analyze_dax_dependencies(self, table_name: str, measure_name: str, expression: str) -> None:
        """Analyze DAX expression to identify measure dependencies"""
        measure_key = f"{table_name}[{measure_name}]"
        self.measure_dependencies[measure_key] = set()
        
        # Basic pattern matching for measure references
        import re
        measure_pattern = r'\[([^\]]+)\]'
        matches = re.finditer(measure_pattern, expression)
        
        for match in matches:
            referenced_measure = match.group(1)
            if referenced_measure != measure_name:  # Avoid self-reference
                self.measure_dependencies[measure_key].add(referenced_measure)

    def _build_dependency_graph(self) -> None:
        """Build nodes and edges for visualization"""
        # Reset existing graph
        self.nodes = []
        self.edges = []
        
        # Add nodes
        for measure in self.measure_dependencies.keys():
            self.nodes.append({
                'id': measure,
                'label': measure,
                'type': 'measure'
            })
        
        # Add edges
        for measure, dependencies in self.measure_dependencies.items():
            for dep in dependencies:
                self.edges.append({
                    'from': measure,
                    'to': dep,
                    'type': 'depends_on'
                })

    def get_measure_dependencies(self, measure_name: str) -> Set[str]:
        """Get direct dependencies for a measure"""
        return self.measure_dependencies.get(measure_name, set())

    def get_measure_expression(self, measure_name: str) -> Optional[str]:
        """Get DAX expression for a measure"""
        return self.dax_expressions.get(measure_name)

    def get_all_measures(self) -> Set[str]:
        """Get all measure names"""
        return set(self.dax_expressions.keys())
