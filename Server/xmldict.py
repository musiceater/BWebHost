# A sane XML-to-objects parser
# TODO: error & better malformed xml handling
# (c) 2005. Ivan Voras
import sys
import re

class Tag:

    def __init__(self, name, attrs, data='', parser=None):
        self.d = {}
        self.name = name
        self.attrs = attrs
        if type(self.attrs) == type(''):
            self.attrs = splitattrs(self.attrs)
        for a in self.attrs:
            if a.startswith('xmlns'):
                nsname = a[6:]
                parser.namespaces[nsname] = self.attrs[a]
        self.rawname = self.name

        p = name.find(':')
        if p > 0:
            nsname = name[0:p]
            if nsname in parser.namespaces:
                self.ns = parser.namespaces[nsname]
                self.name = self.rawname[p+1:]
        else:
            self.ns = ''
        #print self.rawname, '->', self.name, self.ns
        self.data = data

    # Emulate dictionary d
    def __len__(self):
        return len(self.d)

    def __getitem__(self, key):
        return self.d[key]

    def __setitem__(self, key, value):
        self.d[key] = value

    def __delitem__(self, key):
        del self.d[key]

    def __iter__(self):
        return self.d.iterkeys()

    def __contains__(self, key):
        return key in self.d

    def __str__(self):
        """Returns unicode semi human-readable representation of the structure"""
        if self.attrs:
            s = u'<%s %s> %s ' % (self.name, self.attrs, self.data)
        else:
            s = u'<%s> %s ' % (self.name, self.data)

        for k in self.d:
            if type(self.d[k]) == type(self):
                s += u'|%s: %s|' % (k, str(self.d[k]))
            else:
                s += u'|' + u','.join([str(x) for x in self.d[k]]) + u'|'
        return s


    def addChild(self, tag):
        """Adds a child to self. tag must be instance of Tag"""
        if tag.name in self.d:
            if type(self.d[tag.name]) == type(self): # If there are multiple sibiling tags with same name, form a list :)
                self.d[tag.name] = [self.d[tag.name]]
            self.d[tag.name].append(tag)
        else:
            self.d[tag.name] = tag
        return tag


    def toUnicode(self, fromencoding, recurse=True):
        """Converts data & attribute data to unicode from specified encoding"""
        if type(self.data) == type(''):
            self.data = self.data.decode(fromencoding, 'replace')
        for a in self.attrs:
            if type(self.attrs[a] == type('')):
                self.attrs[a] = self.attrs[a].decode(fromencoding, 'replace')
        if recurse:
            for k in self.d:
                if type(self.d[k]) == type(self):
                    self.d[k].toUnicode(fromencoding, recurse)



class XMLDict_Parser:

    def __init__(self, xml):
        self.xml = xml
        self.p = 0
        self.encoding = sys.getdefaultencoding()
        self.namespaces = {}


    def getnexttag(self):
        ptag = self.xml.find('<', self.p)
        if ptag < 0:
            return None, None, self.xml[self.p:].strip()

        data = self.xml[self.p:ptag].strip()

        self.p = ptag
        self.tagbegin = ptag

        p2 = self.xml.find('>', self.p+1)
        if p2 < 0:
            raise "Malformed XML - unclosed tag?"

        tag = self.xml[ptag+1:p2]
        self.p = p2+1
        self.tagend = p2+1

        ps = tag.find(' ')
        if ps > 0:
            tag, attrs = tag.split(' ', 1)
        else:
            attrs = ''

        return tag, attrs, data


    def builddict(self):
        """Builds a nested-dictionary-like structure from the xml. This method
        picks up tags on the main level and calls processTag() for nested tags."""
        d = Tag('<root>', '')
        while True:
            tag, attrs, data = self.getnexttag()
            if data != '': # data is actually that between the last tag and this one
                sys.stderr.write("Warning: inline data between tags?!\n")
            if not tag:
                break
            if tag[-1] == '/': # an 'empty' tag (e.g. <empty/>)
                d.addChild(Tag(tag[:-1], attrs, parser=self))
                continue
            elif tag[0] == '?': # special tag
                t = d.addChild(Tag(tag, attrs, parser=self))
                if tag == '?xml' and 'encoding' in t.attrs:
                    self.encoding = t.attrs['encoding']
            else:
                try:
                    self.processTag(d.addChild(Tag(tag, attrs, parser=self)))
                except:
                    sys.stderr.write("Error processing tag %s\n" % tag)
        d.encoding = self.encoding
        return d


    def processTag(self, dtag):
        """Process single tag's data"""
        until = '/'+dtag.rawname
        while True:
            tag, attrs, data = self.getnexttag()
            if data:
                dtag.data += data
            if tag == None:
                sys.stderr.write("Unterminated tag '"+dtag.rawname+"'?\n")
                break
            if tag == until:
                break
            if tag[-1] == '/':
                dtag.addChild(Tag(tag[:-1], attrs, parser=self))
                continue
            self.processTag(dtag.addChild(Tag(tag, attrs, parser=self)))


def splitattrs(att):
    """Extracts name="value" pairs from string; returns them as dictionary"""
    d = {}
    for m in re.findall('([a-zA-Z_][a-zA-Z_:0-9]*?)="(.+?)"', att):
        d[m[0]] = m[1]
    return d


def builddict(xml):
    """Wrapper function for straightforward parsing"""
    p = XMLDict_Parser(xml)
    return p.builddict()


if __name__ == '__main__': # functionality test
    p = XMLDict_Parser('<tag1>text</tag1>')
    d = p.builddict()
    print d
    print "Contents of tag1 is: '%s'" % d['tag1'].data
    p = XMLDict_Parser('<group><user>joe</user><user>nick</user><user>john</user></group>')
    d = p.builddict()
    print d
    print 'users are:'
    for u in d['group']['user']:
        print u
#    print d['group']
#    print d['group'].d
    p = XMLDict_Parser('<group><user/><user/><user/></group>')
    d = p.builddict()
    print d
#    print d['group'].d
    p = XMLDict_Parser('<users><joe/><nick/><john/></users>')
    d = p.builddict()
    print d
    if 'joe' in d['users']:
        print 'have no fear, joe is near.'
    if 'george' in d['users']:
        print 'george is evil'
    print 'users are:'
    for u in d['users']:
        print u

