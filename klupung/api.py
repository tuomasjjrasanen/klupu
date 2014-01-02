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

class Error(Exception):

    def __init__(self, code, message):
        self.code = code
        self.message = message

class InvalidArgumentError(Error):

    def __init__(self, arg, name, expected=""):
        message = "Invalid value '%s' for argument '%s', " \
            "expected %s." % (arg, name, expected)
        Error.__init__(self, 400, message)

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
    try:
        value = int(arg)
    except ValueError:
        raise InvalidArgumentError(arg, name, expected="a positive integer")
    else:
        if value < 0:
            raise InvalidArgumentError(arg, name, expected="a positive integer")
    return value

def _get_choice_arg(name, choices):
    arg = flask.request.args.get(name, "")
    arg = arg if arg else choices[0]
    if arg not in choices:
        raise InvalidArgumentError(arg, name,
                                   expected=" or ".join([repr(s) for s in choices]))
    return arg

def _jsonified_resource(model_class=None, resource_mapper=None, model_id=None, sortable_fields=()):
    if model_id is not None:
        resource = resource_mapper(model_class.query.get_or_404(model_id))
        return flask.jsonify(**resource)

    limit = min(_get_uint_arg("limit", 20), 1000)
    offset = _get_uint_arg("offset", 0)

    total_count = 0
    objects = []

    if model_class is not None:
        models = model_class.query.limit(limit).offset(offset).all()
        total_count = model_class.query.count()
        objects = [resource_mapper(m) for m in models]

    if sortable_fields:
        choices = []
        for field in sortable_fields:
            choices.append(field)
            choices.append("-%s" % field)
        order_by_arg = _get_choice_arg("order_by", choices)
        is_descending = order_by_arg.startswith("-")
        field = order_by_arg.lstrip("-")
        objects.sort(key=lambda o: o[field], reverse=is_descending)

    next_path = None
    prev_path = None

    if limit + offset < total_count:
        next_path_args = flask.request.args.to_dict()
        next_path_args["offset"] = offset + limit
        next_path = "%s?%s" % (flask.request.path, urllib.urlencode(next_path_args))

    if offset > 0:
        prev_path_args = flask.request.args.to_dict()
        prev_path_args["offset"] = max(offset - limit, 0)
        prev_path = "%s?%s" % (flask.request.path, urllib.urlencode(prev_path_args))

    resource = {
        "meta": {
            "limit": limit,
            "next": next_path,
            "offset": offset,
            "previous": prev_path,
            "total_count": total_count,
            },
        "objects": objects,
        }

    return flask.jsonify(**resource)

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

@v0.route("/policymaker/")
@v0.route("/policymaker/<int:policymaker_id>/")
def _policymaker_route(policymaker_id=None):
    return _jsonified_resource(klupung.models.Policymaker,
                              _policymaker_resource,
                              policymaker_id,
                              ["name"])

@v0.route("/meeting/")
@v0.route("/meeting/<int:meeting_id>/")
def _meeting_route(meeting_id=None):
    return _jsonified_resource(klupung.models.Meeting,
                              _meeting_resource,
                              meeting_id,
                              ["date", "policymaker"])

@v0.route("/meeting_document/")
@v0.route("/meeting_document/<int:meeting_document_id>/")
def _meeting_document_route(meeting_document_id=None):
    return _jsonified_resource(klupung.models.MeetingDocument,
                              _meeting_document_resource,
                              meeting_document_id)

@v0.route("/category/")
def _category_route():
    return _jsonified_resource()

@v0.route("/video/")
def _video_route():
    return _jsonified_resource()

@v0.route("/district/")
def _district_route():
    return _jsonified_resource()

@v0.route("/attachment/")
def _attachment_route():
    return _jsonified_resource()

@v0.errorhandler(Error)
def _errorhandler(error):
    return flask.jsonify(error=error.message), error.code
