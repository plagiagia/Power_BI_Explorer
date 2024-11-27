import os
from flask import Flask, render_template, request, jsonify, g
from utils.database import db
from utils.nlp_processor import process_query, store_embeddings
from utils.powerbi_parser import DataProcessor
from utils.lineage_view import LineageView
from models import PowerBIModel, Query
import json

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///powerbi.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'bim', 'json'}

db.init_app(app)

def get_data_processor():
    if 'data_processor' not in g:
        g.data_processor = DataProcessor()
    return g.data_processor

def get_lineage_view():
    if 'lineage_view' not in g:
        g.lineage_view = LineageView()
    return g.lineage_view

@app.teardown_appcontext
def teardown_context(exception=None):
    g.pop('data_processor', None)
    g.pop('lineage_view', None)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        try:
            content = file.read().decode('utf-8')
            data_processor = get_data_processor()
            if file.filename.endswith('.bim'):
                model_data = data_processor.parse_bim_file(content)
            else:
                model_data = data_processor.parse_report_file(content)
            
            # Create PowerBIModel instance
            model = PowerBIModel(
                name=file.filename,
                content=json.dumps(model_data)
            )
            db.session.add(model)
            db.session.commit()
            
            # Generate and store embeddings
            store_embeddings(model.id, json.dumps(model_data))
            
            return jsonify({'success': True, 'data': model_data})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/query', methods=['POST'])
def process_natural_language_query():
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        result = process_query(data['query'])
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/table-view')
def table_view():
    data_processor = get_data_processor()
    latest_model = PowerBIModel.query.order_by(PowerBIModel.created_at.desc()).first()
    if not latest_model:
        return render_template('table_view.html', table_data=[])
    
    model_data = json.loads(latest_model.content)
    table_data = data_processor.extract_visual_data(model_data)
    return render_template('table_view.html', table_data=table_data)

@app.route('/lineage-view')
def lineage_view():
    lineage_view = get_lineage_view()
    latest_model = PowerBIModel.query.order_by(PowerBIModel.created_at.desc()).first()
    if not latest_model:
        return render_template('lineage_view.html', nodes=[], edges=[])
    
    model_data = json.loads(latest_model.content)
    lineage_view.process_model_data(model_data)
    return render_template('lineage_view.html', nodes=lineage_view.nodes, edges=lineage_view.edges)

@app.route('/dax-expressions')
def dax_expressions():
    lineage_view = get_lineage_view()
    latest_model = PowerBIModel.query.order_by(PowerBIModel.created_at.desc()).first()
    if not latest_model:
        return render_template('dax_expressions.html', dax_expressions=[])
    
    model_data = json.loads(latest_model.content)
    lineage_view.process_model_data(model_data)
    expressions = lineage_view.get_dax_context()
    return render_template('dax_expressions.html', dax_expressions=expressions)

@app.route('/source-explorer')
def source_explorer():
    data_processor = get_data_processor()
    latest_model = PowerBIModel.query.order_by(PowerBIModel.created_at.desc()).first()
    if not latest_model:
        return render_template('source_explorer.html', m_queries_info=[])
    
    model_data = json.loads(latest_model.content)
    m_queries = data_processor._extract_m_queries(model_data)
    return render_template('source_explorer.html', m_queries_info=m_queries)

@app.route('/unused-measures')
def unused_measures():
    data_processor = get_data_processor()
    lineage_view = get_lineage_view()
    latest_model = PowerBIModel.query.order_by(PowerBIModel.created_at.desc()).first()
    if not latest_model:
        return render_template('unused_measures.html', unused_measures=[])
    
    model_data = json.loads(latest_model.content)
    used_measures = data_processor.get_used_measures(model_data)
    all_measures = lineage_view.get_all_measures()
    unused_measures = sorted(list(all_measures - used_measures))
    return render_template('unused_measures.html', unused_measures=unused_measures)

with app.app_context():
    db.create_all()
