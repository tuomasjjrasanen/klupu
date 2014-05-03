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

import klupung

class AgendaItem(klupung.db.Model):
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
    id = klupung.db.Column(
        klupung.db.Integer,
        primary_key=True,
        )
    subject = klupung.db.Column(
        klupung.db.String(500),
        nullable=False,
        )
    issue_id = klupung.db.Column(
        klupung.db.Integer,
        klupung.db.ForeignKey("issue.id"),
        )
    meeting_id = klupung.db.Column(
        klupung.db.Integer,
        klupung.db.ForeignKey("meeting.id"),
        nullable=False,
        )
    index = klupung.db.Column(
        klupung.db.Integer,
        nullable=False,
        )
    introducer = klupung.db.Column(
        klupung.db.String(100),
        )
    preparer = klupung.db.Column(
        klupung.db.String(100),
        )
    last_modified_time = klupung.db.Column(
        klupung.db.DateTime,
        default=klupung.db.func.now(),
        onupdate=klupung.db.func.now(),
        nullable=False,
        )
    origin_last_modified_time = klupung.db.Column(
        klupung.db.DateTime,
        nullable=False,
        )
    permalink = klupung.db.Column(
        klupung.db.String(500),
        nullable=False,
        )
    resolution = klupung.db.Column(
        klupung.db.Enum(*RESOLUTIONS),
        nullable=False,
        )

    # Relationships
    issue = klupung.db.relationship(
        "Issue",
        backref="agenda_items",
        )
    meeting = klupung.db.relationship(
        "Meeting",
        backref="agenda_items",
        )

    __table_args__ = (
        klupung.db.CheckConstraint(index >= 0, name="check_index_positive"),
        klupung.db.UniqueConstraint("meeting_id", "index"),
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

class Category(klupung.db.Model):
    __tablename__ = "category"

    # Columns
    id = klupung.db.Column(
        klupung.db.Integer,
        primary_key=True,
        )
    name = klupung.db.Column(
        klupung.db.String(100),
        nullable=False,
        )
    level = klupung.db.Column(
        klupung.db.Integer,
        nullable=False,
        )
    origin_id = klupung.db.Column(
        klupung.db.String(50),
        nullable=False,
        )
    parent_id = klupung.db.Column(
        klupung.db.Integer,
        klupung.db.ForeignKey("category.id"),
        nullable=True, # Top-level category does not have a parent
                       # category.
        )

    # Relationships
    parent = klupung.db.relationship(
        "Category",
        )

    __table_args__ = (
        klupung.db.UniqueConstraint("origin_id"),
        )

    def __init__(self,  name, origin_id, parent_id=None):
        self.name = name
        self.origin_id = origin_id
        self.parent_id = parent_id
        self.level = 0
        if self.parent_id is not None:
            self.level = klupung.models.Category.query.filter_by(id=parent_id).first().level + 1

class Issue(klupung.db.Model):
    __tablename__ = "issue"

    # Columns
    id = klupung.db.Column(
        klupung.db.Integer,
        primary_key=True,
        )
    register_id = klupung.db.Column(
        klupung.db.String,
        nullable=False,
        )
    subject = klupung.db.Column(
        klupung.db.String(500),
        nullable=False,
        )
    summary = klupung.db.Column(
        klupung.db.String(1000),
        nullable=False,
        )
    category_id = klupung.db.Column(
        klupung.db.Integer,
        klupung.db.ForeignKey("category.id"),
        nullable=False,
        )
    last_modified_time = klupung.db.Column(
        klupung.db.DateTime,
        default=klupung.db.func.now(),
        onupdate=klupung.db.func.now(),
        nullable=False,
        )
    latest_decision_date = klupung.db.Column(
        klupung.db.DateTime,
        )

    # Relationships
    category = klupung.db.relationship(
        "Category",
        )

    __table_args__ = (
        klupung.db.UniqueConstraint("register_id"),
        )

    def __init__(self, register_id, subject, summary, category_id):
        self.register_id = register_id
        self.subject = subject
        self.summary = summary
        self.category_id = category_id

class Meeting(klupung.db.Model):
    __tablename__ = "meeting"

    # Columns
    id = klupung.db.Column(
        klupung.db.Integer,
        primary_key=True,
        )
    start_datetime = klupung.db.Column(
        klupung.db.DateTime,
        nullable=False,
        )
    policymaker_id = klupung.db.Column(
        klupung.db.Integer,
        klupung.db.ForeignKey("policymaker.id"),
        nullable=False,
        )

    # Relationships
    meeting_documents = klupung.db.relationship(
        "MeetingDocument",
        )
    policymaker = klupung.db.relationship(
        "Policymaker",
        )

    __table_args__ = (
        klupung.db.UniqueConstraint("policymaker_id", "start_datetime"),
        )

    def __init__(self, start_datetime, policymaker_id):
        self.start_datetime = start_datetime
        self.policymaker_id = policymaker_id

class MeetingDocument(klupung.db.Model):
    __tablename__ = "meeting_document"

    # Columns
    id = klupung.db.Column(
        klupung.db.Integer,
        primary_key=True,
        )
    meeting_id = klupung.db.Column(
        klupung.db.Integer,
        klupung.db.ForeignKey("meeting.id"),
        nullable=False,
        )
    origin_url = klupung.db.Column(
        klupung.db.Text,
        )
    origin_id = klupung.db.Column(
        klupung.db.String(40),
        nullable=False,
        )
    publish_datetime = klupung.db.Column(
        klupung.db.DateTime,
        )

    # Relationships
    meeting = klupung.db.relationship(
        "Meeting",
        )

    __table_args__ = (
        klupung.db.UniqueConstraint("origin_id"),
        )

    def __init__(self, origin_url, meeting_id, origin_id, publish_datetime):
        self.origin_url = origin_url
        self.meeting_id = meeting_id
        self.origin_id = origin_id
        self.publish_datetime = publish_datetime

class Policymaker(klupung.db.Model):
    __tablename__ = "policymaker"

    # Columns
    id = klupung.db.Column(
        klupung.db.Integer,
        primary_key=True,
        )
    abbreviation = klupung.db.Column(
        klupung.db.String(20),
        nullable=False,
        )
    name = klupung.db.Column(
        klupung.db.String(50),
        nullable=False,
        )

    # Relationships
    meetings = klupung.db.relationship(
        "Meeting",
        )

    __table_args__ = (
        klupung.db.UniqueConstraint("abbreviation"),
        klupung.db.UniqueConstraint("name"),
        )

    def __init__(self, abbreviation, name):
        self.abbreviation = abbreviation
        self.name = name
