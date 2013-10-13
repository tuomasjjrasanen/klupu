# klupu - scrape meeting minutes of governing bodies of city of Jyväskylä
# Copyright (C) 2012 Tuomas Jorma Juhani Räsänen <tuomasjjrasanen@tjjr.fi>
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

import datetime
import os.path
import re
import sqlite3
import sys
import warnings

import klupu
import klupu.db

def showwarning(message, category, filename, lineno, *args):
    try:
        file = args[0]
    except IndexError:
        file = sys.stderr
    print("klupu: %s:" % category.__name__, message, file=file)

warnings.showwarning = showwarning

RE_PERSON = re.compile(r"([A-ZÖÄÅ][a-zöäå]*(?:-[A-ZÖÄÅ][a-zöäå]*)*(?: [A-ZÖÄÅ][a-zöäå]*(?:-[A-ZÖÄÅ][a-zöäå]*)*)+)")
RE_DNRO = re.compile(r"Dnro (\d+[ ]?/\d+)")
RE_TIME = re.compile(r"(?:[a-zA-Z]+ )?(\d\d?)\.(\d\d?)\.(\d{4})[ ]?,? (?:kello|klo)\s?(\d\d?)\.(\d\d)\s*[–-]\s*(\d\d?)\.(\d\d)")

def parse_meeting_times(text):
    for time_spec in RE_TIME.findall(text):
        yield [int(v) for v in time_spec]

def parse_meeting_info(soup):
    starts = []
    ends = []

    # Find the correct element.
    markertag = soup(text=re.compile("KOKOUSTIEDOT"))[0]
    ps = markertag.parent.parent.parent.parent("td")[1]("p")

    # We are interested only in text elements.
    texts = [re.sub(r"[\xad\s]+", " ", p.text) for p in ps if p.text.strip()]

    # The place of meeting is easy, it's always the last element.
    place = texts[-1]

    # Then there might be one or more start time - end time pairs:
    # some of the meetings are two-day meetings.
    for text in texts[:-1]:

        # There can be also several datetime within one paragraph
        for meeting_time in parse_meeting_times(text):
            day, month, year, start_hour, start_minute, end_hour, end_minute = meeting_time

            # Someone uses stupid format to denote that this is part
            # of the yesterday..
            end_hour %= 24

            start = datetime.datetime(year, month, day, start_hour, start_minute)
            end = datetime.datetime(year, month, day, end_hour, end_minute)
            if start > end:
                end += datetime.timedelta(1)

            starts.append(start)
            ends.append(end)

    return place, starts, ends

def parse_participants(soup, marker_text):
    markers = soup(text=re.compile(marker_text))
    if not markers:
        return []
    td = markers[0].parent.parent.parent.parent("td")[1]
    persons = []
    for text in [p.text for p in td("p")]:
        parts = re.findall(r"[xX]\s+([^\xa0]+)", text)
        for part in parts:
            s = re.sub("\s+", " ", part)
            for name in RE_PERSON.findall(s):
                persons.append(name)

    return persons

def parse_decision_makers(soup):
    return parse_participants(soup, "Päätöksentekijä")

def parse_others(soup):
    return parse_participants(soup, "Muut läsnäolijat")

def parse_issue_title(soup):
    numbered_title = soup.html.body("p", {"class": "Asiaotsikko"})[0].text
    match = re.match(r"^(\d+)\s+", numbered_title)
    number = int(match.group(1))
    title = re.sub(r"\s+", " ", numbered_title[match.end():])
    return number, title

def parse_dnro(soup):
    ps = soup.html.body("p")
    dnros = []
    for text in [re.sub(r"\s+", " ", p.text) for p in ps]:
        dnro_match = RE_DNRO.match(text)
        if dnro_match:
            dnros.append(dnro_match.group(1))

    try:
        dnro = dnros[0]
    except IndexError:
        # Some of the issues in each meeting are "standard" issues,
        # e.g. opening of the meeting, determination of quorum, which
        # do not have Dnro.
        dnro = None

    if dnro == "0/00":
        dnro = None

    return dnro

def parse_decision(soup):
    decision = None
    for p in soup.html.body("p"):
        match = re.match(r"^\s*Päätös\s+(.*)", p.text, re.DOTALL)
        if match:
            decision = re.sub("\s+", " ", match.group(1))
    return decision

def parse_presenters(soup):
    presenters = []
    for text in [re.sub(r"\s+", " ", p.text).strip() for p in soup("p")]:
        if text.startswith("Asian valmisteli"):
            presenters.extend(RE_PERSON.findall(text))
            break
    return presenters

def parse_issue(soup):
    number, title = parse_issue_title(soup)
    dnro = parse_dnro(soup)
    presenters = parse_presenters(soup)
    decision = parse_decision(soup)
    return {
        "number": number,
        "dnro": dnro,
        "presenters": presenters,
        "title": title,
        "decision": decision,
        }

def parse_meeting(minutes_dirpath):
    minutes_dirpath = os.path.normpath(minutes_dirpath)

    issues = []
    for issue_filepath in klupu.iter_issue_filepaths(minutes_dirpath):
        issue_soup = klupu.read_soup(issue_filepath)
        issue = parse_issue(issue_soup)
        issues.append(issue)

    index_filepath = os.path.join(minutes_dirpath, "index.htm")
    index_soup = klupu.read_soup(index_filepath)

    selfurl = index_soup.html.body("a", target="_self")[0]["href"]
    body = os.path.splitext(os.path.basename(selfurl))[0]

    info_filepath = os.path.join(minutes_dirpath, klupu.INFO_FILENAME)
    info_soup = klupu.read_soup(info_filepath)

    place, starttimes, endtimes = parse_meeting_info(info_soup)

    decision_makers = parse_decision_makers(info_soup)
    others = parse_others(info_soup)

    return {
        "body": body,
        "place": place,
        "start-times": starttimes,
        "end-times": endtimes,
        "decision-makers": decision_makers,
        "others": others,
        "issues": issues,
        }

class ValidityWarning(UserWarning):
    pass

def warn(message):
    warnings.warn(message, ValidityWarning)

def validate_issue(issue):
    if not issue["number"]:
        warn("issue number not found")
    if not issue["title"]:
        warn("issue title not found")
    if not issue["dnro"] and issue["presenters"]:
        warn("presented issue does not have dnro")

def validate(meeting):
    if not meeting["body"]:
        warn("governing body not found")
    if not meeting["place"]:
        warn("meeting place not found")
    if len(meeting["start-times"]) != len(meeting["end-times"]):
        warn("number of meeting start-times and end-times do not match")
    for starttime, endtime in zip(meeting["start-times"], meeting["end-times"]):
        if starttime >= endtime:
            warn("meeting start time is past end time")
    if not meeting["decision-makers"]:
        warn("decision-makers not found")
    if not meeting["others"]:
        warn("other participants not found")
    if not meeting["issues"]:
        warn("issues not found")
    for issue in meeting["issues"]:
        validate_issue(issue)

def _main():
    db_path = sys.argv[1]
    for minutes_dirpath in sys.argv[2:]:
        print(minutes_dirpath)
        meeting = parse_meeting(minutes_dirpath)
        validate(meeting)
        try:
            klupu.db.insert(db_path, meeting)
        except sqlite3.IntegrityError as err:
            print(err, "Skipping...", file=sys.stderr)
            continue

if __name__ == "__main__":
    _main()
