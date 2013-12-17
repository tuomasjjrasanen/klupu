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

import klupung.ktweb

downloader = klupung.ktweb.HTMLDownloader(download_dir="downloads")

# HTTP requests will not be made more often than once per second.
downloader.min_http_request_interval = 1

# Do not download pages if they are found from download_dir.
downloader.force_download = False

downloader.download("http://www3.jkl.fi/paatokset/karltk.htm")
