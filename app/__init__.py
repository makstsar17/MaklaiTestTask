from flask import Flask


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_pyfile("../instance/config.py")

    from .paraphrase import paraphrase_bp
    app.register_blueprint(paraphrase_bp)

    return app
