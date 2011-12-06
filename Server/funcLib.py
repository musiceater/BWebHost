#!/usr/bin/python2.6  
# -*- coding: utf-8 -*-
import string,os,time
import json
from member import Member
from collection import Collection
import os.path, os
import md5
import dircache
from util import *
import mimetypes
import urllib
import base64
"""
	Import python module for further use.
"""
import sys
sys.path.append("/root/pHttpServer/CGI/Agent")
import getpool

"""
	command , python funciton mapping
"""
funcMapping = { 'getpool': getpool.execute}

"""
	Returns username and password
"""
def getUsernamePassword(str_tmp):
	str=''
	if str_tmp.find('Basic')!=-1:
		str = str_tmp.split()[1:][0]
	else:
		str = str_tmp
	return base64.b64decode(str).split(':')

def getSupportMethod():
	return 'GET,HEAD,PUT,DELETE,\
MKCOL,PROPFIND,PROPPATCH,\
LOCK,UNLOCK,COPY,MOVE,OPTIONS'

def getSupportLevel():
		return '1,2'		
		
# return empty string '' for nothing found
def getHTMLFile(curdir, path):
	defaultAppendix = ['html','htm']
	
	idx = path.find('?')
	if idx != -1:	path = path[:path.find('?')]
		
	print 'no ? path =',path
	if path == '/':
		# Check for existence of default files.
		for item in defaultAppendix:
			#print curdir+path+'index.'+item
			if os.path.isfile(curdir+path+'index.'+item) == True:
				return curdir+path+'index.'+item
	else:
		if os.path.isfile(curdir+path) == True:	
			return curdir+path
		# Append html or htm as default if we can't find any match for given filename
		for item in defaultAppendix:
			# handle htm <-> html
			idx = path.find('.htm')
			if idx != -1:	path = path[:path.index('.htm')]
			print 'handled path',path
			if os.path.isfile(curdir+path+'.'+item) == True:
				return curdir+path+'.'+item	
	return ''

def getParms(path):
	idx = path.find('?')
	if idx == -1: return []
	parms = path[path.find('?')+1:]
	return parms.split('&')

def split_path(path):
	p = path.split('/')[1:]
	while p and p[-1] in ('','/'):
		p = p[:-1]
		if len(p) > 0:
			p[-1] += '/'
	return p

def path_elem(sharepath, curpath):	   
	print 'search path',sharepath+curpath[1:]
	print 'file exist:',os.path.exists(sharepath+curpath[1:])
	#path = split_path(urllib.unquote(curpath))
	path = split_path(curpath)
	print 'unit path:', urllib.unquote(curpath)
	
	if not os.path.exists(sharepath+curpath[1:]):
		return (path, None)
	
	
	elem = DirCollection(sharepath)
	
	
	for e in path:
		elem = elem.findMember(e)
		if elem == None:
			break
	return (path, elem)

def getFilenameAndPath(path):
	paths = split_path(path)
	filename = paths[len(paths)-1]
	paths = paths[0:len(paths)-1]
	newpath='/'
	for dir in paths:
		if dir != '':
			newpath = newpath + dir + '/' 
	return (filename,newpath)
	
#  args contains python module name and arguments that need 
# to pass to the module.
#	status = 0 : no error
#		   = -1 : function not found	
def callFunc(page,args):
	status = 0
	output = ''
	
	if len(args) == 0:	return (status, output)
	
	# Handle all command, this should be huge
	print 'args', args
	cmd = args[0]
	print 'cmd', cmd
	parms = args[1:]
	print 'parms', parms
	try:
		return (status, funcMapping[cmd]())
	except:
		return (-1,'')
	return (status, output)

	
def saveFile(path,rfile, size):
	print 'save file',path
	filename, newpath = getFilenameAndPath(path)
	fname = os.path.join(newpath, filename)
	f = file(fname, 'wb')
	writ = 0
	bs = 65536
	while True:
		if size != -1 and (bs > size-writ):
			bs = size-writ
			buf = rfile.read(bs)
			if len(buf) == 0:
				break
			f.write(buf)
			writ += len(buf)
		if size != -1 and writ >= size:
			break
	f.close()
	return 0
	
class FileMember(Member):

	def __init__(self, name, parent):
		self.name = name
		self.parent = parent
		self.name = name
		self.fsname = parent.fsname + name # e.g. '/var/www/mysite/some.txt'
		self.virname = parent.virname + name # e.g. '/mysite/some.txt'
		self.type = Member.M_MEMBER

	def __str__(self):
		return "%s -> %s" % (self.virname, self.fsname)

	def getProperties(self):
		"""Return dictionary with WebDAV properties. Values shold be
		formatted according to the WebDAV specs."""
		st = os.stat(self.fsname)
		p = {}
		p['creationdate'] = unixdate2iso8601(st.st_ctime)
		p['getlastmodified'] = unixdate2httpdate(st.st_mtime)
		p['displayname'] = self.name
		p['getetag'] = md5.new(self.fsname).hexdigest()
		#p['resourcetype'] = None
		if self.type == Member.M_MEMBER:
			p['getcontentlength'] = st.st_size
			p['getcontenttype'], z = mimetypes.guess_type(self.name)
			p['getcontentlanguage'] = None
		if self.name[0] == ".":
			p['ishidden'] = 1
		if not os.access(self.fsname, os.W_OK):
			p['isreadonly'] = 1
		if self.name == '/':
			p['isroot'] = 1
		return p


	def sendData(self, wfile):
		"""Send the file to the client. Literally."""
		st = os.stat(self.fsname)
		f = file(self.fsname, 'rb')
		writ = 0
		while writ < st.st_size:
			buf = f.read(65536)

			if len(buf) == 0: # eof?
				break

			writ += len(buf)
			wfile.write(buf)
		f.close()



class DirCollection(FileMember, Collection):

	COLLECTION_MIME_TYPE = 'httpd/unix-directory'

	def __init__(self, fsdir, virdir='/', parent=None):
	
		
		if not os.path.exists(fsdir):
			raise "Local directory (fsdir) not found: " + fsdir
		self.fsname = fsdir
		# what are you going to show
		self.name = virdir

		if self.fsname[-1] != os.sep:
			if self.fsname[-1] == '/': # fixup win/dos/mac separators
				self.fsname = self.fsname[:-1] + os.sep
			else:
				self.fsname += os.sep

		self.virname = virdir
		if self.virname[-1] != '/':
			self.virname += '/'

		self.parent = parent
		self.type = Member.M_COLLECTION
	
	def getProperties(self):
		p = FileMember.getProperties(self) # inherit file properties
		p['iscollection'] = 1
		p['getcontenttype'] = DirCollection.COLLECTION_MIME_TYPE
		return p


	def getMembers(self):
		"""Get immediate members of this collection."""
		l = dircache.listdir(self.fsname)[:] # obtain a copy of dirlist
		dircache.annotate(self.fsname, l)
		r = []
		for f in l:
			if f[-1] != '/':
				m = FileMember(f, self) # Member is a file
			else:
				m = DirCollection(self.fsname + f, self.virname + f, self) # Member is a collection
			r.append(m)
		return r


	def findMember(self, name):
		"""Search for a particular member."""
		l = dircache.listdir(self.fsname)[:] # obtain a copy of dirlist
		dircache.annotate(self.fsname, l)
		print "%s - %s, find %s" % (self.fsname, repr(l), name)

		if name in l:
			if name[-1] != '/':
				return FileMember(name, self)
			else:
				return DirCollection(self.fsname + name, self.virname + name, self)
		elif name[-1] != '/':
			name += '/'
			if name in l:
				return DirCollection(self.fsname + name, self.virname + name, self)


	def sendData(self, wfile):
		"""Send "file" to the client. Since this is a directory, build some arbitrary HTML."""
		memb = self.getMembers()
		data = '<html><head><title>%s</title></head><body>' % self.virname
		data += '<table><tr><th>Name</th><th>Size</th><th>Timestamp</th></tr>'
		for m in memb:
			p = m.getProperties()
			if 'getcontentlength' in p:
				p['size'] = int(p['getcontentlength'])
				p['timestamp'] = p['getlastmodified']
			else:
				p['size'] = 0
				p['timestamp'] = '-DIR-'
			data += '<tr><td>%s</td><td>%d</td><td>%s</td></tr>' % (p['displayname'], p['size'], p['timestamp'])
		data += '</table></body></html>'
		wfile.write(data)


	# def recvMember(self, rfile, name, size, req):
		# """Receive (save) a member file"""
		# fname = os.path.join(self.fsname, name)
		# f = file(fname, 'wb')
		# writ = 0
		# bs = 65536
		# while True:
			# if size != -1 and (bs > size-writ):
				# bs = size-writ
			# buf = rfile.read(bs)
			# if len(buf) == 0:
				# break
			# f.write(buf)
			# writ += len(buf)
			# if size != -1 and writ >= size:
				# break
		# f.close()

	