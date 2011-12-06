# -*- coding: utf-8 -*-
import commands

webdavPath='/webdav'
"""
	link the share path to webdav
	this function only link the folder to folder under WEBDAV
	ex: ln -s /tmp/tt /webdav
"""
def addShareFolder(folderpath):
	print 'folderpath','/usr/bin/ln -s %s %s 1>/dev/null'%(folderpath, webdavPath)
	message = commands.getoutput('/usr/bin/ln -s %s %s 1>/dev/null'%(folderpath, webdavPath))
	
def delShareFolder(foldername):
	print 'foldername','/usr/bin/rm  -rf %s/%s 1>/dev/null'%(webdavPath,foldername)
	message = commands.getoutput('/usr/bin/rm  -rf %s/%s 1>/dev/null'%(webdavPath,foldername))
	
	