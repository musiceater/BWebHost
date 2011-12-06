#!/usr/bin/python2.6  
# -*- coding: utf-8 -*-

import xmldict


import funcLib
from member import Member
	
AllProperty = ['displayname','creationdate', 'resourcetype', 'supportedlock', 'href']
BasicProperty = ['displayname','creationdate', 'resourcetype', 'supportedlock']

# return (status, 'content')
	
def execute(req,depth, sharepath, curpath,webdavFolder):
	
	print 'args:',req,depth, sharepath, curpath,webdavFolder
	
	d = xmldict.builddict(req)
	
	wished_all = False
	wished_props = BasicProperty
	if len(d) == 0:
		wished_props = BasicProperty
	else:
		if 'allprop' in d['propfind']:
			wished_props = AllProperty
			wished_all = True
		else:
			wished_props = []
			for prop in d['propfind']['prop']:
				wished_props.append(prop)

				
	path, elem = funcLib.path_elem(sharepath, curpath)
	
	if not elem:
		print "path", repr(path), "elem", repr(elem), 'path', path
		if len(path) >= 1: # it's a non-existing file
			return (404, 'Not found')				
		else:
			elem = DirCollection(sharepath, '/') # fixup sharepath lookups?
	
	if depth != '0' and not elem or elem.type != Member.M_COLLECTION:
		return(406, 'This is not allowed')

	
	reponseContent = '<?xml version="1.0" encoding="utf-8"?>\n'
	reponseContent += '<D:multistatus xmlns:D="DAV:">\n'
	rep=''
	rep = write_props_member(elem,wished_all, wished_props)
	
	
	if depth == '1':
		for m in elem.getMembers():
			if curpath == '/':
				print 'name',m.name
				if m.name==webdavFolder:
					rep += write_props_member(m,wished_all, wished_props)
			else:
				rep += write_props_member(m,wished_all, wished_props)
	reponseContent += rep
	
	reponseContent += '</D:multistatus>'
   
	return (0, reponseContent)
	
def write_props_member(m, wished_all, wished_props):
	
	rep = '<D:response>\n'
	rep += '<D:href>%s</D:href>\n' % m.virname

	rep += '<D:propstat>\n' # return known properties
	rep += '<D:status>HTTP/1.1 200 OK</D:status>\n'
	rep += '<D:prop>\n'
	props = m.getProperties()
	returned_props = []
	
	for p in props: # write out properties
		if props[p] == None:
			rep += '  <D:%s/>\n' % p
		else:
			rep += '  <D:%s>%s</D:%s>\n' % (p, str(props[p]), p)
		returned_props.append(p)
	if m.type != Member.M_COLLECTION:
		rep += '  <D:resourcetype/>\n'
	else:
		rep += '  <D:resourcetype><D:collection/></D:resourcetype>\n'
	rep += '</D:prop>\n'
	rep += '</D:propstat>\n'
	
	if not wished_all and len(returned_props) < len(wished_props): # notify that some properties were not found
		rep += '<D:propstat>\n'
		rep += '<D:status>HTTP/1.1 404 Not found</D:status>\n'
		rep += '<D:prop>\n'
		for wp in wished_props:
			if not wp in returned_props:
				rep += '<D:%s/>' % wp
		rep += '</D:prop>\n'
		rep += '</D:propstat>\n'
	rep += '<D:lockdiscovery/>\n<D:supportedlock/>\n'
	rep += '</D:response>\n'	
	return rep
