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

See deployment/jkl/README.rst for a real-world deployment example.
