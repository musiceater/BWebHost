#!/usr/bin/python2.6  
# -*- coding: utf-8 -*-

import string,cgi,time

from os import curdir, sep
import os
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from SocketServer import ThreadingMixIn
import threading
import mimetypes

# Library from Bart Hsiao.
import funcLib
import message
#import basicACL
import doPropFind

curdir = "/root/pHttpServer/" # WebServer Location
webdavFolder = '/webdav/'
#webdavFolder = '/'
"""
	
"""
class NASServer(BaseHTTPRequestHandler):

	"""
		return 0: success
			   1: no Authorization
			   2: username/password wrong
	"""
	def chkAccess(self):
		try:
			uswd = self.headers['Authorization']
			print 'uswd', uswd
			print funcLib.getUsernamePassword(uswd)				
		except:
			# no Authentication is gaven
			return 1
		# password check ok
		return 0
		
	def do_GET(self):
		try:
			
			print 'GET',self.path
			
			print 'request',self.headers
			path = self.path
			auth_state = self.chkAccess()
			if auth_state!=0:
				self.send_response(401)
				self.send_header('WWW-Authenticate', 'Basic realm="Secure Area"')
				self.end_headers()
			
			filepath = funcLib.getHTMLFile(curdir, path)
			print 'filepath',filepath
			
			parms = funcLib.getParms(path)
			print 'parms',parms
						
			if len(parms) != 0:
				(result, output) = funcLib.callFunc(filepath, parms)
				print 'result',result
				print 'output',output
				if result == -1:
					send_error(404,'File Not Found: %s' % path)
				else:	
					self.wfile.write(output)
			else:
				#if there is any parmater, we will not treat it as a fetch file.
				if  filepath != '':
					f = open(filepath) 
				
					# set different header for supported file format
					# if filepath.endswith('.png'):
						# self.send_header('Content-type', 'image/png')
					# elif filepath.endswith('.jpeg'):
						# self.send_header('Content-type', 'image/jpeg')
					# elif filepath.endswith('.jpg'):
						# self.send_header('Content-type', 'image/jpg')	
					# elif filepath.endswith('.css'):
						# self.send_header('Content-type', 'text/css')
					# elif filepath.endswith('.js'):
						# self.send_header('Content-type', 'application/x-javascript')	
					# else:
						# self.send_header('Content-type', 'text/html')
					mt  = mimetypes.guess_type(path)[0]
					if not mt: 
						mt = 'text/html; charset=utf-8'				
					self.send_response(200)	
					self.send_header('Content-type', mt)	
					self.end_headers()
					self.wfile.write(f.read())
					f.close()
				else:
					self.send_error(404,'File Not Found: %s' % self.path)
		except IOError:
			self.send_error(404,'File Not Found: %s' % self.path)
		
			
			
	def do_POST(self):
		print 'POST',self
		# Only support transfer file for now
		try:
			auth_state = self.chkAccess()
			if auth_state!=0:
				self.send_response(401)
				self.send_header('WWW-Authenticate', 'Basic realm="Secure Area"')
				self.end_headers()
				
			ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
			
			if ctype == 'multipart/form-data':
				print 'start upload'
				guery=cgi.parse_multipart(self.rfile, pdict)
				
			else:
				self.send_error(404,'File Not Found: %s' % self.path)
				return
			print '1',self.send_response(301)
			print '2',self.end_headers()
			
			test = guery.get('filename')
			print 'name=',pdict[0]
			
			upfilecontent = guery.get('upfile')
			
			print 'get content'
			if upfilecontent:
				fout = file('/tmp/test.tmp', 'wb')
				fout.write (upfilecontent[0])
				fout.close()
			print "fileName"
			print '3',self.wfile.write("<HTML>POST OK.<BR><BR>")
			
		except :
			pass
			
	def do_PUT(self):
		print 'PUT',self
		print 'PUT',self.path
		try:
			auth_state = self.chkAccess()
			print 'auth_stat',auth_state
			if auth_state!=0:
				self.send_response(401)
				self.send_header('WWW-Authenticate', 'Basic realm="Secure Area"')
				self.end_headers()
		
			if 'Content-length' in self.headers:
				size = int(self.headers['Content-length'])
			else:
				size = -1
		except:
			self.send_response(400, 'Cannot parse request')
			self.end_headers()
			raise
			return

		try:
			result = funcLib.saveFile(curdir+self.path,self.rfile, size)
			print 'save file result:',result
			if result != 0: raise
		except:
			self.send_response(500, 'Cannot save file')
			self.end_headers()
			raise
			return

		self.send_response(200, 'Ok, received')
		self.end_headers()

	def do_HEAD(self):
		print 'HEAD',self
		# Only support transfer file for now
		try:
			auth_state = self.chkAccess()
			if auth_state!=0:
				self.send_response(401)
				self.send_header('WWW-Authenticate', 'Basic realm="Secure Area"')
				self.end_headers()
			pass
		except :
			pass		
			
	def do_PROPFIND(self):
		print 'PROPFIND bart1',self
		print 'PROPFIND bart2',self.path
		
		print 'headers:',
		
		try:
			auth_state = self.chkAccess()
			print 'auth_state',auth_state
			if auth_state!=0:
				self.send_response(401)
				self.send_header('WWW-Authenticate', 'Basic realm="Secure Area"')
				self.end_headers()
		
			if 'Content-length' in self.headers:
				req = self.rfile.read(int(self.headers['Content-length']))
			else:
				req = self.rfile.read()
				
			depth = 'infinity'
			
			if 'Depth' in self.headers:
				depth = self.headers['Depth'].lower()
			print 'PROPFIND 111'
			status, content = doPropFind.execute(req,depth,curdir,self.path,webdavFolder)
			
			if status==0:
				self.send_response(207, 'Multistatus')
				self.send_header('Content-Type', 'text/xml')
				self.send_header('Content-Length', str(len(content)))
				self.end_headers()
				self.wfile.write(content)
				
			print 'PROPFIND end'
		except :
			raise		
			
	def do_PROPPATCH(self):
		print 'PROPPATCH',self
		# Only support transfer file for now
		try:
			auth_state = self.chkAccess()
			if auth_state!=0:
				self.send_response(401)
				self.send_header('WWW-Authenticate', 'Basic realm="Secure Area"')
				self.end_headers()
			pass
		except :
			pass		
	
	def do_DELETE(self):
		print 'DELETE',self
		
		try:
			auth_state = self.chkAccess()
			if auth_state!=0:
				self.send_response(401)
				self.send_header('WWW-Authenticate', 'Basic realm="Secure Area"')
				self.end_headers()
				
			print curdir+self.path
			
			os.remove(curdir+self.path)			
		except :
			print 'Delete Fail'
			self.send_response(423)
			self.end_headers()
			raise
			return 			
		self.send_response(204)
		self.end_headers()
		
	def do_COPY(self):
		print 'COPY',self
		print 'COPY',self.path
		
		auth_state = self.chkAccess()
		if auth_state!=0:
			self.send_response(401)
			self.send_header('WWW-Authenticate', 'Basic realm="Secure Area"')
			self.end_headers()
		
		host = self.headers['Host']
		print 'COPY host',host
		dest_tmp = self.headers['Destination']
		idx=dest_tmp.find(host)+len(host)
		dest=dest_tmp
		if idx!=-1:
			dest=dest_tmp[idx:]
		
		print 'COPY to',str
		
		preExist=0
		if os.path.isfile(curdir+dest):
			preExist=1
		
		try:
			print curdir+dest
			print 'COPY from %s to %s'%(curdir+self.path,curdir+dest)
			
			re=os.system(" cp %s %s 2> /dev/null"%(curdir+self.path,curdir+dest))
			if re!=0:
				raise
		except:
			print 'copy file fail'
			self.send_response(403 )
			self.end_headers()
			return
		if 	preExist==0:
			self.send_response(201)
		else:
			self.send_response(204)
		self.end_headers()

		
	def do_MOVE(self):
		print 'MOVE',self
		print 'MOVE',self.path
		auth_state = self.chkAccess()
		if auth_state!=0:
			self.send_response(401)
			self.send_header('WWW-Authenticate', 'Basic realm="Secure Area"')
			self.end_headers()
		
		host = self.headers['Host']
		print 'MOVE host',host
		dest_tmp = self.headers['Destination']
		idx=dest_tmp.find(host)+len(host)
		dest=dest_tmp
		if idx!=-1:
			dest=dest_tmp[idx:]
		
		print 'MOVE to',str
		
		preExist=0
		if os.path.isfile(curdir+dest):
			preExist=1
		
		try:
			print curdir+dest
			print 'MOVE from %s to %s'%(curdir+self.path,curdir+dest)
			
			re=os.system("mv %s %s 2> /dev/null"%(curdir+self.path,curdir+dest))
			if re!=0:
				raise
		except:
			print 'Move file fail'
			self.send_response(403 )
			self.end_headers()
			return
		if 	preExist==0:
			self.send_response(201)
		else:
			self.send_response(204)
		self.end_headers()
	   
	def do_MKCOL(self):
		print 'MKCOL',self
		print 'MKCOL',self.path
		# Only support transfer file for now
		try:
			auth_state = self.chkAccess()
			if auth_state!=0:
				self.send_response(401)
				self.send_header('WWW-Authenticate', 'Basic realm="Secure Area"')
				self.end_headers()
				
			if os.path.exists(curdir+self.path):
				self.send_response(405)
				self.end_headers()
				return 
			else:	
				try:
					print curdir+self.path
					os.makedirs(curdir+self.path)
				except:
					print 'create folder fail'
					raise
		except :
			self.send_response(403)
			self.end_headers()
			raise
			return 			
		self.send_response(201)
		self.end_headers()
			
	def do_LOCK(self):
		print 'LOCK',self
		# Only support transfer file for now
		try:
			auth_state = self.chkAccess()
			if auth_state!=0:
				self.send_response(401)
				self.send_header('WWW-Authenticate', 'Basic realm="Secure Area"')
				self.end_headers()
			pass
		except :
			pass		
	def do_UNLOCK(self):
		print 'UNLOCK',self
		# Only support transfer file for now
		try:
			auth_state = self.chkAccess()
			if auth_state!=0:
				self.send_response(401)
				self.send_header('WWW-Authenticate', 'Basic realm="Secure Area"')
				self.end_headers()
			pass
		except :
			pass		
			
	def do_OPTIONS(self):
		print 'OPTIONS',self
		# Only support transfer file for now
		try:
			auth_state = self.chkAccess()
			if auth_state!=0:
				self.send_response(401)
				self.send_header('WWW-Authenticate', 'Basic realm="Secure Area"')
				self.end_headers()
			self.send_response(200)
			methods = funcLib.getSupportMethod()
			print methods
			levels = funcLib.getSupportLevel()
			print levels
			self.send_header('Allow', funcLib.supportMethod)
			self.send_header('Content-length', '0')
			self.send_header('DAV', funcLib.supportLevel)
			#self.send_header('MS-Author-Via', 'DAV')
			self.end_headers()
			
		except :
			pass		
	   
	
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
	pass
	
# def main():
	# try:
		
		##server = ThreadedHTTPServer(('', 443), NASServer)
		# server = ThreadedHTTPServer(('', 80), NASServer)
		# print 'started httpserver...'
		# server.serve_forever()
	# except KeyboardInterrupt:
		# print '*C received, shutting down server'
		# server.socket.close()
		
# if __name__ == '__main__':
	# main()
