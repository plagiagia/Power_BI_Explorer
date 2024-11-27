import json
import logging
from typing import List, Dict, Any, Optional, Set

logger = logging.getLogger(__name__)

class DataProcessor:
    """Processes the report JSON file to extract visual data."""

    def __init__(self):
        self.json_file_path = None
        self.visuals_data: List[List[str]] = []
        self.data: Dict[str, Any] = {}

    def process_json(self) -> None:
        """Processes the JSON file and extracts data into visuals_data."""
        if not self.json_file_path:
            logger.error("JSON file path not set")
            return

        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                self.data = json.load(file)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error reading or parsing the JSON file: {e}")
            return

        filters_str = self.data.get('filters', '[]')
        page_filters = self.safe_json_loads(filters_str)
        if page_filters:
            filter_name = page_filters[0].get('name', '')
            page_filter_fields = self.extract_filter_fields(page_filters)
            if page_filter_fields:
                self.visuals_data.append(
                    ['All Pages', 'Global Level Filters', filter_name, '', page_filter_fields, '', '']
                )

        for section in self.data.get('sections', []):
            self.process_section(section)

    def safe_json_loads(self, data: Any) -> Any:
        """Safely loads JSON data from a string or returns the data if already a dict."""
        if isinstance(data, str):
            try:
                return json.loads(data)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON data: {e}")
                return []
        return data

    def process_section(self, section: Dict[str, Any]) -> None:
        """Processes a section of the report."""
        filters_str = section.get('filters', '[]')
        section_filters = self.safe_json_loads(filters_str)
        page_name = section.get('displayName', '')
        if section_filters:
            filter_name = section_filters[0].get('name', '')
            section_filter_fields = self.extract_filter_fields(section_filters)
            if section_filter_fields:
                self.visuals_data.append(
                    [page_name, 'Page Level Filters', filter_name, '', section_filter_fields, '', '']
                )

        for visual in section.get('visualContainers', []):
            visual_data = self.extract_visual_data(visual, page_name)
            self.visuals_data.append(visual_data)

    def extract_filter_fields(self, filter_data: List[Dict[str, Any]]) -> str:
        """Extracts filter fields from filter data."""
        filter_fields = []
        for f in filter_data:
            expression = f.get('expression', {})
            if isinstance(expression, dict):
                for key, expr in expression.items():
                    if isinstance(expr, dict) and 'Expression' in expr and 'Property' in expr:
                        entity = expr['Expression'].get('SourceRef', {}).get('Entity', '')
                        property_name = expr.get('Property', '')
                        if entity and property_name:
                            filter_fields.append(f"{entity}[{property_name}]")
        return "; ".join(filter_fields)

    def extract_visual_data(self, visual: Dict[str, Any], page_name: str) -> List[str]:
        """Extracts data from a visual."""
        config_str = visual.get('config', '{}')
        config = self.safe_json_loads(config_str)

        visual_config = None
        for key in config:
            if isinstance(config[key], dict) and 'visualType' in config[key]:
                visual_config = config[key]
                break

        if not visual_config:
            return [page_name, "Unknown visual type", "", "", "", '', '']

        visual_type = visual_config.get('visualType', '')
        visual_name = config.get('name', '')

        if 'prototypeQuery' not in visual_config:
            return [page_name, visual_type, visual_name, "", "", '', '']

        entity_aliases = {
            item['Name']: item['Entity']
            for item in visual_config['prototypeQuery'].get('From', [])
        }

        select_fields = self.extract_fields(
            visual_config['prototypeQuery'].get('Select', []), entity_aliases
        )

        filter_data_str = visual.get('filters', '[]')
        filter_data = self.safe_json_loads(filter_data_str)
        filter_fields = self.extract_filter_fields(filter_data)

        object_data = visual_config.get('objects', {})
        object_fields = self.extract_vc_objects_fields(object_data)

        vc_objects_data = visual_config.get('vcObjects', {})
        vc_objects_fields = self.extract_vc_objects_fields(vc_objects_data)

        return [
            page_name,
            visual_type,
            visual_name,
            select_fields,
            filter_fields,
            vc_objects_fields,
            object_fields
        ]

    def extract_fields(
        self, fields: List[Dict[str, Any]], entity_aliases: Dict[str, str]
    ) -> str:
        """Extracts field names from select fields."""
        extracted_fields = []
        for field in fields:
            field_details = None
            if 'Column' in field:
                field_details = field['Column']
            elif 'Aggregation' in field:
                field_details = field['Aggregation']['Expression']['Column']
            elif 'Measure' in field:
                field_details = field['Measure']

            if not field_details:
                continue

            expr = field_details.get('Expression', {})
            source_ref = expr.get('SourceRef', {})
            entity_alias = source_ref.get('Source', '')
            entity_name = entity_aliases.get(entity_alias, '')
            property_name = field_details.get('Property', '')

            if entity_name and property_name:
                field_name = f"{entity_name}[{property_name}]"
                extracted_fields.append(field_name)

        return "; ".join(extracted_fields)

    def extract_vc_objects_fields(self, vc_object: Any, current_entity: Optional[str] = None) -> str:
        """Recursively extracts fields from vcObjects or objects data."""
        fields = []
        if isinstance(vc_object, dict):
            for key, value in vc_object.items():
                if isinstance(value, dict):
                    fields.extend(
                        self.extract_vc_objects_fields(value, current_entity).split("; ")
                    )
                elif isinstance(value, list):
                    for item in value:
                        fields.extend(
                            self.extract_vc_objects_fields(item, current_entity).split("; ")
                        )
                elif key == 'expr' and isinstance(value, dict):
                    expr_fields = self.extract_expression_fields(value)
                    fields.extend(expr_fields)
        elif isinstance(vc_object, list):
            for item in vc_object:
                fields.extend(
                    self.extract_vc_objects_fields(item, current_entity).split("; ")
                )
        return "; ".join(filter(None, fields))

    def extract_expression_fields(self, expr_obj: Dict[str, Any]) -> List[str]:
        """Extracts fields from an expression object."""
        extracted_fields = []
        if isinstance(expr_obj, dict):
            if 'Expression' in expr_obj and 'Property' in expr_obj:
                entity = expr_obj['Expression'].get('SourceRef', {}).get('Entity', '')
                property_name = expr_obj.get('Property', '')
                if entity and property_name:
                    extracted_fields.append(f"{entity}[{property_name}]")
            else:
                for key, value in expr_obj.items():
                    if isinstance(value, dict):
                        extracted_fields.extend(self.extract_expression_fields(value))
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                extracted_fields.extend(self.extract_expression_fields(item))
        return extracted_fields

    def get_used_measures(self) -> Set[str]:
        """Extracts used measures from visuals_data."""
        used_measures = set()
        for visual_data in self.visuals_data:
            for index in [3, 4, 5, 6]:
                if index < len(visual_data):
                    fields = visual_data[index].split('; ')
                    for field in fields:
                        if '[' in field and ']' in field:
                            measure = field.split('[')[-1].replace(']', '').strip()
                            if measure:
                                used_measures.add(measure)
        return used_measures
