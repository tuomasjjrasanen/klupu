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
import urllib

## 3rd party imports
import flask
import flask.ext.autodoc

## Local imports
import klupung.flask.models

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

class UnknownArgumentError(Error):
    """Raised when a client has provided an unknown query argument."""

    def __init__(self, name):
        message = "Unknown argument '%s'." % name
        Error.__init__(self, 400, message)

_STRFMT_DATETIME = "%Y-%m-%dT%H:%M:%S.%f"
_STRFMT_DATE = "%Y-%m-%d"

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

def _get_order_by_arg(sortable_fields):
    choices = []
    for field in sortable_fields:
        choices.append(field)
        choices.append("-%s" % field)
    order_by_arg = _get_choice_arg("order_by", choices)
    is_descending = order_by_arg.startswith("-")
    column_name = order_by_arg.lstrip("-")

    return column_name, is_descending

def _jsonified_query_results(query, get_resource):
    meta = {
        "criterion": flask.request.query_string,
        }

    resource = {
        "meta"   : meta,
        "objects": [get_resource(model) for model in query.all()],
        }

    return flask.jsonify(**resource)

def _jsonified_resource(model_class, get_resource, primary_key):
    resource = get_resource(model_class.query.get_or_404(primary_key))
    return flask.jsonify(**resource)

def _encode_args(in_dict):
    out_dict = {}
    for k, v in in_dict.iteritems():
        if isinstance(v, unicode):
            v = v.encode('utf-8')
        elif isinstance(v, str):
            v.decode('utf-8')
        out_dict[k] = v
    return out_dict

def _jsonified_resource_list(model_class, get_resource,
                             sortable_fields=(), do_paginate=False,
                             query=None):
    limit = min(_get_uint_arg("limit", 20), 1000)
    offset = _get_uint_arg("offset", 0)

    if do_paginate:
        page = max(_get_uint_arg("page", 1), 1)
        offset = limit * (page - 1)

    total_count = 0
    objects = []

    if query is None:
        query = model_class.query

    total_count = query.count()

    if sortable_fields:
        column_name, is_descending = _get_order_by_arg(sortable_fields)

        relationship_name, _, related_column_name = column_name.partition("__")
        if related_column_name != '':
            relationship = getattr(model_class, relationship_name)
            query = query.join(relationship)
            column = relationship.property.table.columns[related_column_name]
        else:
            column = getattr(model_class, column_name)

        if is_descending:
            column = column.desc()

        query = query.order_by(column)

    query = query.limit(limit).offset(offset)

    objects = [get_resource(model) for model in query.all()]

    next_path = None
    prev_path = None

    if limit + offset < total_count:
        next_path_args = _encode_args(flask.request.args.to_dict())
        next_path_args["offset"] = offset + limit
        next_path = "%s?%s" % (flask.request.path, urllib.urlencode(next_path_args))

    if offset > 0:
        prev_path_args = _encode_args(flask.request.args.to_dict())
        prev_path_args["offset"] = max(offset - limit, 0)
        prev_path = "%s?%s" % (flask.request.path, urllib.urlencode(prev_path_args))

    if do_paginate:
        meta = {
            "limit"       : limit,
            "total_count" : total_count,
            "page"        : page,
            }
    else:
        meta = {
            "limit"       : limit,
            "next"        : next_path,
            "offset"      : offset,
            "previous"    : prev_path,
            "total_count" : total_count,
            }

    resource = {
        "meta"   : meta,
        "objects": objects,
        }

    return flask.jsonify(**resource)

def _get_agenda_item_contents(agenda_item):
    query = klupung.flask.models.Content.query
    contents = query.filter_by(agenda_item_id=agenda_item.id).order_by(klupung.flask.models.Content.index).all()
    for content in contents:
        yield {"type": content.content_type, "text": content.text}

def _get_agenda_item_resource(agenda_item):
    origin_last_modified_time = agenda_item.last_modified_time.strftime(_STRFMT_DATETIME)
    if agenda_item.origin_last_modified_time:
        origin_last_modified_time = agenda_item.origin_last_modified_time.strftime(_STRFMT_DATETIME)
    return {
        "attachments"                : [],
        "classification_code"        : "",
        "classification_description" : "",
        "content"                    : list(_get_agenda_item_contents(agenda_item)),
        "from_minutes"               : True,
        "id"                         : agenda_item.id,
        "index"                      : agenda_item.index,
        "introducer"                 : agenda_item.introducer,
        "issue"                      : _get_issue_resource(agenda_item.issue) if agenda_item.issue else {},
        "last_modified_time"         : agenda_item.last_modified_time.strftime(_STRFMT_DATETIME),
        "meeting"                    :  _get_meeting_resource(agenda_item.meeting),
        "origin_last_modified_time"  : origin_last_modified_time,
        "permalink"                  : agenda_item.permalink,
        "preparer"                   : agenda_item.preparer,
        "resolution"                 : agenda_item.resolution,
        "resource_uri"               : flask.url_for("._agenda_item_id_route",
                                                     agenda_item_id=agenda_item.id),
        "subject"                    : agenda_item.subject,
        }

def _get_category_resource(category):
    parent_uri = None
    if category.parent_id is not None:
        parent_uri = flask.url_for("._category_id_route",
                                   category_id=category.parent_id)

    return {
        "id"          : category.id,
        "level"       : category.level,
        "name"        : category.name,
        "origin_id"   : category.origin_id,
        "parent"      : parent_uri,
        "resource_uri": flask.url_for("._category_id_route",
                                      category_id=category.id),
        }

def _get_issue_resource(issue):
    geometries = []
    for agenda_item in issue.agenda_items:
        for geometry in agenda_item.geometries:
            geometries.append({
                    "name": geometry.name,
                    "type": geometry.type,
                    "category": geometry.category,
                    "coordinates": geometry.coordinates,
                    })
    return {
        "category"            : flask.url_for("._category_id_route",
                                              category_id=issue.category_id),
        "category_name"       : issue.category.name,
        "category_origin_id"  : issue.category.origin_id,
        "districts"           : [],
        "geometries"          : geometries,
        "id"                  : issue.id,
        "last_modified_time"  : issue.last_modified_time.strftime(_STRFMT_DATETIME),
        "latest_decision_date": issue.latest_decision_date.strftime(_STRFMT_DATETIME),
        "reference_text"      : "",
        "register_id"         : issue.register_id,
        "slug"                : issue.slug,
        "subject"             : issue.subject,
        "summary"             : issue.summary,
        "top_category_name"   : issue.category.find_top_category().name,
        "resource_uri"        : flask.url_for("._issue_id_route",
                                              issue_id=issue.id),
        }

def _get_policymaker_resource(policymaker):
    return {
        "id"          : policymaker.id,
        "abbreviation": policymaker.abbreviation,
        "name"        : policymaker.name,
        "origin_id"   : policymaker.abbreviation,
        "slug"        : policymaker.slug,
        "summary"     : policymaker.summary,
        "resource_uri": flask.url_for("._policymaker_id_route",
                                      policymaker_id=policymaker.id),
        }

def _get_meeting_resource(meeting):
    return {
        "id"              : meeting.id,
        "date"            : meeting.date.strftime(_STRFMT_DATE),
        "minutes"         : True,
        "number"          : meeting.number,
        "policymaker"     : flask.url_for("._policymaker_id_route",
                                          policymaker_id=meeting.policymaker.id),
        "policymaker_name": meeting.policymaker.name,
        "year"            : meeting.date.year,
        "resource_uri"    : flask.url_for("._meeting_id_route",
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
        "resource_uri"       : flask.url_for("._meeting_document_id_route",
                                             meeting_document_id=meeting_document.id)
    }

auto = flask.ext.autodoc.Autodoc()
v0 = flask.Blueprint("v0", __name__, url_prefix="/v1")

@v0.route("/")
def _index():
    return auto.html()

@v0.route("/agenda_item/filter/")
def _agenda_item_filter_route():
    """Return a filtered list of agenda_items.

    GET parameters:
        issue__id.eq - filter by issue id
    """
    query = klupung.flask.models.AgendaItem.query

    known_args = set([
            "issue__id.eq",
            ])

    unknown_args = set(flask.request.args.keys()) - known_args
    if unknown_args:
        raise UnknownArgumentError(unknown_args.pop())

    try:
        issue_id = int(flask.request.args["issue__id.eq"])
    except KeyError:
        pass
    except ValueError:
        raise InvalidArgumentError(flask.request.args["issue__id.eq"], "issue__id.eq",
                                   expected="an integer value")
    else:
        query = query.join(klupung.flask.models.Issue)
        query = query.filter(klupung.flask.models.Issue.id == issue_id)

    return _jsonified_query_results(query, _get_agenda_item_resource)

@v0.route("/agenda_item/")
@auto.doc()
def _agenda_item_route():
    """Return a list of agenda items of a meeting.

    GET parameters:
        limit    - the maximum number of objects to return
        offset   - the number of objects to skip from the beginning of the result set
        order_by - the name of field by which the results are ordered
        meeting  - the id of the meeting whose agenda items should be returned
    """

    query = klupung.flask.models.AgendaItem.query

    try:
        meeting_id = int(flask.request.args["meeting"])
    except KeyError:
        pass
    except ValueError:
        raise InvalidArgumentError(flask.request.args["meeting"], "meeting",
                                   expected="an integer value")
    else:
        query = query.join(klupung.flask.models.Meeting)
        query = query.filter(klupung.flask.models.Meeting.id == meeting_id)

    return _jsonified_resource_list(
        klupung.flask.models.AgendaItem,
        _get_agenda_item_resource,
        sortable_fields=["last_modified_time",
                         "origin_last_modified_time",
                         "meeting__date",
                         "index"],
        query=query)

@v0.route("/agenda_item/<int:agenda_item_id>/")
@auto.doc()
def _agenda_item_id_route(agenda_item_id):
    """Return an agenda item of a meeting by an id."""
    return _jsonified_resource(
        klupung.flask.models.AgendaItem,
        _get_agenda_item_resource,
        agenda_item_id)

@v0.route("/policymaker/")
@auto.doc()
def _policymaker_route():
    """Return a list of policymakers.

    GET parameters:
        limit    - the maximum number of objects to return
        offset   - the number of objects to skip from the beginning of the result set
        order_by - the name of field by which the results are ordered
    """
    return _jsonified_resource_list(
        klupung.flask.models.Policymaker,
        _get_policymaker_resource,
        sortable_fields=["name"])

@v0.route("/policymaker/<int:policymaker_id>/")
@auto.doc()
def _policymaker_id_route(policymaker_id):
    """Return a policymaker by an id."""
    return _jsonified_resource(
        klupung.flask.models.Policymaker,
        _get_policymaker_resource,
        policymaker_id)

@v0.route("/issue/search/")
@auto.doc()
def _issue_search_route():
    """Return a list of issues.

    GET parameters:
        limit       - the maximum number of objects to return
        offset      - the number of objects to skip from the beginning of the result set
        order_by    - the name of field by which the results are ordered
        page        - the number of the page
        text        - filter results by matching text contents
        policymaker - filter results by matching policymaker id
    """

    query = klupung.flask.models.Issue.query

    try:
        bbox = flask.request.args["bbox"]
    except KeyError:
        pass
    else:
        query = query.join(klupung.flask.models.AgendaItem, klupung.flask.models.AgendaItemGeometry)
        query = query.filter(klupung.flask.models.AgendaItemGeometry.type.like("Point"))
        query = query.distinct()

    try:
        text = flask.request.args["text"]
    except KeyError:
        pass
    else:
        query = query.join(klupung.flask.models.AgendaItem, klupung.flask.models.Content)
        query = query.filter(
            (klupung.flask.models.Content.text.like("%%%s%%" % text))
            |
            (klupung.flask.models.AgendaItem.subject.like("%%%s%%" % text)))
        query = query.distinct()

    try:
        policymaker_ids = [int(v) for v in flask.request.args["policymaker"].split(",")]
    except KeyError:
        pass
    except ValueError:
        raise InvalidArgumentError(flask.request.args["policymaker"], "policymaker",
                                   expected="one or more comma-separated integers")
    else:
        query = query.join(klupung.flask.models.AgendaItem, klupung.flask.models.Meeting)
        query = query.filter(klupung.flask.models.Meeting.policymaker_id.in_(policymaker_ids))
        query = query.distinct()

    return _jsonified_resource_list(
        klupung.flask.models.Issue,
        _get_issue_resource,
        sortable_fields=["latest_decision_date"],
        do_paginate=True,
        query=query)

@v0.route("/policymaker/filter/")
def _policymaker_filter_route():
    """Return a filtered list of policymakers.

    GET parameters:
        abbreviation.isnull - false/true to filter by abbreviation
        slug.eq             - filter by slug
    """

    query = klupung.flask.models.Policymaker.query

    known_args = set([
            "abbreviation.isnull",
            "slug.eq",
            ])

    unknown_args = set(flask.request.args.keys()) - known_args
    if unknown_args:
        raise UnknownArgumentError(unknown_args.pop())

    try:
        abbreviation_isnull = flask.request.args["abbreviation.isnull"]
    except KeyError:
        pass
    else:
        if abbreviation_isnull == "false":
            query = query.filter(klupung.flask.models.Policymaker.abbreviation is not None)
        elif abbreviation_isnull == "true":
            query = query.filter(klupung.flask.models.Policymaker.abbreviation is None)
        else:
            raise InvalidArgumentError(abbreviation_isnull, "abbreviation.isnull",
                                       expected="true or false")

    try:
        slug = flask.request.args["slug.eq"]
    except KeyError:
        pass
    else:
        query = query.filter(klupung.flask.models.Policymaker.slug == slug)

    return _jsonified_query_results(query, _get_policymaker_resource)

@v0.route("/issue/filter/")
def _issue_filter_route():
    """Return a filtered list of issues.

    GET parameters:
        slug.eq - filter by slug
    """

    query = klupung.flask.models.Issue.query

    known_args = set([
            "slug.eq",
            ])

    unknown_args = set(flask.request.args.keys()) - known_args
    if unknown_args:
        raise UnknownArgumentError(unknown_args.pop())

    try:
        slug = flask.request.args["slug.eq"]
    except KeyError:
        pass
    else:
        query = query.filter(klupung.flask.models.Issue.slug == slug)

    return _jsonified_query_results(query, _get_issue_resource)

@v0.route("/issue/")
@auto.doc()
def _issue_route():
    """Return a list of issues.

    GET parameters:
        limit    - the maximum number of objects to return
        offset   - the number of objects to skip from the beginning of the result set
        order_by - the name of field by which the results are ordered
    """
    return _jsonified_resource_list(
        klupung.flask.models.Issue,
        _get_issue_resource,
        sortable_fields=["last_modified_time", "latest_decision_date"])

@v0.route("/issue/<int:issue_id>/")
@auto.doc()
def _issue_id_route(issue_id):
    """Return an issue by an id."""
    return _jsonified_resource(
        klupung.flask.models.Issue,
        _get_issue_resource,
        issue_id)

@v0.route("/meeting/")
@auto.doc()
def _meeting_route():
    """Return a list of meetings.

    GET parameters:
        limit       - the maximum number of objects to return
        offset      - the number of objects to skip from the beginning of the result set
        order_by    - the name of field by which the results are ordered
        policymaker - the id of the policymaker whose meetings should be returned
    """

    query = klupung.flask.models.Meeting.query

    try:
        policymaker_id = int(flask.request.args["policymaker"])
    except KeyError:
        pass
    except ValueError:
        raise InvalidArgumentError(flask.request.args["policymaker"], "policymaker",
                                   expected="an integer value")
    else:
        query = query.join(klupung.flask.models.Policymaker)
        query = query.filter(klupung.flask.models.Policymaker.id == policymaker_id)

    return _jsonified_resource_list(
        klupung.flask.models.Meeting,
        _get_meeting_resource,
        sortable_fields=["date", "policymaker"],
        query=query)

@v0.route("/meeting/<int:meeting_id>/")
@auto.doc()
def _meeting_id_route(meeting_id):
    """Return a meeting by an id."""
    return _jsonified_resource(
        klupung.flask.models.Meeting,
        _get_meeting_resource,
        meeting_id)

@v0.route("/meeting_document/")
@auto.doc()
def _meeting_document_route():
    """Return a list of meeting documents.

    GET parameters:
        limit    - the maximum number of objects to return
        offset   - the number of objects to skip from the beginning of the result set
        order_by - the name of field by which the results are ordered
    """
    return _jsonified_resource_list(
        klupung.flask.models.MeetingDocument,
        _get_meeting_document_resource)

@v0.route("/meeting_document/<int:meeting_document_id>/")
@auto.doc()
def _meeting_document_id_route(meeting_document_id):
    """Return a meeting document by an id."""
    return _jsonified_resource(
        klupung.flask.models.MeetingDocument,
        _get_meeting_document_resource,
        meeting_document_id)

@v0.route("/category/filter/")
def _category_filter_route():
    """Return a filtered list of categorys.

    GET parameters:
        level.lte - filter by level
    """

    query = klupung.flask.models.Category.query

    known_args = set([
            "level.lte",
            ])

    unknown_args = set(flask.request.args.keys()) - known_args
    if unknown_args:
        raise UnknownArgumentError(unknown_args.pop())

    try:
        level = int(flask.request.args["level.lte"])
    except KeyError:
        pass
    except ValueError:
        raise InvalidArgumentError(flask.request.args["level.lte"], "level.lte",
                                   expected="an integer value")
    else:
        query = query.filter(klupung.flask.models.Category.level <= level)

    return _jsonified_query_results(query, _get_category_resource)

@v0.route("/category/")
@auto.doc()
def _category_route():
    """Return a list of issue categories.

    GET parameters:
        limit    - the maximum number of objects to return
        offset   - the number of objects to skip from the beginning of the result set
        order_by - the name of field by which the results are ordered
    """
    return _jsonified_resource_list(
        klupung.flask.models.Category,
        _get_category_resource)

@v0.route("/category/<int:category_id>")
@auto.doc()
def _category_id_route(category_id):
    """Return an issue category by an id."""
    return _jsonified_resource(
        klupung.flask.models.Category,
        _get_category_resource,
        category_id)

@v0.route("/video/")
@auto.doc()
def _video_route():
    """Return a list of meeting videos.

    GET parameters:
        limit    - the maximum number of objects to return
        offset   - the number of objects to skip from the beginning of the result set
        order_by - the name of field by which the results are ordered
    """
    return _jsonified_resource_list()

@v0.route("/district/")
@auto.doc()
def _district_route():
    """Return a list of districts related to an issue.

    GET parameters:
        limit    - the maximum number of objects to return
        offset   - the number of objects to skip from the beginning of the result set
        order_by - the name of field by which the results are ordered
    """
    return _jsonified_resource_list()

@v0.route("/attachment/")
@auto.doc()
def _attachment_route():
    """Return a list of attachments of a meeting document.

    GET parameters:
        limit    - the maximum number of objects to return
        offset   - the number of objects to skip from the beginning of the result set
        order_by - the name of field by which the results are ordered
    """
    return _jsonified_resource_list()

@v0.errorhandler(Error)
def _errorhandler(error):
    return flask.jsonify(error=error.message), error.code
