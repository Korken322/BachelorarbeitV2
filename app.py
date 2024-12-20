from flask import Flask
from routes.index import index_bp
from routes.upload import upload_bp
from routes.relevant import relevant_bp
from routes.result import result_bp
from routes.batch import batch_bp
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
# Flask-Anwendung erstellen
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp'

# Register Blueprints
app.register_blueprint(index_bp, url_prefix='/')
app.register_blueprint(upload_bp, url_prefix='/upload')
app.register_blueprint(relevant_bp, url_prefix='/relevant')
app.register_blueprint(result_bp, url_prefix="/result")
app.register_blueprint(batch_bp, url_prefix="/batch")

if __name__ == '__main__':
    app.run(debug=True)
