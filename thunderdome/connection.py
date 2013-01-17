#http://pypi.python.org/pypi/cql/1.0.4
#http://code.google.com/a/apache-extras.org/p/cassandra-dbapi2 /
#http://cassandra.apache.org/doc/cql/CQL.html

from collections import namedtuple
import httplib
import json
import logging
import Queue
import random
import textwrap

from thunderdome.exceptions import ThunderdomeException

logger = logging.getLogger(__name__)

class ThunderdomeConnectionError(ThunderdomeException): pass
class ThunderdomeQueryError(ThunderdomeException): pass

Host = namedtuple('Host', ['name', 'port'])
_hosts = []
_host_idx = 0
_graph_name = None
_username = None
_password = None
_index_all_fields = True

def create_key_index(name):
    """
    Creates a key index if it does not already exist
    """
    existing = execute_query('g.getIndexedKeys(Vertex.class)')
    if name not in existing:
        execute_query(
            "g.createKeyIndex(keyname, Vertex.class); g.stopTransaction(SUCCESS)",
            {'keyname':name}, transaction=False)

def setup(hosts, graph_name, username=None, password=None, index_all_fields=True):
    """
    Records the hosts and connects to one of 

    :param hosts: list of hosts, strings in the <hostname>:<port>, or just <hostname>
    :param graph_name:
    :param index_all_fields: all vertex fields will be indexed if this is set to True, otherwise they must be set manually
    """
    global _hosts
    global _graph_name
    global _username
    global _password
    global _index_all_fields
    _graph_name = graph_name
    _username = username
    _password = password
    _index_all_fields = index_all_fields
    
    for host in hosts:
        host = host.strip()
        host = host.split(':')
        if len(host) == 1:
            _hosts.append(Host(host[0], 8182))
        elif len(host) == 2:
            _hosts.append(Host(*host))
        else:
            raise ThunderdomeConnectionError("Can't parse {}".format(''.join(host)))

    if not _hosts:
        raise ThunderdomeConnectionError("At least one host required")

    random.shuffle(_hosts)
    for idx in ['vid', 'element_type']:
        create_key_index(idx)

    #index any models that have already been defined
    from thunderdome.models import vertex_types
    for klass in vertex_types.values():
        klass._create_indices()
    
    
def execute_query(query, params={}, transaction=True):
    if transaction:
        query = 'g.stopTransaction(FAILURE)\n' + query

    host = _hosts[0]
    #url = 'http://{}/graphs/{}/tp/gremlin'.format(host.name, _graph_name)
    data = json.dumps({'script':query, 'params': params})
    headers = {'Content-Type':'application/json', 'Accept':'application/json'}

    conn = httplib.HTTPConnection(host.name, host.port)
    conn.request("POST", '/graphs/{}/tp/gremlin'.format(_graph_name), data, headers)
    response = conn.getresponse()
    content = response.read()

    
    logger.info(json.dumps(data))
    logger.info(content)

    response_data = json.loads(content)
    
    if response.status != 200:
        raise ThunderdomeQueryError(response_data['error'])

    return response_data['results'] 


