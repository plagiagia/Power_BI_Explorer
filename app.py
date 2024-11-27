from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from models import db, PowerBIModel
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
            
            # Store in database
            model = PowerBIModel(
                name=filename,
                content=content
            )
            db.session.add(model)
            db.session.commit()
            
            return jsonify({'success': True})
        return jsonify({'error': 'Invalid file type'})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
