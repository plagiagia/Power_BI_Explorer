from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from models import db, PowerBIModel
from utils.data_processor import DataProcessor
from utils.lineage_view import LineageView
from utils.powerbi_parser import PowerBIParser
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'tsv', 'json', 'bim'}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            content = file.read().decode('utf-8')
            
            # Delete old records
            PowerBIModel.query.delete()
            db.session.commit()
            
            # Store new file
            model = PowerBIModel(
                name=filename,
                content=content
            )
            db.session.add(model)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'File uploaded successfully'})
        return jsonify({'error': 'Invalid file type'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/table-view')
def table_view():
    # Get latest uploaded file data from database
    model = PowerBIModel.query.order_by(PowerBIModel.created_at.desc()).first()
    if model:
        processor = DataProcessor()
        processor.process_json(model.content)
        return render_template('table_view.html', table_data=processor.visuals_data)
    return render_template('table_view.html', table_data=[])

@app.route('/lineage-view')
def lineage_view():
    model = PowerBIModel.query.order_by(PowerBIModel.created_at.desc()).first()
    if model:
        lineage = LineageView()
        lineage.process_model_data(model.content)
        return render_template('lineage_view.html', nodes=lineage.nodes, edges=lineage.edges)
    return render_template('lineage_view.html', nodes=[], edges=[])

@app.route('/dax-expressions')
def dax_expressions():
    model = PowerBIModel.query.order_by(PowerBIModel.created_at.desc()).first()
    if model:
        lineage = LineageView()
        lineage.process_model_data(model.content)
        expressions = lineage.extract_dax_expressions()
        return render_template('dax_expressions.html', expressions=expressions)
    return render_template('dax_expressions.html', expressions=[])

@app.route('/source-explorer')
def source_explorer():
    model = PowerBIModel.query.order_by(PowerBIModel.created_at.desc()).first()
    if model:
        parser = PowerBIParser()
        m_queries = parser.extract_m_queries(model.content)
        return render_template('source_explorer.html', queries=m_queries)
    return render_template('source_explorer.html', queries=[])

@app.route('/unused-measures')
def unused_measures():
    model = PowerBIModel.query.order_by(PowerBIModel.created_at.desc()).first()
    if model:
        lineage = LineageView()
        lineage.process_model_data(model.content)
        unused = lineage.get_unused_measures()
        return render_template('unused_measures.html', measures=unused)
    return render_template('unused_measures.html', measures=[])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
