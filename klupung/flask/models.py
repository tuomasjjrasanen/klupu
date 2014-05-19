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
    issue = klupung.flask.db.relationship(
        "Issue",
        backref="agenda_items",
        )
    meeting = klupung.flask.db.relationship(
        "Meeting",
        backref="agenda_items",
        )

    __table_args__ = (
        klupung.flask.db.CheckConstraint(index >= 0, name="check_index_positive"),
        klupung.flask.db.UniqueConstraint("meeting_id", "index"),
        )

    def __init__(self, subject, issue_id, meeting_id, index, introducer,
                 preparer, permalink, resolution, origin_last_modified_time):
        self.subject = subject
        self.issue_id = issue_id
        self.meeting_id = meeting_id
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
    parent = klupung.flask.db.relationship(
        "Category",
        )

    __table_args__ = (
        klupung.flask.db.UniqueConstraint("origin_id"),
        )

    def __init__(self,  name, origin_id, parent_id=None):
        self.name = name
        self.origin_id = origin_id
        self.parent_id = parent_id
        self.level = 0
        if self.parent_id is not None:
            self.level = klupung.flask.models.Category.query.filter_by(id=parent_id).first().level + 1

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
        )
    slug = klupung.flask.db.Column(
        klupung.flask.db.String,
        nullable=False,
        )

    # Relationships
    category = klupung.flask.db.relationship(
        "Category",
        )

    __table_args__ = (
        klupung.flask.db.UniqueConstraint("register_id"),
        klupung.flask.db.UniqueConstraint("slug"),
        )

    def __init__(self, register_id, subject, summary, category_id):
        self.register_id = register_id
        self.subject = subject
        self.summary = summary
        self.category_id = category_id
        self.slug = _slugify(self.register_id)

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
        )
    policymaker = klupung.flask.db.relationship(
        "Policymaker",
        )

    __table_args__ = (
        klupung.flask.db.UniqueConstraint("policymaker_id", "date"),
        )

    def __init__(self, date, policymaker_id):
        self.date = date
        self.policymaker_id = policymaker_id

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

    # Relationships
    meeting = klupung.flask.db.relationship(
        "Meeting",
        )

    __table_args__ = (
        klupung.flask.db.UniqueConstraint("origin_id"),
        )

    def __init__(self, origin_url, meeting_id, origin_id, publish_datetime):
        self.origin_url = origin_url
        self.meeting_id = meeting_id
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

    # Relationships
    meetings = klupung.flask.db.relationship(
        "Meeting",
        )

    __table_args__ = (
        klupung.flask.db.UniqueConstraint("abbreviation"),
        klupung.flask.db.UniqueConstraint("name"),
        klupung.flask.db.UniqueConstraint("slug"),
        )

    def __init__(self, abbreviation, name):
        self.abbreviation = abbreviation
        self.name = name
        self.slug = _slugify(self.abbreviation)

class Content(klupung.flask.db.Model):
    CONTENT_TYPES = (
        CONTENT_TYPE_RESOLUTION,
        ) = (
        "resolution",
        )
    CONTENT_INDICES = (
        CONTENT_INDEX_RESOLUTION,
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

    # Relationships
    agenda_item = klupung.flask.db.relationship(
        "AgendaItem",
        backref="contents",
        )

    __table_args__ = (
        klupung.flask.db.CheckConstraint(index >= 0, name="check_index_positive"),
        klupung.flask.db.UniqueConstraint("agenda_item_id", "index"),
        )

    def __init__(self, content_type, text, index, agenda_item_id):
        self.content_type = content_type
        self.text = text
        self.index = index
        self.agenda_item_id = agenda_item_id
