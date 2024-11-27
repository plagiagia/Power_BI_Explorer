import os
from flask import Flask, render_template, g, request, jsonify
from utils.powerbi_parser import DataProcessor
from utils.lineage_view import LineageView
from utils.database import db
from models import PowerBIModel, Query, FileEmbedding
import json
import re

app = Flask(__name__, 
            static_url_path='',
            static_folder='static')

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Define paths relative to the project root
DATA_DIR = os.path.join(os.getcwd(), 'data')
REPORT_JSON_PATH = os.path.join(DATA_DIR, 'report.json')
MEASURE_DEPENDENCIES_TSV_PATH = os.path.join(DATA_DIR, 'MeasureDependencies.tsv')
MODEL_JSON_PATH = os.path.join(DATA_DIR, 'model.json')

def get_data_processor():
    if 'data_processor' not in g:
        if os.path.exists(REPORT_JSON_PATH):
            g.data_processor = DataProcessor(REPORT_JSON_PATH)
        else:
            g.data_processor = None
    return g.data_processor

def get_lineage_view_processor():
    if 'lineage_view_processor' not in g:
        if os.path.exists(MEASURE_DEPENDENCIES_TSV_PATH):
            g.lineage_view_processor = LineageView(MEASURE_DEPENDENCIES_TSV_PATH)
        else:
            g.lineage_view_processor = None
    return g.lineage_view_processor

@app.teardown_appcontext
def teardown(exception):
    g.pop('data_processor', None)
    g.pop('lineage_view_processor', None)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    content = file.read().decode('utf-8')
    
    try:
        # Save the file content
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(REPORT_JSON_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Process the data
        data_processor = get_data_processor()
        data_processor.process_json()
        
        return jsonify({'success': True, 'data': {'message': 'File uploaded successfully'}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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
        if not os.path.exists(MODEL_JSON_PATH):
            return render_template('source_explorer.html', 
                                nodes=[], 
                                edges=[], 
                                m_queries_info=[])
        
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
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
