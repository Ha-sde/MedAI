from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_socketio import SocketIO
import os
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
jwt = JWTManager()
socketio = SocketIO()

def create_app(config_name=None):
    app = Flask(__name__)

    # Config
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'medai-secret-2024')
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///medai.db')
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-medai-secret')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    CORS(app, origins="*", supports_credentials=True)
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')

    from app.routes.auth import auth_bp
    from app.routes.patient import patient_bp
    from app.routes.consultation import consultation_bp
    from app.routes.report import report_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(patient_bp, url_prefix='/api/patient')
    app.register_blueprint(consultation_bp, url_prefix='/api/consultation')
    app.register_blueprint(report_bp, url_prefix='/api/report')

    # Serve frontend
    from flask import send_from_directory
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, 'index.html')

    with app.app_context():
        db.create_all()

    return app
