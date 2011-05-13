from django import template

register = template.Library()

ACTIVE_TAB_NAME = 'tabsACTIVETABS'
DEFAULT_NAMESPACE = 'default'

def get_active_tabs(context):    
    active_tabs = template.Variable(ACTIVE_TAB_NAME)
    try:
        return active_tabs.resolve(context)
    except template.VariableDoesNotExist:
        return {}

def set_active_tab(context, namespace, name):
    active_tabs = get_active_tabs(context)
    active_tabs[namespace] = name
    context[ACTIVE_TAB_NAME] = active_tabs
    
def is_active_tab(context, namespace, name):
    active_tabs = get_active_tabs(context)
    if namespace in active_tabs and active_tabs[namespace]==name:
        return True
    return False

    
class ActiveTabNode(template.Node):
    
    def __init__(self, name, namespace=None):
        if namespace is None:
            namespace = DEFAULT_NAMESPACE
        self.namespace = template.Variable(namespace)
        self.name = template.Variable(name)

        
    def render(self, context):
        try:
            namespace = self.namespace.resolve(context)
        except template.VariableDoesNotExist:
            namespace = None
        try:
            name = self.name.resolve(context)
        except template.VariableDoesNotExist(context):
            name = None

        set_active_tab(context, namespace, name)
        return ''

class IfActiveTabNode(template.Node):
    def __init__(self, nodelist_true, nodelist_false, name, namespace=None):
        if namespace is None:
            namespace = DEFAULT_NAMESPACE
            
        self.namespace = template.Variable(namespace)
        self.name = template.Variable(name)
        
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false
        
    def render(self, context):
        try:
            namespace = self.namespace.resolve(context)
        except template.VariableDoesNotExist:
            namespace = None
        try:
            name = self.name.resolve(context)
        except template.VariableDoesNotExist(context):
            name = None
            
        if is_active_tab(context, namespace, name):
            return self.nodelist_true.render(context)
        return self.nodelist_false.render(context)

def activetab(parser, token):
    bits = token.contents.split()[1:]
    if len(bits) not in (1, 2):
        raise template.TemplateSyntaxError, "Invalid number of arguments"
    if len(bits) == 1:
        namespace = None
        name = bits[0]
    else:
        namespace = bits[0]
        name = bits[1]
        
    return ActiveTabNode(name, namespace)
activetab = register.tag('activetab', activetab)

def ifactivetab(parser, token):
    bits = token.contents.split()[1:]
    nodelist_true = parser.parse(('else', 'endifactivetab'))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse(('endifactivetab',))
        parser.delete_first_token()
    else:
        nodelist_false = template.NodeList()
    if len(bits) not in (1, 2):
        raise template.TemplateSyntaxError, "Invalid number of arguments"
    if len(bits) == 1:
        namespace = None
        name = bits[0]
    else:
        namespace = bits[0]
        name = bits[1]
    return IfActiveTabNode(nodelist_true, nodelist_false, name, namespace)

ifactivetab = register.tag('ifactivetab', ifactivetab)

