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

import datetime
import re
import unicodedata

import flask

import klupung.models

v0 = flask.Blueprint("v0", __name__, url_prefix="/api/v0")

_PUNCT_RE = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

def _slugify(text, delim=u'-'):
    result = []
    for word in _PUNCT_RE.split(text.lower()):
        word = unicodedata.normalize('NFKD', word).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return unicode(delim.join(result))

def _policymaker_resource(policymaker):
    return {
        "id": policymaker.id,
        "abbreviation": policymaker.abbreviation,
        "name": None,
        "origin_id": None,
        "slug": _slugify(policymaker.abbreviation),
        "summary": None,
        "resource_uri": flask.url_for("._policymaker_route",
                                      policymaker_id=policymaker.id),
        }

@v0.route("/policymaker/")
def _policymakers_route():
    return "list of policymakers"

@v0.route("/policymaker/<int:policymaker_id>/")
def _policymaker_route(policymaker_id=None):
    policymaker = klupung.models.Policymaker.query.get_or_404(policymaker_id)

    resource = _policymaker_resource(policymaker)

    return flask.jsonify(**resource)

def _meeting_resource(meeting):
    return {
        "id": meeting.id,
        "date": str(meeting.start_datetime.date()),
        "minutes": True,
        "number": 1,
        "policymaker": flask.url_for("._policymaker_route",
                                     policymaker_id=meeting.policymaker.id),
        "policymaker_name": None,
        "year": meeting.start_datetime.year,
        "resource_uri": flask.url_for("._meeting_route", meeting_id=meeting.id),
        }

@v0.route("/meeting/")
def _meetings_route():
    return "list of meetings"

@v0.route("/meeting/<int:meeting_id>/")
def _meeting_route(meeting_id=None):
    meeting = klupung.models.Meeting.query.get_or_404(meeting_id)

    resource = _meeting_resource(meeting)

    return flask.jsonify(**resource)


def _meeting_document_resource(meeting_document):
    return {
        "id": meeting_document.id,
        "last_modified_time": None,
        "meeting": _meeting_resource(meeting_document.meeting),
        "organisation": None,
        "origin_id": meeting_document.origin_id,
        "origin_url": meeting_document.origin_url,
        "publish_time": None,
        "type": "minutes",
        "xml_uri": None,
        "resource_uri": flask.url_for("._meeting_document_route",
                                      meeting_document_id=meeting_document.id)
        }

@v0.route("/meeting_document/")
def _meeting_documents_route():
    return "list of meeting documents"

@v0.route("/meeting_document/<int:meeting_document_id>/")
def _meeting_document_route(meeting_document_id=None):
    meeting_document = klupung.models.MeetingDocument.query.get_or_404(meeting_document_id)

    resource = _meeting_document_resource(meeting_document)

    return flask.jsonify(**resource)
