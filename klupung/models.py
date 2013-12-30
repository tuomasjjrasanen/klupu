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

import sqlalchemy
import sqlalchemy.orm

import klupung.db

class Policymaker(klupung.db.Base):
    __tablename__ = "policymaker"

    # Columns
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True)
    abbreviation = sqlalchemy.Column(sqlalchemy.String(20),
                                     unique=True,
                                     nullable=False)

    # Relationships
    meetings = sqlalchemy.orm.relationship("Meeting")

    def __init__(self, abbreviation):
        self.abbreviation = abbreviation

class Meeting(klupung.db.Base):
    __tablename__ = "meeting"

    # Columns
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True)
    start_datetime = sqlalchemy.Column(sqlalchemy.DateTime,
                                       nullable=False)
    policymaker_id = sqlalchemy.Column(sqlalchemy.Integer,
                                       sqlalchemy.ForeignKey("policymaker.id"),
                                       nullable=False)

    # Relationships
    meeting_documents = sqlalchemy.orm.relationship("MeetingDocument")
    policymaker = sqlalchemy.orm.relationship("Policymaker")

    def __init__(self, start_datetime, policymaker_id):
        self.start_datetime = start_datetime
        self.policymaker_id = policymaker_id

class MeetingDocument(klupung.db.Base):
    __tablename__ = "meeting_document"

    # Columns
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    meeting_id = sqlalchemy.Column(sqlalchemy.Integer,
                                   sqlalchemy.ForeignKey("meeting.id"),
                                   nullable=False)
    origin_url = sqlalchemy.Column(sqlalchemy.Text)

    # Relationships
    meeting = sqlalchemy.orm.relationship("Meeting")

    def __init__(self, origin_url, meeting_id):
        self.origin_url = origin_url
        self.meeting_id = meeting_id
