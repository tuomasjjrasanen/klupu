import flask
import flask.ext.sqlalchemy

app = flask.Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///klupung.db'
db = flask.ext.sqlalchemy.SQLAlchemy(app)

db.create_all()

app.run()
