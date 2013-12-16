=======
 Klupu
=======

Klupu is a report mining tool designed to extract and visualize data
from meeting minutes of various governing bodies of city of
Jyväskylä. Klupu is a Finnish word for flail which is a tool used for
separating grains from husks. Grains of knowledge, in this case.

Author: Tuomas Jorma Juhani Räsänen <tuomasjjrasanen@tjjr.fi>

Requirements
============

- Python 3
- Beautiful Soup 4
- Matplotlib

How to use
==========

1. Fetch meeting minutes::

  python3 fetch.py http://www3.jkl.fi/paatokset/karltk08.htm

2. Initialize Sqlite3 database::

  python3 init.py myklupu.db

3. Import meeting minutes to the database::

  python3 save.py myklupu.db paatokset/karltk/2008/16121630.0

4. Draw figures from the database::

  python draw.py myklupu.db

5. Fetch addresses::

  python3 fetch_addresses.py Jyväskylä >fetched_addresses.txt

6. Geocode addresses::

  mkdir osm_gecodes
  python3 geocode_addresses.py osm_geocodes addresses.txt your@email.address

How to contribute
=================

Source code history is controlled with Git and hosted hosted in
GitHub. The preferred way to contibute is to clone the main repository
and send pull-requests. Patches via email are also accepted, but do
not use attachments; insert the patch to body of the message.

How to copy
===========

Klupu is licensed under the terms of GNU Public License version 3 or
later. In short, it means that you are free to copy, modify and
redistribute this software as long as you place the derivative work
under a compatible license. See COPYING for details.
