# KlupuNG
# Copyright (C) 2013 Koodilehto Osk <http://koodilehto.fi>.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import flask
import flask.ext.sqlalchemy
import flask.ext.autodoc

db = flask.ext.sqlalchemy.SQLAlchemy()

def create_app(db_uri):
    app = flask.Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri

    db.init_app(app)

    import klupung.flask.api
    klupung.flask.api.auto.init_app(app)

    app.register_blueprint(klupung.flask.api.v0)

    return app
