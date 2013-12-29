import datetime
import json

import flask

import klupung.db
klupung.db.init_session("sqlite:///klupung.db")

import klupung.models

app = flask.Flask(__name__)
app.config["DEBUG"] = True

def policymaker_resource(policymaker):
    return {
        "id": policymaker.id,
        "abbreviation": policymaker.abbreviation,
        "name": None,
        "origin_id": None,
        "slug": None,
        "summary": None,
        "resource_uri": flask.url_for("policymaker_route",
                                      policymaker_id=policymaker.id),
        }

@app.route("/policymaker/")
def policymakers_route():
    return "list of policymakers"

@app.route("/policymaker/<int:policymaker_id>/")
def policymaker_route(policymaker_id=None):
    policymaker = klupung.models.Policymaker.query.get(policymaker_id)
    if not policymaker:
        return flask.make_response("invalid policymaker id", 404)

    resource = policymaker_resource(policymaker)

    return flask.jsonify(**resource)

def meeting_resource(meeting):
    return {
        "id": meeting.id,
        "date": str(meeting.date),
        "minutes": True,
        "number": 1,
        "policymaker": flask.url_for("policymaker_route",
                                     policymaker_id=meeting.policymaker.id),
        "policymaker_name": None,
        "year": meeting.date.year,
        "resource_uri": flask.url_for("meeting_route", meeting_id=meeting.id),
        }

@app.route("/meeting/")
def meetings_route():
    return "list of meetings"

@app.route("/meeting/<int:meeting_id>/")
def meeting_route(meeting_id=None):
    meeting = klupung.models.Meeting.query.get(meeting_id)
    if not meeting:
        return flask.make_response("invalid meeting id", 404)

    resource = meeting_resource(meeting)

    return flask.jsonify(**resource)

def meeting_document_resource(meeting_document):
    return {
        "id": meeting_document.id,
        "last_modified_time": None,
        "meeting": meeting_resource(meeting_document.meeting),
        "organisation": None,
        "origin_id": None,
        "origin_url": meeting_document.origin_url,
        "publish_time": None,
        "type": "minutes",
        "xml_uri": None,
        "resource_uri": flask.url_for("meeting_document_route",
                                      meeting_document_id=meeting_document.id)
        }

@app.route("/meeting_document/")
def meeting_documents_route():
    return "list of meeting documents"

@app.route("/meeting_document/<int:meeting_document_id>/")
def meeting_document_route(meeting_document_id=None):
    meeting_document = klupung.models.MeetingDocument.query.get(meeting_document_id)
    if not meeting_document:
        return flask.make_response("invalid meeting document id", 404)

    resource = meeting_document_resource(meeting_document)

    return flask.jsonify(**resource)

if __name__ == "__main__":
    app.run()
