# Copyright (c) 2005.-2006. Ivan Voras <ivoras@gmail.com>
# Released under the Artistic License

from time import time, timezone, strftime, localtime, gmtime


def unixdate2iso8601(d):
    tz = timezone / 3600 # can it be fractional?
    tz = '%+03d' % tz
    return strftime('%Y-%m-%dT%H:%M:%S', localtime(d)) + tz + ':00'

def unixdate2httpdate(d):
    return strftime('%a, %d %b %Y %H:%M:%S GMT', gmtime(d))
    

def dict2xml(d):
    r = ''
    for k in d:
        if d[k] != None:
            if type(d[k]) == type(d):
                r += '<%s>%s</%s>' % (k, dict2xml(d[k]), k)
            else:
                r += '<%s>%s</%s>' % (k, d[k], k)
        else:
            r += '<%s/>' % k
    return r

