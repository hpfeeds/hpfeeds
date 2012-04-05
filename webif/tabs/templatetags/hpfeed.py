from django import template
from models import Channel

register = template.Library()

@register.filter(name='access_chan_user')
def access_chan_user(chan, user):
	return chan.access_user(user)

@register.filter(name='access_chan_name_user')
def access_chan_name_user(chan, user):
	return Channel.objects.get(name=chan).access_user(user)

from django.conf import settings
from django.utils.encoding import smart_str, force_unicode
from django.utils.safestring import mark_safe

@register.filter
def bbcode(value):
    """
    Generates (X)HTML from string with BBCode "markup".
    By using the postmark lib from:
    @see: http://code.google.com/p/postmarkup/
    
    """ 
    try:
        from postmarkup import render_bbcode
    except ImportError:
        if settings.DEBUG:
            raise template.TemplateSyntaxError, "Error in {% bbcode %} filter: The Python postmarkup library isn't installed."
        return force_unicode(value)
    else:
        return mark_safe(render_bbcode(value, auto_urls=False))
bbcode.is_save = True

@register.filter
def strip_bbcode(value):
    """ 
    Strips BBCode tags from a string
    By using the postmark lib from: 
    @see: http://code.google.com/p/postmarkup/
    
    """ 
    try:
        from postmarkup import strip_bbcode
    except ImportError:
        if settings.DEBUG:
            raise template.TemplateSyntaxError, "Error in {% bbcode %} filter: The Python postmarkup library isn't installed."
        return force_unicode(value)
    else:
        return mark_safe(strip_bbcode(value))
bbcode.is_save = True

