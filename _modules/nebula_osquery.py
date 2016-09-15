# -*- coding: utf-8 -*-
'''
osquery wrapper for HubbleStack Nebula

:maintainer: basepi
:maturity: 20160517
:platform: All
:requires: SaltStack, osquery

Designed to run sets of osquery queries defined in pillar. These sets will have
a unique identifier, and be targeted by identifier. Usually, this identifier
will be a frequency. ('15 minutes', '1 day', etc). Identifiers are
case-insensitive.

You can then use the scheduler of your choice to run sets os queries at
whatever frequency you choose.

Sample pillar data:

nebula_osquery:
  hour:
    - crontab: query: select c.*,t.iso_8601 as _time from crontab as c join time as t;
    - query_name: suid_binaries
      query: select sb.*, t.iso_8601 as _time from suid_bin as sb join time as t;
  day:
    - query_name: rpm_packages
      query: select rpm.*, t.iso_8601 from rpm_packages as rpm join time as t;
'''
from __future__ import absolute_import

import copy
import logging
import yaml

import salt.utils
from salt.exceptions import CommandExecutionError

log = logging.getLogger(__name__)

__virtualname__ = 'nebula'


def __virtual__():
    if salt.utils.is_windows():
        return False, 'Windows not supported'
    if 'osquery.query' not in __salt__:
        return False, 'osquery not available'
    return __virtualname__


def queries(query_group,
            query_file='salt://hubblestack_nebula/hubblestack_nebula_queries.yaml',
            verbose=False):
    '''
    Run the set of queries represented by ``query_group`` from the
    configuration in the file query_file

    query_group
        Group of queries to run

    query_file
        salt:// file which will be parsed for osquery queries

    verbose
        Defaults to False. If set to True, more information (such as the query
        which was run) will be included in the result.

    CLI Examples:

    .. code_block:: bash

        salt '*' nebula.queries day
        salt '*' nebula.queries hour verbose=True
        salt '*' nebula.queries hour pillar_key=sec_osqueries
    '''
    query_file = __salt__['cp.cache_file'](query_file)
    with open(query_file, 'r') as fh:
        query_data = yaml.safe_load(fh)

    if not isinstance(query_data, dict):
        raise CommandExecutionError('Query data is not formed as a dict {0}'
                                    .format(query_data))

    query_data = query_data.get(query_group, [])

    if not query_data:
        return None

    ret = []
    for query in query_data:
        name = query.get('query_name')
        query_sql = query.get('query')
        if not query_sql:
            continue
        query_ret = __salt__['osquery.query'](query_sql)
        if verbose:
            tmp = copy.deepcopy(query)
            tmp['query_result'] = query_ret
            ret.append(tmp)
        else:
            ret.append({name: query_ret})

    return ret
