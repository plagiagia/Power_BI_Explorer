import os
from flask import Flask, render_template, request, jsonify
from utils.database import db
from utils.nlp_processor import process_query
from utils.powerbi_parser import DataProcessor
from models import PowerBIModel
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
            data_processor = DataProcessor()
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
            from utils.nlp_processor import store_embeddings
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

with app.app_context():
    db.create_all()
