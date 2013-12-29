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

import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.interfaces
import sqlalchemy.orm

_engine = None
session = None
Base = None

class _ForeignKeysListener(sqlalchemy.interfaces.PoolListener):
    def connect(self, dbapi_con, con_record):
        db_cursor = dbapi_con.execute("pragma foreign_keys=ON")

def create_session(db_uri):
    global _engine
    global session
    global Base

    if session:
        return False

    _engine = sqlalchemy.create_engine(db_uri, convert_unicode=True,
                                       listeners=[_ForeignKeysListener()])
    session = sqlalchemy.orm.scoped_session(
        sqlalchemy.orm.sessionmaker(autocommit=False,
                                    autoflush=False,
                                    bind=_engine))
    Base = sqlalchemy.ext.declarative.declarative_base()
    Base.query = session.query_property()

    return True

def create_tables():
    import klupung.models
    Base.metadata.create_all(bind=_engine)
