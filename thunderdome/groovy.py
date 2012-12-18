import collections
import pyparsing
import re


class GroovyFunctionParser(object):
    """
    Given a string containing a single function definition this class will 
    parse the function definition and return information regarding it.
    """

    # Simple Groovy sub-grammar definitions
    KeywordDef  = pyparsing.Keyword('def')
    VarName     = pyparsing.Regex(r'[A-Za-z0-9]\w*')
    FuncName    = VarName
    StmtList    = pyparsing.Regex(r'.*')
    FuncDefn    = KeywordDef + FuncName + "(" + pyparsing.delimitedList(VarName) + ")" + "{"
    
    # Result named tuple
    GroovyFunction = collections.namedtuple('GroovyFunction', ['name', 'args', 'body', 'defn'])
    
    @classmethod
    def parse(cls, data):
        """
        Parse the given function definition and return information regarding
        the contained definition.
        
        :param data: The function definition in a string
        :type data: str
        :rtype: dict
        
        """
        try:
            # Parse the function here
            result = cls.FuncDefn.parseString(data)
            result_list = result.asList()
            args = result_list[3:result_list.index(')')]
            # Return single line or multi-line function body
            fn_body = re.sub(r'\}$', '', re.sub(r'[^\{]+\{', '', data))
            return cls.GroovyFunction(result[1], args, fn_body, data)
        except:
            return {}
        

def parse(file):
    """
    Parse Groovy code in the given file and return a list of information about
    each function necessary for usage in queries to database.
    
    :param file: The file containing groovy code.
    :type file: str
    :rtype: 
    
    """
    FuncDefnRegexp = r'^def.*\{'
    FuncEndRegexp = r'^\}$'
    with open(file, 'r') as f:
        data = f.read()
    file_lines = data.split("\n")
    all_fns = []
    fn_lines = ''
    for line in file_lines:
        if len(fn_lines) > 0:
            if re.match(FuncEndRegexp, line):
                fn_lines += line + "\n"
                all_fns.append(fn_lines)
                fn_lines = ''
            else:
                fn_lines += line + "\n"
        elif re.match(FuncDefnRegexp, line):
            fn_lines += line + "\n"
            
    func_results = []
    for fn in all_fns:
        func_results += [GroovyFunctionParser.parse(fn)]
    return func_results