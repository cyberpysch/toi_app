from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
