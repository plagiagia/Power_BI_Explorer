# lineage_view.py
import csv
import logging
from typing import List, Dict, Set, Tuple

logger = logging.getLogger(__name__)


class LineageView:
    """Processes the MeasureDependencies.tsv file to build measure lineage."""

    def __init__(self, tsv_file_path: str):
        self.tsv_file_path = tsv_file_path
        self.nodes: List[Dict[str, str]] = []
        self.edges: List[Dict[str, str]] = []
        self.unique_edges: Set[Tuple[str, str]] = set()
        self.unique_columns: Set[str] = set()
        self.measure_index = 0
        self.dax_expression_index = 1
        self.parent_index = 2
        self.child_index = 3
        self.column_index = 5

    def process_lineage_data(self) -> None:
        """Processes the TSV file to extract nodes and edges for the lineage graph."""
        try:
            with open(self.tsv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file, delimiter='\t')
                headers = next(reader)  # Skip the header row
                data = list(reader)  # Read the rest of the data
        except IOError as e:
            logger.error(f"Error reading the TSV file: {e}")
            return

        for measure in data:
            measure_name = measure[self.measure_index]
            self.nodes.append({
                'id': measure_name,
                'label': measure_name,
                'dax': measure[self.dax_expression_index]
            })

            parent_measures = measure[self.parent_index].split('; ') if measure[self.parent_index] else []

            # Processing for columns
            measure_columns = measure[self.column_index].split('; ') if measure[self.column_index] else []
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

            # Processing for parent-child relationships
            for parent in parent_measures:
                if parent:
                    edge = (parent, measure_name)
                    if edge not in self.unique_edges:
                        self.unique_edges.add(edge)
                        self.edges.append({'from': parent, 'to': measure_name})

    def extract_dax_expressions(self) -> List[Tuple[str, str]]:
        """Extracts DAX expressions for each measure."""
        dax_expressions = []
        for measure in self.nodes:
            if 'label' in measure and measure.get('type') != 'column':
                label = measure['label'].strip()
                if label:
                    dax_expression = measure.get('dax', '')
                    if dax_expression:
                        # Replace escape sequences with their corresponding characters
                        dax_expression = dax_expression.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
                        dax_expressions.append((label, dax_expression))
        return dax_expressions

    def get_all_measures(self) -> Set[str]:
        """Retrieves all final measures (measures without children)."""
        final_measures = set()
        parent_measures = set()

        try:
            with open(self.tsv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file, delimiter='\t')
                next(reader)  # Skip the header row

                for measure in reader:
                    measure_name = measure[self.measure_index]
                    child_measures = measure[self.child_index].split('; ') if measure[self.child_index] else []

                    if not child_measures:
                        final_measures.add(measure_name)

                    if child_measures:
                        parent_measures.add(measure_name)
        except IOError as e:
            logger.error(f"Error reading the TSV file: {e}")

        return final_measures - parent_measures
