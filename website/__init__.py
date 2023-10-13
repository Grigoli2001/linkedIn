from flask import Flask
import os
from flask_login import LoginManager
login_manager = LoginManager()
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'qwerty'
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    # Initialize the LoginManager
    login_manager.login_view = 'login_blueprint.login_logic'  # Set the login view
    login_manager.init_app(app)

# Register Blueprintss
    from .root import root
    from .APIs.register import register
    from .APIs.login import login_blueprint
    app.register_blueprint(root,url_prefix='/')
    app.register_blueprint(register,url_prefix='/register')
    app.register_blueprint(login_blueprint,url_prefix='/login')
    return app
