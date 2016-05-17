Nebula
======

Nebula is Hubble's Insight system, which ties into osquery, allowing you to
query your infrastructure as if it were a database. Currently only supported on
Linux.

Installation
------------

Currently Nebula consists of only a single module, ``nebula_osquery.py``. Place
this module in your ``_modules/`` directory and use ``saltutil.sync_all`` to
sync it to your minions. The module's ``__virtualname__`` is ``nebula``, so
that is the name you'll use when calling the module. (See the examples below)

The module relies on Salt's ``osquery`` module, which in turn relies on the
``osquery`` package. Installation instructions for ``osquery`` can be found
`here <https://osquery.io/downloads/>`_.

This module also requires pillar data to function. The default pillar key for
this data is ``nebula_osquery``, but you can pass in a different pillar key at
call time. The queries themselves should be grouped under one or more group
identifiers. Usually, these identifiers will be frequencies, such as
``fifteen_min`` or ``hourly`` or ``daily``. The module targets the queries
using these identifiers.

Your pillar data might look like this:

.. code-block:: yaml

    nebula_osquery:
      hour:
        - crontab: query: select c.*,t.iso_8601 as _time from crontab as c join time as t;
        - query_name: suid_binaries
          query: select sb.*, t.iso_8601 as _time from suid_bin as sb join time as t;
      day:
        - query_name: rpm_packages
          query: select rpm.*, t.iso_8601 from rpm_packages as rpm join time as t;

You can then target these queries like so:

.. code_block:: bash

    salt '*' nebula.queries day
    salt '*' nebula.queries hour verbose=True
    salt '*' nebula.queries hour pillar_key=sec_osqueries

You can set up the queries to run on a schedule using salt's scheduler, and
return the results to Splunk or another destination. Or you can run the queries
manually on demand.

Roadmap
-------

  * WQL (Windows)
