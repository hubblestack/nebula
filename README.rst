.. _nebula_introduction:

Introduction
============

Nebula is Hubble's Insight system, which ties into ``osquery``, allowing you to
query your infrastructure as if it were a database. This system can be used to
take scheduled snapshots of your systems.

Two different installation methods are outlined below. The first method is more
stable (and therefore recommended). This method uses Salt's package manager to
track versioned, packaged updates to Hubble's components.

The second method installs directly from git. It should be considered bleeding
edge and possibly unstable.

.. note:: Currently only supported on Linux, on SaltStack 2015.8 and above. You can actually sync the osquery execution module from a newer version of salt to 2015.5 minions and it seems to work without issue. Officially, just upgrade to 2015.8.

.. seealso:: Nebula has a hard dependency on the ``osqueryi`` binary. See install requirements here https://osquery.io/downloads/

Installation
============

Each of the four HubbleStack components have been packaged for use with Salt's
Package Manager (SPM). Note that all SPM installation commands should be done
on the *Salt Master*.

.. _nebula_installation_config:

**Required Configuration**

Salt's Package Manager (SPM) installs files into ``/srv/spm/{salt,pillar}``.
Ensure that this path is defined in your Salt Master's ``file_roots``:

.. code-block:: yaml

    file_roots:
      - /srv/salt
      - /srv/spm/salt

.. note:: This should be the default value. To verify run: ``salt-call config.get file_roots``

.. tip:: Remember to restart the Salt Master after making this change to the configuration.

.. _nebula_installation_packages:

Installation (Packages)
-----------------------

Installation is as easy as downloading and installing a package. (Note: in
future releases you'll be able to subscribe directly to our HubbleStack SPM
repo for updates and bugfixes!)

.. code-block:: shell

    wget https://spm.hubblestack.io/2016.7.1/hubblestack_nebula-2016.7.1-1.spm
    spm local install hubblestack_nebula-2016.7.1-1.spm

You should now be able to sync the new modules to your minion(s) using the
``sync_modules`` Salt utility:

.. code-block:: shell

    salt \* saltutil.sync_modules

Copy the ``hubblestack_nebula.sls.orig`` into your Salt pillar, dropping the
``.orig`` extension and target it to selected minions.

.. code-block:: shell

    base:
      '*':
        - hubblestack_nebula

.. code-block:: shell

    salt \* saltutil.refresh_pillar

Once these modules are synced you are ready to schedule HubbleStack Nebula
queries.

Skip to :ref:`Usage <nebula_usage>`

.. _nebula_installation_manual:

Installation (Manual)
---------------------

Place ``_modules/nebula_osquery.py`` into your ``salt/_modules/`` directory, and sync
it to the minions.

.. code-block:: shell

    git clone https://github.com/hubblestack/nebula.git hubblestack-nebula.git
    cd hubblestack-nebula.git
    mkdir -p /srv/salt/_modules/
    cp _modules/nebula_osquery.py /srv/salt/_modules/
    cp pillar.example /srv/pillar/hubblestack_nebula.sls

    salt \* saltutil.sync_modules

Target the ``hubblestack_nebula.sls`` to selected minions.

.. code-block:: shell

    base:
      '*':
        - hubblestack_nebula

.. code-block:: shell

    salt \* saltutil.refresh_pillar

Once these modules are synced you are ready to schedule HubbleStack Nebula
queries.

.. _nebula_usage:

Usage
=====

This module also requires pillar data to function. The default pillar key for
this data is ``nebula_osquery``.  The queries themselves should be grouped
under one or more group identifiers. Usually, these identifiers will be
frequencies, such as ``fifteen_min`` or ``hourly`` or ``daily``. The module
targets the queries using these identifiers.

Your pillar data might look like this:

**hubble_nebula.sls**

.. code-block:: yaml

    nebula_osquery:
      fifteen_min:
        - query_name: running_procs
          query: select p.name as process, p.pid as process_id, p.cmdline, p.cwd, p.on_disk, p.resident_size as mem_used, p.parent, g.groupname, u.username as user, p.path, h.md5, h.sha1, h.sha256 from processes as p left join users as u on p.uid=u.uid left join groups as g on p.gid=g.gid left join hash as h on p.path=h.path;
        - query_name: established_outbound
          query: select t.iso_8601 as _time, pos.family, h.*, ltrim(pos.local_address, ':f') as src, pos.local_port as src_port, pos.remote_port as dest_port, ltrim(remote_address, ':f') as dest, name, p.path as file_path, cmdline, pos.protocol, lp.protocol from process_open_sockets as pos join processes as p on p.pid=pos.pid left join time as t LEFT JOIN listening_ports as lp on lp.port=pos.local_port AND lp.protocol=pos.protocol LEFT JOIN hash as h on h.path=p.path where not remote_address='' and not remote_address='::' and not remote_address='0.0.0.0' and not remote_address='127.0.0.1' and port is NULL;
        - query_name: listening_procs
          query:  select t.iso_8601 as _time, h.md5 as md5, p.pid, name, ltrim(address, ':f') as address, port, p.path as file_path, cmdline, root, parent from listening_ports as lp JOIN processes as p on lp.pid=p.pid left JOIN time as t JOIN hash as h on h.path=p.path WHERE not address='127.0.0.1';
        - query_name: suid_binaries
          query: select sb.*, t.iso_8601 as _time from suid_bin as sb join time as t;
      hour:
        - query_name: crontab
          query: select c.*,t.iso_8601 as _time from crontab as c join time as t;
      day:
        - query_name: rpm_packages
          query: select rpm.*, t.iso_8601 from rpm_packages as rpm join time as t;

.. _nebula_usage_schedule:

Schedule
--------

Nebula is designed to be used on a schedule. Here is a set of sample schedules
for use with the sample pillar data contained in this repo:

**hubble_nebula.sls (cont.)**

.. code-block:: yaml

    schedule:
      nebula_fifteen_min:
        function: nebula.queries
        seconds: 900
        args:
          - fifteen_min
        returner: splunk_nebula_return
        return_job: False
        run_on_start: False
      nebula_hour:
        function: nebula.queries
        seconds: 3600
        args:
          - hour
        returner: splunk_nebula_return
        return_job: False
        run_on_start: False
      nebula_day:
        function: nebula.queries
        seconds: 86400
        args:
          - day
        returner: splunk_nebula_return
        return_job: False
        run_on_start: False

.. _nebula_configuration:

Configuration
=============

The only configuration required to use Nebula is to incorporate the Queries and
the Schedule into your minion config or pillar (pillar recommended). See the
Usage section above for more information.

.. _nebula_under_the_hood:

Under the Hood
==============

Nebula leverages the ``osquery_nebula`` execution module, which needs to be
synced to each minion. In addition, this also requires the ``osquery`` binary
to be installed.

More information about osquery can be found at https://osquery.io.

.. note:: ``osqueryd`` does not need to be running, as we handle the scheduled queries via Salt's scheduler.

.. _nebula_development:

Development
===========

Development for Nebula features is either incorporated into upstream osquery,
or comes in the form of additional queries that leverage existing features. If
you'd like to contribute queries or schedules, please see the section below.

.. _nebula_contribute:

Contribute
==========

If you are interested in contributing or offering feedback to this project feel
free to submit an issue or a pull request. We're very open to community
contribution.
