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
    date = sqlalchemy.Column(sqlalchemy.Date,
                             nullable=False)
    policymaker_id = sqlalchemy.Column(sqlalchemy.Integer,
                                       sqlalchemy.ForeignKey("policymaker.id"),
                                       nullable=False)

    # Relationships
    meeting_documents = sqlalchemy.orm.relationship("MeetingDocument")
    policymaker = sqlalchemy.orm.relationship("Policymaker")

    def __init__(self, date, policymaker_id):
        self.date = date
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
