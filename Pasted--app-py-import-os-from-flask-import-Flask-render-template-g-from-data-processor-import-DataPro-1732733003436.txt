# app.py
import os
from flask import Flask, render_template, g
from data_processor import DataProcessor
from lineage_view import LineageView
import json
import re

app = Flask(__name__)

# Define paths relative to the project root
REPORT_JSON_PATH = os.path.join('data', 'D:\GitHub\Personal\GPT_Projects\WebAPP\\report.json')
MEASURE_DEPENDENCIES_TSV_PATH = os.path.join('data', 'D:\GitHub\Personal\GPT_Projects\WebAPP\MeasureDependencies.tsv')
MODEL_JSON_PATH = os.path.join('data', 'D:\GitHub\Personal\GPT_Projects\WebAPP\model.json')

def get_data_processor():
    if 'data_processor' not in g:
        data_processor = DataProcessor(REPORT_JSON_PATH)
        data_processor.process_json()
        g.data_processor = data_processor
    return g.data_processor

def get_lineage_view_processor():
    if 'lineage_view_processor' not in g:
        lineage_view_processor = LineageView(MEASURE_DEPENDENCIES_TSV_PATH)
        lineage_view_processor.process_lineage_data()
        g.lineage_view_processor = lineage_view_processor
    return g.lineage_view_processor

@app.teardown_appcontext
def teardown(exception):
    g.pop('data_processor', None)
    g.pop('lineage_view_processor', None)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/table-view')
def table_view():
    data_processor = get_data_processor()
    return render_template('table_view.html', table_data=data_processor.visuals_data)

@app.route('/lineage-view')
def lineage_view_route():
    lineage_view_processor = get_lineage_view_processor()
    return render_template(
        'lineage_view.html',
        nodes=lineage_view_processor.nodes,
        edges=lineage_view_processor.edges
    )

@app.route('/dax-expressions')
def dax_expressions():
    lineage_view_processor = get_lineage_view_processor()
    dax_expressions = lineage_view_processor.extract_dax_expressions()
    return render_template('dax_expressions.html', dax_expressions=dax_expressions)

@app.route('/source-explorer')
def source_explorer():
    try:
        with open(MODEL_JSON_PATH, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except (json.JSONDecodeError, IOError) as e:
        app.logger.error(f"Error reading or parsing the model JSON file: {e}")
        return render_template('error.html', message="Error loading model data.")

    tables = data.get('model', {}).get('tables', [])
    expressions = data.get('model', {}).get('expressions', [])

    m_queries_info = []

    def starts_with_let(query):
        return query.strip().lower().startswith('let')

    for table in tables:
        for partition in table.get('partitions', []):
            source = partition.get('source', {})
            if source.get('type') == 'm':
                m_query = '\n'.join(source.get('expression', []))
                if starts_with_let(m_query):
                    m_queries_info.append({
                        'table_name': table['name'],
                        'm_query': m_query
                    })

    for expression in expressions:
        if expression.get('kind') == 'm':
            m_query = '\n'.join(expression.get('expression', []))
            if starts_with_let(m_query):
                m_queries_info.append({
                    'table_name': expression['name'],
                    'm_query': m_query
                })

    nodes = []
    edges = []

    for query_info in m_queries_info:
        nodes.append(
            {'id': query_info['table_name'], 'label': query_info['table_name']}
        )

    for query_info in m_queries_info:
        m_query_text = query_info['m_query']
        for other_query_info in m_queries_info:
            if other_query_info['table_name'] != query_info['table_name']:
                pattern = r'"{}"'.format(
                    re.escape(other_query_info['table_name'])
                )
                if re.search(pattern, m_query_text):
                    edges.append(
                        {'from': query_info['table_name'], 'to': other_query_info['table_name']}
                    )

    return render_template(
        'source_explorer.html',
        nodes=nodes,
        edges=edges,
        m_queries_info=m_queries_info
    )

@app.route('/unused-measures')
def unused_measures_view():
    data_processor = get_data_processor()
    lineage_view_processor = get_lineage_view_processor()

    used_measures = data_processor.get_used_measures()
    all_measures = lineage_view_processor.get_all_measures()

    unused_measures = sorted(list(all_measures - used_measures))

    return render_template('unused_measures.html', unused_measures=unused_measures or [])

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])
