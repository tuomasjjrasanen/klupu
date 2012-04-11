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

import json

def dump(meeting):
    body = meeting["body"]
    starttime = meeting["start-times"][0].strftime("%Y-%m-%d-%H-%M")

    # Jason does not know how to serialize datetimes, let's do it for
    # him this time.
    meeting["start-times"] = [d.isoformat() for d in meeting["start-times"]]
    meeting["end-times"] = [d.isoformat() for d in meeting["end-times"]]

    with open("%s-%s.json" % (body, starttime), "w") as json_file:
        json.dump(meeting, json_file, ensure_ascii=False, indent=1)
