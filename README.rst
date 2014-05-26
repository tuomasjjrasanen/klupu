=========
 KlupuNG
=========

Klupu Next Generation is `OpenAhjo API
<http://dev.hel.fi/apis/openahjo>`_ -compatible implementation for
decision material published with KTweb.

Copyright © 2014 `Koodilehto Osk <http://koodilehto.fi>`_

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or (at
your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

``COPYING`` contains a copy of the GNU Affero General Public License.

Dependencies
============

* `Python 2.7 <http://python.org/download/releases/2.7/>`_
* `Flask <http://flask.pocoo.org/>`_
* `Flask-SQLAlchemy <http://pythonhosted.org/Flask-SQLAlchemy/>`_

Recommended tools
=================

* `pip <http://www.pip-installer.org/>`_
* `virtualenv <http://www.virtualenv.org>`_
* `Docutils <http://docutils.sourceforge.net/>`_
* `Gunicorn <http://gunicorn.org/>`_

Installation
============

With pip::

 pip install -r requirements.txt
 python setup.py sdist
 pip install dist/klupung-0.1.0.tar.gz

Without pip, install packages listed in ``requirements.txt`` manually
and then install klupung by running ``python setup.py install``.

Setup and running
=================

Download KTWeb meeting documents::

  klupung-download-ktweb deployment/jkl/ktweb_urls.txt ktweb-jkl

Initialize the database and create tables (in this example we are using sqlite3)::

  klupung-dbinit sqlite:///jkl.db

Populate the database with data which cannot be scraped from the meeting documents::

  klupung-dbimport-categories sqlite:///jkl.db deployment/jkl/categories.csv
  klupung-dbimport-policymakers sqlite:///jkl.db deployment/jkl/policymakers.csv

Import previously downloaded meeting documents::

  klupung-dbimport-ktweb sqlite:///jkl.db ktweb-jkl

Run in development mode::

  klupung-stupid-apiserver sqlite:///jkl.db

Run in production mode::

  gunicorn --env KLUPUNG_DB_URI='sqlite:///jkl.db' klupung.flask.wsgi:app

Please refer to `the documentation of gunicorn
<http://docs.gunicorn.org>`_ for further information.
