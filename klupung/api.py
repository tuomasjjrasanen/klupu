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

## Standard library imports
import datetime
import re
import unicodedata
import urllib

## 3rd party imports
import flask
import flask.ext.autodoc

## Local imports
import klupung.models

class Error(Exception):
    """Common base class for all API-related exceptions."""

    def __init__(self, code, message):
        self.code = code
        self.message = message

class InvalidArgumentError(Error):
    """Raised when a client has provided an invalid query argument."""

    def __init__(self, arg, name, expected=""):
        message = "Invalid value '%s' for argument '%s', " \
            "expected %s." % (arg, name, expected)
        Error.__init__(self, 400, message)

_STRFMT_DATETIME = "%Y-%m-%dT%H:%M:%S.%f"
_STRFMT_DATE = "%Y-%m-%d"

_SLUG_PUNCT_RE = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

def _slugify(text, delim=u'-'):
    """Return an unicode slug of the text"""
    result = []
    for word in _SLUG_PUNCT_RE.split(text.lower()):
        word = unicodedata.normalize('NFKD', word).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return unicode(delim.join(result))

def _get_uint_arg(name, default):
    """Return `int` value of argument `name` from the current request

    If the current request does not have argument `name`, `default`
    value is returned instead. Raises `InvalidArgumentError` if the
    value (or `default` value if it is used) is not a positive integer.

    """

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
    """Return `str` value of argument `name` from the current request

    If the current request does not have argument `name`, the first item
    from `choices` sequence is returned. Raises `InvalidArgumentError`
    if the value is not listed in `choices`.

    """

    arg = flask.request.args.get(name, "")
    arg = arg if arg else choices[0]
    if arg not in choices:
        raise InvalidArgumentError(arg, name,
                                   expected=" or ".join([repr(s) for s in choices]))
    return arg

def _jsonified_resource(model_class=None, get_resource=None, model_id=None, sortable_fields=()):
    if model_id is not None:
        resource = get_resource(model_class.query.get_or_404(model_id))
        return flask.jsonify(**resource)

    limit = min(_get_uint_arg("limit", 20), 1000)
    offset = _get_uint_arg("offset", 0)

    total_count = 0
    objects = []

    if model_class is not None:
        models = model_class.query.limit(limit).offset(offset).all()
        total_count = model_class.query.count()
        objects = [get_resource(m) for m in models]

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
            "limit"       : limit,
            "next"        : next_path,
            "offset"      : offset,
            "previous"    : prev_path,
            "total_count" : total_count,
            },
        "objects": objects,
        }

    return flask.jsonify(**resource)

def _get_agenda_item_resource(agenda_item):
    return {
        "attachments"                : [],
        "classification_code"        : "",
        "classification_description" : "",
        "content"                    : [],
        "from_minutes"               : True,
        "id"                         : agenda_item.id,
        "index"                      : agenda_item.index,
        "introducer"                 : agenda_item.introducer,
        "issue"                      : _get_issue_resource(agenda_item.issue) if agenda_item.issue else {},
        "last_modified_time"         : agenda_item.last_modified_time.strftime(_STRFMT_DATETIME),
        "meeting"                    :  _get_meeting_resource(agenda_item.meeting),
        "meeting__date"              : agenda_item.meeting.start_datetime.strftime(_STRFMT_DATE),
        "origin_last_modified_time"  : agenda_item.origin_last_modified_time.strftime(_STRFMT_DATETIME),
        "permalink"                  : agenda_item.permalink,
        "preparer"                   : agenda_item.preparer,
        "resolution"                 : agenda_item.resolution,
        "resource_uri"               : flask.url_for("._agenda_item_route",
                                                     agenda_item_id=agenda_item.id),
        "subject"                    : agenda_item.subject,
        }

def _get_top_category(category):
    if category.parent:
        _top_category(category.parent)
    return category

def _get_category_resource(category):
    parent_uri = None
    if category.parent_id is not None:
        parent_uri = flask.url_for("._category_route",
                                   category_id=category.parent_id)

    return {
        "id"          : category.id,
        "level"       : category.level,
        "name"        : category.name,
        "origin_id"   : category.origin_id,
        "parent"      : parent_uri,
        "resource_uri": flask.url_for("._category_route",
                                      category_id=category.id),
        }

def _get_issue_resource(issue):
    return {
        "category"            : flask.url_for("._category_route",
                                              category_id=issue.category_id),
        "category_name"       : issue.category.name,
        "category_origin_id"  : issue.category.origin_id,
        "districts"           : [],
        "geometries"          : [],
        "id"                  : issue.id,
        "last_modified_time"  : issue.last_modified_time.strftime(_STRFMT_DATETIME),
        "latest_decision_date": sorted([ai.meeting.start_datetime for ai in issue.agenda_items])[0].strftime(_STRFMT_DATE),
        "reference_text"      : "",
        "register_id"         : issue.register_id,
        "slug"                : _slugify(issue.register_id),
        "subject"             : issue.subject,
        "summary"             : issue.summary,
        "top_category_name"   : _get_top_category(issue.category).name,
        "resource_uri"        : flask.url_for("._issue_route",
                                              issue_id=issue.id),
        }

def _get_policymaker_resource(policymaker):
    return {
        "id"          : policymaker.id,
        "abbreviation": policymaker.abbreviation,
        "name"        : policymaker.name,
        "origin_id"   : policymaker.abbreviation,
        "slug"        : _slugify(policymaker.abbreviation),
        "summary"     : None,
        "resource_uri": flask.url_for("._policymaker_route",
                                      policymaker_id=policymaker.id),
        }

def _get_meeting_resource(meeting):
    return {
        "id"              : meeting.id,
        "date"            : meeting.start_datetime.strftime(_STRFMT_DATE),
        "minutes"         : True,
        "number"          : 1,
        "policymaker"     : flask.url_for("._policymaker_route",
                                          policymaker_id=meeting.policymaker.id),
        "policymaker_name": meeting.policymaker.name,
        "year"            : meeting.start_datetime.year,
        "resource_uri"    : flask.url_for("._meeting_route",
                                          meeting_id=meeting.id),
        }

def _get_meeting_document_resource(meeting_document):
    return {
        "id"                 : meeting_document.id,
        "last_modified_time" : meeting_document.publish_datetime.strftime(_STRFMT_DATETIME),
        "meeting"            : _get_meeting_resource(meeting_document.meeting),
        "organisation"       : None,
        "origin_id"          : meeting_document.origin_id,
        "origin_url"         : meeting_document.origin_url,
        "publish_time"       : meeting_document.publish_datetime.strftime(_STRFMT_DATETIME),
        "type"               : "minutes",
        "xml_uri"            : None,
        "resource_uri"       : flask.url_for("._meeting_document_route",
                                             meeting_document_id=meeting_document.id)
    }

auto = flask.ext.autodoc.Autodoc()
v0 = flask.Blueprint("v0", __name__, url_prefix="/v1")

@v0.route("/")
def _index():
    return auto.html()

@v0.route("/agenda_item/")
@auto.doc()
def _agenda_items_route():
    """Return a list of agenda items of a meeting.

    GET parameters:
        limit    - the maximum number of objects to return
        offset   - the number of objects to skip from the beginning of the result set
        order_by - the name of field by which the results are ordered
    """
    return _jsonified_resource(
        model_class=klupung.models.AgendaItem,
        get_resource=_get_agenda_item_resource,
        sortable_fields=["last_modified_time",
                         "origin_last_modified_time",
                         "meeting__date",
                         "index"])

@v0.route("/agenda_item/<int:agenda_item_id>/")
@auto.doc()
def _agenda_item_route(agenda_item_id):
    """Return an agenda item of a meeting by an id."""
    return _jsonified_resource(
        model_class=klupung.models.AgendaItem,
        get_resource=_get_agenda_item_resource,
        model_id=agenda_item_id)

@v0.route("/policymaker/")
@auto.doc()
def _policymakers_route():
    """Return a list of policymakers.

    GET parameters:
        limit    - the maximum number of objects to return
        offset   - the number of objects to skip from the beginning of the result set
        order_by - the name of field by which the results are ordered
    """
    return _jsonified_resource(
        model_class=klupung.models.Policymaker,
        get_resource=_get_policymaker_resource,
        sortable_fields=["name"])

@v0.route("/policymaker/<int:policymaker_id>/")
@auto.doc()
def _policymaker_route(policymaker_id):
    """Return a policymaker by an id."""
    return _jsonified_resource(
        model_class=klupung.models.Policymaker,
        get_resource=_get_policymaker_resource,
        model_id=policymaker_id)

@v0.route("/issue/search/")
@v0.route("/issue/")
@auto.doc()
def _issues_route():
    """Return a list of issues.

    GET parameters:
        limit    - the maximum number of objects to return
        offset   - the number of objects to skip from the beginning of the result set
        order_by - the name of field by which the results are ordered
    """
    return _jsonified_resource(
        model_class=klupung.models.Issue,
        get_resource=_get_issue_resource,
        sortable_fields=["last_modified_time", "latest_decision_date"])

@v0.route("/issue/<int:issue_id>/")
@auto.doc()
def _issue_route(issue_id):
    """Return an issue by an id."""
    return _jsonified_resource(
        model_class=klupung.models.Issue,
        get_resource=_get_issue_resource,
        model_id=issue_id)

@v0.route("/meeting/")
@auto.doc()
def _meetings_route():
    """Return a list of meetings.

    GET parameters:
        limit    - the maximum number of objects to return
        offset   - the number of objects to skip from the beginning of the result set
        order_by - the name of field by which the results are ordered
    """
    return _jsonified_resource(
        model_class=klupung.models.Meeting,
        get_resource=_get_meeting_resource,
        sortable_fields=["date", "policymaker"])

@v0.route("/meeting/<int:meeting_id>/")
@auto.doc()
def _meeting_route(meeting_id):
    """Return a meeting by an id."""
    return _jsonified_resource(
        model_class=klupung.models.Meeting,
        get_resource=_get_meeting_resource,
        model_id=meeting_id)

@v0.route("/meeting_document/")
@auto.doc()
def _meeting_documents_route():
    """Return a list of meeting documents.

    GET parameters:
        limit    - the maximum number of objects to return
        offset   - the number of objects to skip from the beginning of the result set
        order_by - the name of field by which the results are ordered
    """
    return _jsonified_resource(
        model_class=klupung.models.MeetingDocument,
        get_resource=_get_meeting_document_resource)

@v0.route("/meeting_document/<int:meeting_document_id>/")
@auto.doc()
def _meeting_document_route(meeting_document_id):
    """Return a meeting document by an id."""
    return _jsonified_resource(
        model_class=klupung.models.MeetingDocument,
        get_resource=_get_meeting_document_resource,
        model_id=meeting_document_id)

@v0.route("/category/")
@auto.doc()
def _categories_route():
    """Return a list of issue categories.

    GET parameters:
        limit    - the maximum number of objects to return
        offset   - the number of objects to skip from the beginning of the result set
        order_by - the name of field by which the results are ordered
    """
    return _jsonified_resource(
        model_class=klupung.models.Category,
        get_resource=_get_category_resource)

@v0.route("/category/<int:category_id>")
@auto.doc()
def _category_route(category_id):
    """Return an issue category by an id."""
    return _jsonified_resource(
        model_class=klupung.models.Category,
        get_resource=_get_category_resource,
        model_id=category_id)

@v0.route("/video/")
@auto.doc()
def _video_route():
    """Return a list of meeting videos.

    GET parameters:
        limit    - the maximum number of objects to return
        offset   - the number of objects to skip from the beginning of the result set
        order_by - the name of field by which the results are ordered
    """
    return _jsonified_resource()

@v0.route("/district/")
@auto.doc()
def _district_route():
    """Return a list of districts related to an issue.

    GET parameters:
        limit    - the maximum number of objects to return
        offset   - the number of objects to skip from the beginning of the result set
        order_by - the name of field by which the results are ordered
    """
    return _jsonified_resource()

@v0.route("/attachment/")
@auto.doc()
def _attachment_route():
    """Return a list of attachments of a meeting document.

    GET parameters:
        limit    - the maximum number of objects to return
        offset   - the number of objects to skip from the beginning of the result set
        order_by - the name of field by which the results are ordered
    """
    return _jsonified_resource()

@v0.errorhandler(Error)
def _errorhandler(error):
    return flask.jsonify(error=error.message), error.code
