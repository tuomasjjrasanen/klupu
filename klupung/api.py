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
import urllib

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

def _get_uint_arg(name, default):
    arg = flask.request.args.get(name, "")
    arg = arg if arg else default
    error_msg = "Invalid value '%s' for argument '%s', " \
        "expected a positive integer." % (arg, name)
    error_response = flask.make_response(flask.jsonify(error=error_msg), 400)
    try:
        value = int(arg)
    except ValueError:
        return None, error_response
    else:
        if value < 0:
            return None, error_response
    return value, None

def _get_choice_arg(name, choices):
    arg = flask.request.args.get(name, "")
    arg = arg if arg else choices[0]
    error_msg = "Invalid value '%s' for argument '%s', expected %s." % \
        (arg, name, " or ".join([repr(s) for s in choices]))
    if arg not in choices:
        return None, flask.make_response(flask.jsonify(error=error_msg), 400)
    return arg, None

def _next_url(limit, offset, total_count):
    if limit + offset >= total_count:
        return None
    next_url_args = flask.request.args.to_dict()
    next_url_args["offset"] = offset + limit
    return "%s?%s" % (flask.request.path, urllib.urlencode(next_url_args))

def _prev_url(limit, offset):
    if offset <= 0:
        return None

    prev_url_args = flask.request.args.to_dict()
    prev_url_args["offset"] = max(offset - limit, 0)
    return "%s?%s" % (flask.request.path, urllib.urlencode(prev_url_args))

def _policymaker_resource(policymaker):
    return {
        "id": policymaker.id,
        "abbreviation": policymaker.abbreviation,
        "name": policymaker.name,
        "origin_id": policymaker.abbreviation,
        "slug": _slugify(policymaker.abbreviation),
        "summary": None,
        "resource_uri": flask.url_for("._policymaker_route",
                                      policymaker_id=policymaker.id),
        }

@v0.route("/policymaker/")
def _policymakers_route():
    limit, error_response = _get_uint_arg("limit", 20)
    if error_response:
        return error_response

    offset, error_response = _get_uint_arg("offset", 0)
    if error_response:
        return error_response

    order_by, error_response = _get_choice_arg("order_by", ("name", "-name"))
    if error_response:
        return error_response

    desc = False
    column_name = order_by
    if order_by.startswith("-"):
        column_name = order_by[1:]
        desc = True

    order_by_criterion = getattr(klupung.models.Policymaker, column_name)
    if desc:
        order_by_criterion = klupung.db.desc(order_by_criterion)

    policymakers = klupung.models.Policymaker.query.order_by(
        order_by_criterion).limit(limit).offset(offset).all()

    total_count = klupung.models.Policymaker.query.count()

    resource = {
        "meta": {
            "limit": limit,
            "next": _next_url(limit, offset, total_count),
            "offset": offset,
            "previous": _prev_url(limit, offset),
            "total_count": total_count,
            },
        "objects": [_policymaker_resource(p) for p in policymakers],
        }

    return flask.jsonify(**resource)

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
        "policymaker_name": meeting.policymaker.name,
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
    meeting_document = klupung.models.MeetingDocument.query.get_or_404(
        meeting_document_id)

    resource = _meeting_document_resource(meeting_document)

    return flask.jsonify(**resource)
