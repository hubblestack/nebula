THIS REPO IS DEPRECATED. PLEASE USE https://github.com/hubblestack/hubble-salt

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

    wget https://spm.hubblestack.io/nebula/hubblestack_nebula-2016.10.2-1.spm
    spm local install hubblestack_nebula-2016.10.2-1.spm

You should now be able to sync the new modules to your minion(s) using the
``sync_modules`` Salt utility:

.. code-block:: shell

    salt \* saltutil.sync_modules

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
    mkdir /srv/salt/hubblestack_nebula
    cp hubblestack_nebula/hubblestack_nebula_queries.yaml /srv/salt/hubblestack_nebula

    salt \* saltutil.sync_modules

Once these modules are synced you are ready to schedule HubbleStack Nebula
queries.

.. _nebula_installation_gitfs:

Installation (GitFS)
--------------------

This installation method subscribes directly to our GitHub repository, pinning
to a tag or branch. This method requires no package installation or manual
checkouts.

Requirements: GitFS support on your Salt Master.

**/etc/salt/master.d/hubblestack-nebula.conf**

.. code-block:: diff

    gitfs_remotes:
      - https://github.com/hubblestack/nebula:
        - base: v2016.10.2

.. tip:: Remember to restart the Salt Master after applying this change.

.. _nebula_usage:

Usage
=====

These queries have been designed to give detailed insight into system activity.

**hubblestack_nebula/hubblestack_nebula_queries.yaml**

.. code-block:: yaml

    fifteen_min:
      - query_name: running_procs
        query: SELECT p.name AS process, p.pid AS process_id, p.cmdline, p.cwd, p.on_disk, p.resident_size AS mem_used, p.parent, g.groupname, u.username AS user, p.path, h.md5, h.sha1, h.sha256 FROM processes AS p LEFT JOIN users AS u ON p.uid=u.uid LEFT JOIN groups AS g ON p.gid=g.gid LEFT JOIN hash AS h ON p.path=h.path;
      - query_name: established_outbound
        query: SELECT t.iso_8601 AS _time, pos.family, h.*, ltrim(pos.local_address, ':f') AS src, pos.local_port AS src_port, pos.remote_port AS dest_port, ltrim(remote_address, ':f') AS dest, name, p.path AS file_path, cmdline, pos.protocol, lp.protocol FROM process_open_sockets AS pos JOIN processes AS p ON p.pid=pos.pid LEFT JOIN time AS t LEFT JOIN (SELECT * FROM listening_ports) AS lp ON lp.port=pos.local_port AND lp.protocol=pos.protocol LEFT JOIN hash AS h ON h.path=p.path WHERE NOT remote_address='' AND NOT remote_address='::' AND NOT remote_address='0.0.0.0' AND NOT remote_address='127.0.0.1' AND port is NULL;
      - query_name: listening_procs
        query:  SELECT t.iso_8601 AS _time, h.md5 AS md5, p.pid, name, ltrim(address, ':f') AS address, port, p.path AS file_path, cmdline, root, parent FROM listening_ports AS lp LEFT JOIN processes AS p ON lp.pid=p.pid LEFT JOIN time AS t LEFT JOIN hash AS h ON h.path=p.path WHERE NOT address='127.0.0.1';
      - query_name: suid_binaries
        query: SELECT sb.*, t.iso_8601 AS _time FROM suid_bin AS sb JOIN time AS t;
    hour:
      - query_name: crontab
        query: SELECT c.*,t.iso_8601 AS _time FROM crontab AS c JOIN time AS t;
    day:
      - query_name: rpm_packages
        query: SELECT rpm.name, rpm.version, rpm.release, rpm.source AS package_source, rpm.size, rpm.sha1, rpm.arch, t.iso_8601 FROM rpm_packages AS rpm JOIN time AS t;

.. _nebula_usage_schedule:

Schedule
--------

Nebula is meant to be run on a schedule. Unfortunately, in it's present state,
the Salt scheduler has a memory leak. Pending a solution we're suggesting the
use of cron for the scheduled jobs:

**/etc/cron.d/hubble**

.. code-block:: yaml

    MAILTO=""
    SHELL=/bin/bash
    */15 * * * * root /usr/bin/salt '*' nebula.queries fifteen_min --return splunk_nebula_return
    @hourly      root /usr/bin/salt '*' nebula.queries hour --return splunk_nebula_return
    @daily       root /usr/bin/salt '*' nebula.queries day --return splunk_nebula_return

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
