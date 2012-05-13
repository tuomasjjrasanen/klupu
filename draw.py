#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
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

from __future__ import division
from __future__ import with_statement

import collections
import datetime
import os.path
import sys

import matplotlib
matplotlib.use("Qt4Agg")
import matplotlib.pyplot as plt

import klupu.db

def get_dist(values):
    dist = collections.OrderedDict()
    for v in sorted(values):
        try:
            dist[v] += 1 / len(values) * 100.0
        except KeyError:
            dist[v] = 1 / len(values) * 100.0
    return dist.keys(), dist.values()

def iter_cumprobs(probs):
    cumprob = 0.0
    for prob in probs:
        cumprob += prob
        yield cumprob

def cdf_plot(subplot, samples, **kwargs):
    subplot.grid(True)
    subplot.set_ylim(0.0, 100.0)
    subplot.set_ylabel("[%]")
    values, probs = get_dist(samples)
    subplot.plot(values, list(iter_cumprobs(probs)), **kwargs)
    subplot.legend(labelspacing=0.1, loc="best")

def stacked_bar(subplot, xvals, yvals, **kwargs):
    bottom = len(xvals) * [0]

    for color, label in zip("bgr", ("kv", "kh", "karltk")):
        yvals = read_monthly_durations("%s*.json" % label, yearmonths)
        subplot.bar(xvals, yvals, color=color, align="center",
                   bottom=bottom, label=label)
        bottom = [x + y for x, y in zip(bottom, yvals)]

    subplot.set_xlim(-1, len(xvals))

    xticks = range(0, len(xvals), 3)
    subplot.get_xaxis().set_ticks(xticks)

    xticklabels = ["%d-%02d" % ym for ym in yearmonths[::3]]
    subplot.get_xaxis().set_ticklabels(xticklabels)

def iter_yearmonths(startyear, startmonth, stopyear, stopmonth):
    for year in range(startyear, startyear + 1):
        for month in range(startmonth, 13):
            yield year, month
    for year in range(startyear + 1, stopyear):
        for month in range(1, 13):
            yield year, month
    for year in range(stopyear, stopyear + 1):
        for month in range(1, stopmonth + 1):
            yield year, month

def query(db_path, expr, *args):
    with klupu.db.connect(db_path) as db_conn:
        cur = db_conn.cursor()
        return cur.execute(expr, args).fetchall()

def get_monthly_durations(db_path, body, yearmonths):
    monthly_durations = {}

    results = query(db_path, """
SELECT starttime, duration/3600.0
FROM klupu_meetings
WHERE body = ?
ORDER BY starttime;
""", body)

    for starttime, duration in results:
        starttime = datetime.datetime.strptime(starttime, "%Y-%m-%dT%H:%M:%S")
        yearmonth = (starttime.year, starttime.month)
        try:
            monthly_durations[yearmonth] += duration
        except KeyError:
            monthly_durations[yearmonth] = duration

    result = []
    for yearmonth in yearmonths:
        duration = monthly_durations.get(yearmonth, 0.0)
        result.append(duration)

    return result

def draw_monthly_durations(db_path, startyear, startmonth, endyear, endmonth):
    fig = plt.figure()

    subplot = fig.add_subplot(1, 1, 1)
    subplot.set_title(u"Monthly meeting durations")
    subplot.set_ylabel("Hours")
    subplot.grid(True)

    yearmonths = list(iter_yearmonths(startyear, startmonth, endyear, endmonth))
    xvals = range(len(yearmonths))
    bottom = len(xvals) * [0]

    for color, body in zip("bgr", ("karltk", "kh", "kv")):
        yvals = get_monthly_durations(db_path, body, yearmonths)
        subplot.bar(xvals, yvals, color=color, align="center",
                   bottom=bottom, label=body)
        bottom = [x + y for x, y in zip(bottom, yvals)]

    subplot.set_xlim(-1, len(xvals))

    xticks = range(0, len(xvals), 3)
    subplot.get_xaxis().set_ticks(xticks)

    xticklabels = ["%d-%02d" % ym for ym in yearmonths[::3]]
    subplot.get_xaxis().set_ticklabels(xticklabels)

    for label in subplot.get_xticklabels():
        label.set_rotation(30)

    subplot.legend(loc="best")

def draw_duration_cdf(db_path):
    fig = plt.figure()

    subplot = fig.add_subplot(1,1,1)
    subplot.set_title(u"Cumulative issue duration distribution")
    subplot.set_xlabel(u"Hours")

    for body in ("karltk", "kh", "kv"):
        samples = query(db_path, """
SELECT duration/3600.0
FROM klupu_meetings
WHERE body = ?
ORDER BY duration;
""", body)
        cdf_plot(subplot, samples, label=body)

def draw_presenter_cdf(db_path):
    fig = plt.figure()

    subplot = fig.add_subplot(1,1,1)
    subplot.set_title(u"Issue preparation distribution among all preparers")
    subplot.set_ylabel(u"Number of issue preparations")
    subplot.set_xlabel(u"Preparer")
    subplot.set_xticks([])

    samples = query(db_path, """
SELECT count()
FROM klupu_presenters
GROUP BY name
ORDER BY count();
""")
    samples = zip(*samples)[0]
    subplot.bar(range(len(samples)), samples, width=1.0, color="k")
    avg = sum(samples) / len(samples)
    subplot.axhline(samples[int(len(samples) * 0.95)], label="95th percentile",
                    color="g", linestyle="--", linewidth=3)
    subplot.axhline(avg, label="average", color="r", linestyle="--", linewidth=3)
    subplot.set_xlim(0, len(samples))
    subplot.set_yticks(range(0, 275, 25))
    subplot.grid(axis="y")
    subplot.legend(loc="best")

def draw_approved_bars(db_path):
    fig = plt.figure()

    subplot = fig.add_subplot(1,1,1)
    subplot.set_title(u"Approval rate of decisions")
    subplot.set_ylabel(u"[%]")
    subplot.set_xlabel(u"Governing body")

    decision_counts, bodies = zip(*query(db_path, """
SELECT count(), body
FROM klupu_issues
  JOIN klupu_presenters
    ON klupu_presenters.issue_id = klupu_issues.id
  JOIN klupu_meetings
    ON klupu_meetings.id = klupu_issues.meeting_id
GROUP BY body
ORDER BY body;
"""))

    approved_counts, bodies = zip(*query(db_path, u"""
SELECT count(), body
FROM klupu_issues
  JOIN klupu_presenters
    ON klupu_presenters.issue_id = klupu_issues.id
  JOIN klupu_meetings
    ON klupu_meetings.id = klupu_issues.meeting_id
WHERE (decision GLOB 'Päätösehdotus hyväksyttiin.*'
       OR decision GLOB 'Ehdotus hyväksyttiin.*')
GROUP BY body
ORDER BY body;
"""))

    subplot.set_xticks(range(len(approved_counts)))
    subplot.set_xticklabels(bodies)
    ratios = [x/y*100.0 for x, y in zip(approved_counts, decision_counts)]
    subplot.bar(range(len(ratios)), ratios, align="center", color="bgr")
    subplot.set_xlim(-0.6, len(ratios) - 0.4)
    subplot.grid(axis="y")

def draw_participation_activity(db_path, role):
    fig = plt.figure()

    subplot = fig.add_subplot(1,1,1)
    subplot.set_title("Cumulative participation activity distribution of %ss" % role)
    subplot.set_xlabel("Participation percentage")

    for body in ("karltk", "kh", "kv"):
        participation_counts = query(db_path, """
select count()
from klupu_participants
join klupu_meetings
  on klupu_meetings.id == klupu_participants.meeting_id
where role = ? and body = ?
group by name
order by count();
""", role, body)
        meeting_count, = query(db_path, """
select count()
from klupu_meetings
where body = ?;
""", body)[0]

        participation_counts = zip(*participation_counts)[0]
        samples = [x / meeting_count * 100 for x in participation_counts]
        cdf_plot(subplot, samples, label=body)

    # subplot.bar(range(len(samples)), samples, width=1.0, color="k")
    # avg = sum(samples) / len(samples)
    # subplot.axhline(samples[int(len(samples) * 0.95)], label="95th percentile",
    #                 color="g", linestyle="--", linewidth=3)
    # subplot.axhline(avg, label="average", color="r", linestyle="--", linewidth=3)
    # subplot.set_xlim(0, len(samples))
    # subplot.set_yticks(range(0, 275, 25))
    # subplot.grid(axis="y")
    # subplot.legend(loc="best")

def _main():
    db_path = sys.argv[1]
    draw_monthly_durations(db_path, 2008, 11, 2011, 12)
    draw_duration_cdf(db_path)
    draw_presenter_cdf(db_path)
    draw_approved_bars(db_path)
    draw_participation_activity(db_path, "other")
    draw_participation_activity(db_path, "decision-maker")

    plt.show()

if __name__ == "__main__":
    _main()
