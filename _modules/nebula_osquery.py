# -*- coding: utf-8 -*-
'''
osquery wrapper for HubbleStack Nebula

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
import salt.utils

import logging
log = logging.getLogger(__name__)

__virtualname__ = 'nebula'


def __virtual__():
    if salt.utils.is_windows():
        return False, 'Windows not supported'
    if 'osquery.query' not in __salt__:
        return False, 'osquery not available'
    return __virtualname__


def queries(query_group, verbose=False, pillar_key='nebula_osquery'):
    '''
    Run the set of queries represented by ``query_group`` from the
    configuration in the pillar key ``nebular_osquery``.

    CLI Examples:

    .. code_block:: bash

        salt '*' nebula.queries day
        salt '*' nebula.queries hour verbose=True
        salt '*' nebula.queries hour pillar_key=sec_osqueries
    '''
    query_data = __salt__['pillar.get']('{0}:{1}'.format(pillar_key, query_group), [])

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
