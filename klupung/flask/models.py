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

import klupung

_SLUG_PUNCT_RE = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

def _slugify(text, delim=u'-'):
    """Return an unicode slug of the text"""
    result = []
    for word in _SLUG_PUNCT_RE.split(text.lower()):
        word = unicodedata.normalize('NFKD', word).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return unicode(delim.join(result))

class AgendaItem(klupung.flask.db.Model):
    RESOLUTIONS = (
        RESOLUTION_PASSED,
        RESOLUTION_PASSED_VOTED,
        RESOLUTION_PASSED_REVISED,
        RESOLUTION_PASSED_MODIFIED,
        RESOLUTION_REJECTED,
        RESOLUTION_NOTED,
        RESOLUTION_RETURNED,
        RESOLUTION_REMOVED,
        RESOLUTION_TABLED,
        RESOLUTION_ELECTION,
        ) = (
        "PASSED_UNCHANGED",
        "PASSED_VOTED",
        "PASSED_REVISED",
        "PASSED_MODIFIED",
        "REJECTED",
        "NOTED",
        "RETURNED",
        "REMOVED",
        "TABLED",
        "ELECTION"
        )

    __tablename__ = "agenda_item"

    # Columns
    id = klupung.flask.db.Column(
        klupung.flask.db.Integer,
        primary_key=True,
        )
    subject = klupung.flask.db.Column(
        klupung.flask.db.String(500),
        nullable=False,
        )
    issue_id = klupung.flask.db.Column(
        klupung.flask.db.Integer,
        klupung.flask.db.ForeignKey("issue.id"),
        )
    meeting_id = klupung.flask.db.Column(
        klupung.flask.db.Integer,
        klupung.flask.db.ForeignKey("meeting.id"),
        nullable=False,
        )
    index = klupung.flask.db.Column(
        klupung.flask.db.Integer,
        nullable=False,
        )
    introducer = klupung.flask.db.Column(
        klupung.flask.db.String(100),
        )
    preparer = klupung.flask.db.Column(
        klupung.flask.db.String(100),
        )
    last_modified_time = klupung.flask.db.Column(
        klupung.flask.db.DateTime,
        default=klupung.flask.db.func.now(),
        onupdate=klupung.flask.db.func.now(),
        nullable=False,
        )
    origin_last_modified_time = klupung.flask.db.Column(
        klupung.flask.db.DateTime,
        )
    permalink = klupung.flask.db.Column(
        klupung.flask.db.String(500),
        nullable=False,
        )
    resolution = klupung.flask.db.Column(
        klupung.flask.db.Enum(*RESOLUTIONS),
        nullable=False,
        )

    # Relationships
    contents = klupung.flask.db.relationship(
        "Content",
        backref="agenda_item",
        )
    # Relationships
    geometries = klupung.flask.db.relationship(
        "AgendaItemGeometry",
        backref="agenda_item",
        )

    __table_args__ = (
        klupung.flask.db.CheckConstraint(index >= 0, name="check_index_positive"),
        klupung.flask.db.UniqueConstraint("meeting_id", "index"),
        )

    def __init__(self, subject, issue, meeting, index, introducer,
                 preparer, permalink, resolution, origin_last_modified_time):
        self.subject = subject
        self.issue = issue
        self.meeting = meeting
        self.index = index
        self.introducer = introducer
        self.preparer = preparer
        self.permalink = permalink
        self.resolution = resolution
        self.origin_last_modified_time = origin_last_modified_time

class Category(klupung.flask.db.Model):
    __tablename__ = "category"

    # Columns
    id = klupung.flask.db.Column(
        klupung.flask.db.Integer,
        primary_key=True,
        )
    name = klupung.flask.db.Column(
        klupung.flask.db.String(100),
        nullable=False,
        )
    level = klupung.flask.db.Column(
        klupung.flask.db.Integer,
        nullable=False,
        )
    origin_id = klupung.flask.db.Column(
        klupung.flask.db.String(50),
        nullable=False,
        )
    parent_id = klupung.flask.db.Column(
        klupung.flask.db.Integer,
        klupung.flask.db.ForeignKey("category.id"),
        nullable=True, # Top-level category does not have a parent
                       # category.
        )

    # Relationships
    issues = klupung.flask.db.relationship(
        "Issue",
        backref="category",
        )

    parent = klupung.flask.db.relationship(
        "Category",
        uselist=False,
        )

    __table_args__ = (
        klupung.flask.db.UniqueConstraint("origin_id"),
        )

    def __init__(self,  name, origin_id, parent=None):
        self.name = name
        self.origin_id = origin_id
        self.parent = parent
        self.level = 0
        if self.parent is not None:
            self.level = klupung.flask.models.Category.query.filter_by(parent=parent).first().level + 1

    def find_top_category(self):
        if self.parent:
            return self.parent.find_top_category()
        return self

class Issue(klupung.flask.db.Model):
    __tablename__ = "issue"

    # Columns
    id = klupung.flask.db.Column(
        klupung.flask.db.Integer,
        primary_key=True,
        )
    register_id = klupung.flask.db.Column(
        klupung.flask.db.String,
        nullable=False,
        )
    subject = klupung.flask.db.Column(
        klupung.flask.db.String(500),
        nullable=False,
        )
    summary = klupung.flask.db.Column(
        klupung.flask.db.String(1000),
        nullable=False,
        )
    category_id = klupung.flask.db.Column(
        klupung.flask.db.Integer,
        klupung.flask.db.ForeignKey("category.id"),
        nullable=False,
        )
    last_modified_time = klupung.flask.db.Column(
        klupung.flask.db.DateTime,
        default=klupung.flask.db.func.now(),
        onupdate=klupung.flask.db.func.now(),
        nullable=False,
        )
    latest_decision_date = klupung.flask.db.Column(
        klupung.flask.db.DateTime,
        nullable=False,
        )
    slug = klupung.flask.db.Column(
        klupung.flask.db.String,
        nullable=False,
        )

    # Relationships
    agenda_items = klupung.flask.db.relationship(
        "AgendaItem",
        backref="issue",
        )

    __table_args__ = (
        klupung.flask.db.UniqueConstraint("register_id"),
        klupung.flask.db.UniqueConstraint("slug"),
        )

    def __init__(self, register_id, subject, summary, category, latest_decision_date):
        self.register_id = register_id
        self.subject = subject
        self.summary = summary
        self.category = category
        self.slug = _slugify(self.register_id)
        self.latest_decision_date = latest_decision_date

class Meeting(klupung.flask.db.Model):
    __tablename__ = "meeting"

    # Columns
    id = klupung.flask.db.Column(
        klupung.flask.db.Integer,
        primary_key=True,
        )
    date = klupung.flask.db.Column(
        klupung.flask.db.DateTime,
        nullable=False,
        )
    policymaker_id = klupung.flask.db.Column(
        klupung.flask.db.Integer,
        klupung.flask.db.ForeignKey("policymaker.id"),
        nullable=False,
        )

    # Relationships
    meeting_documents = klupung.flask.db.relationship(
        "MeetingDocument",
        backref="meeting",
        )
    agenda_items = klupung.flask.db.relationship(
        "AgendaItem",
        backref="meeting",
        )

    __table_args__ = (
        klupung.flask.db.UniqueConstraint("policymaker_id", "date"),
        )

    def __init__(self, date, policymaker):
        self.date = date
        self.policymaker = policymaker

    @property
    def number(self):
        jan1 = datetime.date(self.date.year, 1, 1)
        return klupung.flask.models.Meeting.query.filter(
            klupung.flask.models.Meeting.date>=jan1,
            klupung.flask.models.Meeting.date<=self.date).count()

class MeetingDocument(klupung.flask.db.Model):
    __tablename__ = "meeting_document"

    # Columns
    id = klupung.flask.db.Column(
        klupung.flask.db.Integer,
        primary_key=True,
        )
    meeting_id = klupung.flask.db.Column(
        klupung.flask.db.Integer,
        klupung.flask.db.ForeignKey("meeting.id"),
        nullable=False,
        )
    origin_url = klupung.flask.db.Column(
        klupung.flask.db.Text,
        )
    origin_id = klupung.flask.db.Column(
        klupung.flask.db.String(40),
        nullable=False,
        )
    publish_datetime = klupung.flask.db.Column(
        klupung.flask.db.DateTime,
        )

    __table_args__ = (
        klupung.flask.db.UniqueConstraint("origin_id"),
        )

    def __init__(self, origin_url, meeting, origin_id, publish_datetime):
        self.origin_url = origin_url
        self.meeting = meeting
        self.origin_id = origin_id
        self.publish_datetime = publish_datetime

class Policymaker(klupung.flask.db.Model):
    __tablename__ = "policymaker"

    # Columns
    id = klupung.flask.db.Column(
        klupung.flask.db.Integer,
        primary_key=True,
        )
    abbreviation = klupung.flask.db.Column(
        klupung.flask.db.String(20),
        nullable=False,
        )
    name = klupung.flask.db.Column(
        klupung.flask.db.String(50),
        nullable=False,
        )
    slug = klupung.flask.db.Column(
        klupung.flask.db.String(20),
        nullable=False,
        )
    summary = klupung.flask.db.Column(
        klupung.flask.db.Text,
        nullable=True,
        )

    # Relationships
    meetings = klupung.flask.db.relationship(
        "Meeting",
        backref="policymaker",
        )

    __table_args__ = (
        klupung.flask.db.UniqueConstraint("abbreviation"),
        klupung.flask.db.UniqueConstraint("name"),
        klupung.flask.db.UniqueConstraint("slug"),
        )

    def __init__(self, abbreviation, name, summary):
        self.abbreviation = abbreviation
        self.name = name
        self.slug = _slugify(self.abbreviation)
        self.summary = summary

class Content(klupung.flask.db.Model):
    CONTENT_TYPES = (
        CONTENT_TYPE_RESOLUTION,
        CONTENT_TYPE_DRAFT_RESOLUTION,
        ) = (
        "resolution",
        "draft resolution",
        )
    CONTENT_INDICES = (
        CONTENT_INDEX_RESOLUTION,
        CONTENT_INDEX_DRAFT_RESOLUTION,
        ) = range(len(CONTENT_TYPES))

    __tablename__ = "content"

    # Columns
    id = klupung.flask.db.Column(
        klupung.flask.db.Integer,
        primary_key=True,
        )
    content_type = klupung.flask.db.Column(
        klupung.flask.db.Enum(*CONTENT_TYPES),
        nullable=False,
        )
    text = klupung.flask.db.Column(
        klupung.flask.db.Text,
        nullable=False,
        )
    index = klupung.flask.db.Column(
        klupung.flask.db.Integer,
        nullable=False,
        )
    agenda_item_id = klupung.flask.db.Column(
        klupung.flask.db.Integer,
        klupung.flask.db.ForeignKey("agenda_item.id"),
        )

    __table_args__ = (
        klupung.flask.db.CheckConstraint(index >= 0, name="check_index_positive"),
        klupung.flask.db.UniqueConstraint("agenda_item_id", "index"),
        )

    def __init__(self, content_type, text, index, agenda_item):
        self.content_type = content_type
        self.text = text
        self.index = index
        self.agenda_item = agenda_item

class AgendaItemGeometry(klupung.flask.db.Model):
    __tablename__ = "agenda_item_geometry"

    CATEGORIES = (
        CATEGORY_ADDRESS,
        CATEGORY_PLAN,
        CATEGORY_PLAN_UNIT,
        ) = (
        "address",
        "plan",
        "plan_unit",
        )

    TYPES = (
        TYPE_LINESTRING,
        TYPE_POINT,
        TYPE_POLYGON,
        ) = (
        "LineString",
        "Point",
        "Polygon",
        )

    # Columns
    id = klupung.flask.db.Column(
        klupung.flask.db.Integer,
        primary_key=True,
        )
    agenda_item_id = klupung.flask.db.Column(
        klupung.flask.db.Integer,
        klupung.flask.db.ForeignKey("agenda_item.id"),
        nullable=False,
        )
    category = klupung.flask.db.Column(
        klupung.flask.db.Enum(*CATEGORIES),
        nullable=False,
        )
    type = klupung.flask.db.Column(
        klupung.flask.db.Enum(*TYPES),
        nullable=False,
        )
    name = klupung.flask.db.Column(
        klupung.flask.db.Text,
        nullable=False,
        )
    coordinates = klupung.flask.db.Column(
        klupung.flask.db.PickleType,
        nullable=False,
        )

    __table_args__ = (
        klupung.flask.db.UniqueConstraint("agenda_item_id", "name"),
        )

    def __init__(self, agenda_item, category, type, name, coordinates):
        self.agenda_item = agenda_item
        self.category = category
        self.type = type
        self.name = name
        self.coordinates = coordinates
