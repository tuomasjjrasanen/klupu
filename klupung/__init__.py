import flask

def create_app(db_uri):
    app = flask.Flask(__name__)

    # Database session must be initialized before models, because models
    # rely on SQLAlchemy ORM session.
    import klupung.db
    klupung.db.create_session(db_uri)

    import klupung.api
    app.register_blueprint(klupung.api.v0)

    return app
