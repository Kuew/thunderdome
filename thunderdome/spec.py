import json


class Property(object):
    """Abstracts a property parsed from a spec file."""

    def __init__(self, name, data_type, functional=False):
        """
        Defines a property parsed from a spec file.

        :param name: The name of the property
        :type name: str
        :param data_type: The Java data type to be used for this property
        :type data_type: str
        :param functional: Indicates whether or not this is a functional property
        :type functional: boolean
        
        """
        self.name = name
        self.data_type = data_type
        self.functional = functional

    @property
    def gremlin(self):
        """
        Return the gremlin code for creating this property.

        :rtype: str
        
        """
        initial = '{} = g.makeType().name("{}").dataType({}.class).{}makePropertyKey()'
        func = ''
        if self.functional:
            func = 'functional().'
        return initial.format(self.name, self.name, self.data_type, func)


class Edge(object):
    """Abstracts an edge parsed from a spec file."""

    def __init__(self, label, primary_key=None):
        """
        Defines an edge parsed from a spec file.

        :param label: The label for this edge
        :type label: str
        :param primary_key: The primary key for this edge
        :type primary_key: thunderdome.spec.Property or None
        
        """
        self.label = label
        self.primary_key = primary_key

    @property
    def gremlin(self):
        """
        Return the gremlin code for creating this edge.

        :rtype: str
        
        """
        initial = '{} = g.makeType().name("{}").{}makeEdgeLabel()'
        primary_key = ''
        if self.primary_key:
            primary_key = "primaryKey({}).".format(self.primary_key)
        return initial.format(self.label, self.label, primary_key)
    

class SpecParser(object):
    """
    Parser for a spec file describing properties and primary keys for edges.
    This file is used to ensure duplicate primary keys are not created.

    File format:

    [
        {
            "type":"property",
            "name":"updated_at",
            "data_type":"Integer",
            "functional":true
        },
        {
            "type":"edge",
            "label":"subscribed_to",
            "primary_key":"updated_at"
        } 
    ]

    """

    def __init__(self, filename=None):
        """
        Pass in the 
        
        :param filename: The path to the file to be parsed
        :type filename: str
        
        """
        self._specs = self._load_spec(filename)
        self._properties = {}

    def _load_spec(self, filename=None):
        """
        Loads the spec with the given filename or returns an empty
        list.

        :param filename: The filename to be opened (optional)
        :type filename: str or None
        :rtype: list
        
        """
        specs = []
        if filename:
            with open(filename) as spec_file:
                specs = json.load(spec_file)
        return specs

    def parse(self):
        """
        Parse the internal spec and return a list of gremlin statements.

        :rtype: list
        
        """
        self._properties = {}

        self._results = [self.parse_statement(x) for x in self._specs]
        self.validate(self._results)
        return self._results

    def validate(self, results):
        """
        Validate the given set of results.

        :param results: List of parsed objects
        :type results: list
        
        """
        edges = [x for x in results if isinstance(x, Edge)]
        props = {x.name: x for x in results if isinstance(x, Property)}

        for e in edges:
            if e.primary_key and e.primary_key not in props:
                raise ValueError('Missing primary key {} for edge {}'.format(e.primary_key, e.label))

    def parse_property(self, stmt):
        """
        Build object for a new property type.

        :param stmt: The statement to be parsed
        :type stmt: str

        :rtype: thunderdome.spec.Property

        """
        if stmt['name'] in self._properties:
            raise ValueError('There is already a property called {}'.format(stmt['name']))
        prop = Property(name=stmt['name'],
                        data_type=stmt['data_type'],
                        functional=stmt.get('functional', False))
        self._properties[prop.name] = prop
        return prop

    def parse_edge(self, stmt):
        """
        Build object for a new edge with a primary key.

        :param stmt: The statement to be parsed
        :type stmt: str

        :rtype: thunderdome.spec.Edge
        
        """
        return Edge(label=stmt['label'],
                    primary_key=stmt.get('primary_key', None))

    def parse_statement(self, stmt):
        """
        Takes the given spec statement and converts it into an object.

        :param stmt: The statement
        :type stmt: dict

        :rtype: thunderdome.spec.Property or thunderdome.spec.Edge

        """
        if 'type' not in stmt:
            raise TypeError('Type field required')

        if stmt['type'] == 'property':
            return self.parse_property(stmt)
        elif stmt['type'] == 'edge':
            return self.parse_edge(stmt)
        else:
            raise ValueError('Invalid `type` value {}'.format(stmt['type']))

        
class Spec(object):
    """Represents a generic type spec for thunderdome."""

    def __init__(self, filename):
        """
        Parse and attempt to initialize the spec with the contents of the given
        file.

        :param filename: The spec file to be parsed
        :type filename: str
        
        """
        self._results = SpecParser(filename).parse()

    def sync(self, host, graph_name, username=None, password=None):
        """
        Sync the current internal spec using the given graph on the given host.

        :param host: The host in <hostname>:<port> or <hostname> format
        :type host: str
        :param graph_name: The name of the graph as defined in rexster.xml
        :type graph_name: str
        :param username: The username for the rexster server
        :type username: str
        :param password: The password for the rexster server
        :type password: str
        
        """
        from thunderdome.connection import setup, execute_query
        setup(hosts=[host],
              graph_name=graph_name,
              username=username,
              password=password,
              index_all_fields=False)
        
        q = ""
        for stmt in self._results:
            q += "{}\n".format(stmt.gremlin)
        q += "g.stopTransaction(SUCCESS)"
    
        execute_query(q)

    def _get_types(self, types):
        """
        Returns the types of all the defined types from the current spec.

        :param types: All types defined in the current spec
        :type types: list

        :rtype: dict
        
        """
        q  = "results = [:]\n"
        q += "for (x in names) {\n"
        q += "  t = g.getType(x)\n"
        q += "  if (t == null) { break }\n"
        q += "  results[x] = [data_type: t.getDataType(), functional: t.isFunctional()]\n"
        q += "}\n"
        q += "results"

        names = [x.name if isinstance(x, Property) else x.label for x in self._results]

        from thunderdome.connection import execute_query
        return execute_query(q, {'names': names})
