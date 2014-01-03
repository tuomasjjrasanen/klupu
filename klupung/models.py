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

class Policymaker(klupung.db.Model):
    __tablename__ = "policymaker"

    # Columns
    id = klupung.db.Column(klupung.db.Integer,
                           primary_key=True)
    abbreviation = klupung.db.Column(klupung.db.String(20),
                                     unique=True,
                                     nullable=False)
    name = klupung.db.Column(klupung.db.String(50),
                             unique=True,
                             nullable=False)

    # Relationships
    meetings = klupung.db.relationship("Meeting")

    def __init__(self, abbreviation, name):
        self.abbreviation = abbreviation
        self.name = name

class Meeting(klupung.db.Model):
    __tablename__ = "meeting"

    # Columns
    id = klupung.db.Column(klupung.db.Integer,
                           primary_key=True)
    start_datetime = klupung.db.Column(klupung.db.DateTime,
                                       nullable=False)
    policymaker_id = klupung.db.Column(klupung.db.Integer,
                                       klupung.db.ForeignKey("policymaker.id"),
                                       nullable=False)

    # Relationships
    meeting_documents = klupung.db.relationship("MeetingDocument")
    policymaker = klupung.db.relationship("Policymaker")
    __table_args__ = (
        klupung.db.UniqueConstraint("policymaker_id", "start_datetime"),
        )

    def __init__(self, start_datetime, policymaker_id):
        self.start_datetime = start_datetime
        self.policymaker_id = policymaker_id

class MeetingDocument(klupung.db.Model):
    __tablename__ = "meeting_document"

    # Columns
    id = klupung.db.Column(klupung.db.Integer, primary_key=True)
    meeting_id = klupung.db.Column(klupung.db.Integer,
                                   klupung.db.ForeignKey("meeting.id"),
                                   nullable=False)
    origin_url = klupung.db.Column(klupung.db.Text)
    origin_id = klupung.db.Column(klupung.db.String(40),
                                  unique=True,
                                  nullable=False)
    publish_datetime = klupung.db.Column(klupung.db.DateTime)

    # Relationships
    meeting = klupung.db.relationship("Meeting")

    def __init__(self, origin_url, meeting_id, origin_id, publish_datetime):
        self.origin_url = origin_url
        self.meeting_id = meeting_id
        self.origin_id = origin_id
        self.publish_datetime = publish_datetime
