# -*- coding: utf-8 -*-
# klupu - scrape meeting minutes of governing bodies of city of Jyväskylä
# Copyright (C) 2013 Koodilehto Osk <http://koodilehto.fi>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sqlite3

def connect(db_path):
    db_conn = sqlite3.connect(db_path)
    with db_conn:
        db_conn.execute("""
PRAGMA foreign_keys = ON
""")
    return db_conn

def init(db_path):
    with connect(db_path) as db_conn:
        db_conn.execute("""
CREATE TABLE klupu_meetings
(id INTEGER PRIMARY KEY,
 body TEXT NOT NULL,
 place TEXT NOT NULL,
 starttime TEXT NOT NULL,
 duration INTEGER NOT NULL,
 UNIQUE(body, starttime))
""")

        db_conn.execute("""
CREATE TABLE klupu_participants
(id INTEGER PRIMARY KEY,
 meeting_id INTEGER NOT NULL,
 name TEXT NOT NULL,
 role TEXT NOT NULL,
 FOREIGN KEY(meeting_id) REFERENCES klupu_meetings(id)
 UNIQUE(meeting_id, name, role))
""")

        db_conn.execute("""
CREATE TABLE klupu_issues
(id INTEGER PRIMARY KEY,
 meeting_id INTEGER NOT NULL,
 decision TEXT,
 title TEXT NOT NULL,
 number INTEGER NOT NULL,
 dnro TEXT,
 FOREIGN KEY(meeting_id) REFERENCES klupu_meetings(id)
 UNIQUE(meeting_id, decision, title, number, dnro))
""")

        db_conn.execute("""
CREATE TABLE klupu_presenters
(id INTEGER PRIMARY KEY,
 issue_id INTEGER NOT NULL,
 name TEXT NOT NULL,
 FOREIGN KEY(issue_id) REFERENCES klupu_issues(id)
 UNIQUE(issue_id, name))
""")

def insert_meeting(db_conn, body, place, starttime, duration):
    starttime = starttime.isoformat()
    cur = db_conn.cursor()
    cur.execute("""
INSERT INTO klupu_meetings (id, body, place, starttime, duration)
VALUES (NULL, ?, ?, ?, ?)
""", [body, place, starttime, duration])
    return cur.lastrowid

def insert_participant(db_conn, meeting_id, name, role):
    cur = db_conn.cursor()
    cur.execute("""
INSERT INTO klupu_participants (id, meeting_id, name, role)
VALUES (NULL, ?, ?, ?)
""", [meeting_id, name, role])
    return cur.lastrowid

def insert_issue(db_conn, meeting_id, decision, title, number, dnro):
    cur = db_conn.cursor()
    cur.execute("""
INSERT INTO klupu_issues (id, meeting_id, decision, title, number, dnro)
VALUES (NULL, ?, ?, ?, ?, ?)
""", [meeting_id, decision, title, number, dnro])
    return cur.lastrowid

def insert_presenter(db_conn, issue_id, name):
    cur = db_conn.cursor()
    cur.execute("""
INSERT INTO klupu_presenters (id, issue_id, name)
VALUES (NULL, ?, ?)
""", [issue_id, name])
    return cur.lastrowid

def insert(db_path, meeting):
    with connect(db_path) as db_conn:
        duration = 0
        for start, end in zip(meeting["start-times"], meeting["end-times"]):
            duration += (end - start).total_seconds()
        meeting_id = insert_meeting(db_conn, meeting["body"], meeting["place"],
                                    meeting["start-times"][0], duration)
        for name in meeting["decision-makers"]:
            insert_participant(db_conn, meeting_id, name, "decision-maker")
        for name in meeting["others"]:
            insert_participant(db_conn, meeting_id, name, "other")
        for issue in meeting["issues"]:
            issue_id = insert_issue(db_conn, meeting_id, issue["decision"], issue["title"],
                                    issue["number"], issue["dnro"])
            for name in issue["presenters"]:
                insert_presenter(db_conn, issue_id, name)
