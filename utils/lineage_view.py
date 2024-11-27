import csv
import logging
import json
from typing import Set, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class LineageView:
    def __init__(self, tsv_file_path: Optional[str] = None):
        self.tsv_file_path = tsv_file_path
        self.nodes: List[Dict[str, str]] = []
        self.edges: List[Dict[str, str]] = []
        self.measure_dependencies: Dict[str, Set[str]] = {}
        self.dax_expressions: Dict[str, str] = {}
        self.unique_edges: Set[Tuple[str, str]] = set()
        self.unique_columns: Set[str] = set()
        self.measure_index = 0
        self.dax_expression_index = 1
        self.parent_index = 2
        self.child_index = 3
        self.column_index = 5

        if tsv_file_path:
            self.process_lineage_data()

    def process_lineage_data(self) -> None:
        """Processes the TSV file to extract nodes and edges for the lineage graph."""
        try:
            with open(self.tsv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file, delimiter='\t')
                next(reader)  # Skip the header row
                data = list(reader)
        except IOError as e:
            logger.error(f"Error reading the TSV file: {e}")
            return

        for measure in data:
            if len(measure) <= self.column_index:
                continue

            measure_name = measure[self.measure_index]
            self.nodes.append({
                'id': measure_name,
                'label': measure_name,
                'dax': measure[self.dax_expression_index]
            })

            parent_measures = measure[self.parent_index].split('; ') if measure[self.parent_index] else []
            measure_columns = measure[self.column_index].split('; ') if measure[self.column_index] else []

            # Process columns
            for column in measure_columns:
                if column:
                    if column not in self.unique_columns:
                        self.nodes.append({
                            'id': column,
                            'label': column,
                            'type': 'column'
                        })
                        self.unique_columns.add(column)

                    edge = (column, measure_name)
                    if edge not in self.unique_edges:
                        self.unique_edges.add(edge)
                        self.edges.append({'from': column, 'to': measure_name})

            # Process parent-child relationships
            for parent in parent_measures:
                if parent:
                    edge = (parent, measure_name)
                    if edge not in self.unique_edges:
                        self.unique_edges.add(edge)
                        self.edges.append({'from': parent, 'to': measure_name})

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
        for measure in self.measure_dependencies.keys():
            if not any(node['id'] == measure for node in self.nodes):
                self.nodes.append({
                    'id': measure,
                    'label': measure,
                    'type': 'measure'
                })
        
        for measure, dependencies in self.measure_dependencies.items():
            for dep in dependencies:
                edge = (measure, dep)
                if edge not in self.unique_edges:
                    self.unique_edges.add(edge)
                    self.edges.append({
                        'from': measure,
                        'to': dep,
                        'type': 'depends_on'
                    })

    def extract_dax_expressions(self) -> List[Tuple[str, str]]:
        """Extracts DAX expressions for each measure."""
        dax_expressions = []
        for measure in self.nodes:
            if 'label' in measure and measure.get('type') != 'column':
                label = measure['label'].strip()
                if label:
                    dax_expression = measure.get('dax', '')
                    if dax_expression:
                        dax_expression = dax_expression.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
                        dax_expressions.append((label, dax_expression))
        return dax_expressions

    def get_measure_dependencies(self, measure_name: str) -> Set[str]:
        """Get direct dependencies for a measure"""
        return self.measure_dependencies.get(measure_name, set())

    def get_measure_expression(self, measure_name: str) -> Optional[str]:
        """Get DAX expression for a measure"""
        return self.dax_expressions.get(measure_name)

    def get_all_measures(self) -> Set[str]:
        """Get all measure names"""
        measures = set()
        try:
            with open(self.tsv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file, delimiter='\t')
                next(reader)  # Skip the header row
                for measure in reader:
                    if measure and len(measure) > self.measure_index:
                        measures.add(measure[self.measure_index])
        except IOError as e:
            logger.error(f"Error reading the TSV file: {e}")
        return measures
