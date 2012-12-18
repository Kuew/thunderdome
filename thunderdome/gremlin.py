import inspect
import os.path

from thunderdome.connection import execute_query
from thunderdome.exceptions import ThunderdomeException
from thunderdome.groovy import parse

class ThunderdomeGremlinException(ThunderdomeException):pass

class BaseGremlinMethod(object):
    
    def __init__(self, path=None, method_name=None, classmethod=False, default_args={}):
        """
        :param path: path to the source gremlin file, relative to the file the class is defined in
            absolute paths also work, defaults to gremlin.groovy if left blank
        :param method_name: the name of the function definition in the groovy file.
            defaults to the attribute name this is instantiated on
        :param classmethod: method will behave as a classmethod if this is True, defaults to False
        :param default_args: default values for arguments
        """
        self.is_configured = False
        self.path = path or 'gremlin.groovy'
        self.method_name = method_name
        self.classmethod = classmethod
        self.default_args = default_args
        
        self.attr_name = None
        self.arg_list = []
        self.function_body = None
        self.function_def = None
        
    def configure_method(self, klass, attr_name):
        """
        Configures the methods internals
        
        :param klass: the class object this function is being added onto
        :param attr_name: the attribute name this function is being added to the class as
        """
        self.attr_name = attr_name
        self.method_name = self.method_name or self.attr_name
        if not self.is_configured:
            if self.path.startswith('/'):
                path = self.path
            else:
                path = inspect.getfile(klass)
                path = os.path.split(path)[0]
                path += '/' + self.path
                
            #TODO: make this less naive
            gremlin_obj = None
            for grem_obj in parse(path):
                if grem_obj.name == self.method_name:
                    gremlin_obj = grem_obj
                    break
                
            if gremlin_obj is None:
                raise ThunderdomeGremlinException("The method'{}' wasnt found in {}".format(self.method_name, path))
            
            for arg in gremlin_obj.args:
                if arg in self.arg_list:
                    raise ThunderdomeGremlinException("'{}' defined more than once in gremlin method arguments".format(arg))
                self.arg_list.append(arg)
            
            self.function_body = gremlin_obj.body
            self.function_def = gremlin_obj.defn
        
    def __call__(self, instance, *args, **kwargs):
        args = list(args)
        if not self.classmethod:
            args = [instance.eid] + args
            
        params = self.default_args.copy()
        if len(args + kwargs.values()) > len(self.arg_list):
            raise TypeError('{}() takes {} args, {} given'.format(self.attr_name, len(self.arg_list), len(args)))
        
        arglist = self.arg_list[:]
        for arg in args:
            params[arglist.pop(0)] = arg
            
        for k,v in kwargs.items():
            if k not in arglist:
                an = self.attr_name
                if k in params:
                    raise TypeError(
                        "{}() got multiple values for keyword argument '{}'".format(an, k))
                else:
                    raise TypeError(
                        "{}() got an unexpected keyword argument '{}'".format(an, k))
            arglist.pop(arglist.index(k))
            params[k] = v
            
        return execute_query(self.function_body, params)
    
class GremlinMethod(BaseGremlinMethod):
    
    def __call__(self, instance, *args, **kwargs):
        from thunderdome.models import Element
        results = super(GremlinMethod, self).__call__(instance, *args, **kwargs)
        return [Element.deserialize(r) for r in results]
        