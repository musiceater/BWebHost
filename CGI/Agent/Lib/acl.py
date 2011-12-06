# -*- coding: utf-8 -*-

import sys
import os
import acl
import commands
import re
import string
import pyLogger
log = pyLogger.pylogger('acl','/var/log/aclpy.log')

import pwd
import grp
from stat import * 
import acl_lib

"""

"""		
def doAddACL(name, type, entries,path, acltable):
	#print 'nddame:',name
	log.error("doAddACL in:%s"%name)
	addEntry=[]
	ret=0
	for item in entries:
		if name=='owner@' or name=='group@' or name=='everyone@':
			e='%s:%s'%(name,item)
		else:
			e='%s:%s:%s'%(type,name,item)
		addEntry.append(e)	
	#print 'addEntry:',addEntry
	
	delEntry=[]
	
	for entry in acltable:		
		if entry[2] == name:
			#index, path
			deltmp=[]
			deltmp.append(entry[1])
			deltmp.append(entry[0])
			delEntry.append(deltmp)
	
	""" 
		if entry == allow, add last
		else if entry == deny, add first
	"""

	firstIdx=len(acltable)	
	## when it's something left
	if len(delEntry)!=0:
		num=len(delEntry)
		#print 'del entry %s'%delEntry
		
		firstIdx=string.atoi(delEntry[0][0])+1
		
		for i in range(num-1, 0, -1):
			#print '%s %s'%(i,delEntry[i][0])
			log.error('/usr/bin/chmod A%s- \"%s\"'%(delEntry[i][0],delEntry[i][1]))
			#print('1 /usr/bin/chmod A%s- \"%s\"'%(delEntry[i][0],delEntry[i][1]))
			os.system('/usr/bin/chmod A%s- \"%s\" 2>/dev/null'%(delEntry[i][0],delEntry[i][1]))
		


	# add to last
	for adde in addEntry:
		if adde.find('allow')!=-1:
			#print 'entry:',adde
			#print('2 /usr/bin/chmod A%s+\"%s\" %s '%(firstIdx,adde,path))
			log.error('2 /usr/bin/chmod A%s+\"%s\" \"%s\" 2>/dev/null'%(firstIdx,adde,path))
			if os.system('/usr/bin/chmod A%s+\"%s\" \"%s\" 2>/dev/null'%(firstIdx,adde,path)) !=0:
				log.error('/usr/bin/chmod A%s+\"%s\" \"%s\" 2>/dev/null Fail'%(firstIdx,adde,path))
				return (1,path)

	
	#remove the last one		
	if len(delEntry)!=0:
		#print('22 /usr/bin/chmod A%s- \"%s\"'%(delEntry[0][0],delEntry[0][1]))
		log.error('/usr/bin/chmod A%s- %s2>/dev/null'%(delEntry[0][0],delEntry[0][1]))
		os.system('/usr/bin/chmod A%s- \"%s\" 2>/dev/null'%(delEntry[0][0],delEntry[0][1]))
	
	# add to the front, this should be 'deny'
	for adde in addEntry:
		if adde.find('deny')!=-1:
			#print 'entry:',adde
			#print('2 /usr/bin/chmod A+\"%s\" %s '%(adde,path))
			log.error('2 /usr/bin/chmod A+\"%s\" \"%s\" 2>/dev/null'%(adde,path))
			if os.system('/usr/bin/chmod A+\"%s\" \"%s\" 2>/dev/null'%(adde,path)) !=0:
				log.error('/usr/bin/chmod A+\"%s\" \"%s\" 2>/dev/null Fail'%(adde,path))
				return (1,path)
		
	return (0,path)
	
	
# return 0 for success
def doDelACL(name,acltable):
	#print 'name:',name
	##print 'acltable:',acltable

	for entry in reversed(acltable):
		
		##print 'entry[2]:',entry[2]
		if entry[2] == name:
			path=entry[0]
			index=entry[1]
			##print('cmd=chmod A%s- %s'%(index,path))
			status=os.system('/usr/bin/chmod A%s- \"%s\" 2>/dev/null'%(index,path))
			if status !=0:
				log.error('cmd=chmod A%s- \"%s\" Fail'%(index,path))
				return (1,path)
	return (0,path)

	
# type should == user or group
def modifyACL(username, type, startFolder,entries, recur, delacl):
	##print('precessing %s %s'%(startFolder, recur))
	#egreapFolder=replaceForEgrep(startFolder)
	#startFolder=startFolder.decode('string_escape')
	log.error('precessing %s %s'%(startFolder, recur))
	
	folders = commands.getoutput('/usr/bin/find \"%s\"'%startFolder).split('\n')
	lengthOfEntry=len(entries)
	ret=0
	for folder in folders:
		acltable=[]
		##print folder
		acls=commands.getoutput('/usr/bin/ls -dv \"%s\" | egrep \"owner@|group@|everyone@|:user:|group:\" '%folder.strip())
		lines=acls.split('\n')
		length=len(lines)
		
		#make sure the ACL is available
		# reserve 4
		if length+lengthOfEntry > 1020:
			if type=='other':
				acls_tmp=commands.getoutput('/usr/bin/ls -dv \"%s\" | egrep \"%s\" '%(folder.strip(),username))
				log.error('acls_tmp:%s'%acls_tmp)
			else:
				acls_tmp=commands.getoutput('/usr/bin/ls -dv \"%s\" | egrep \"%s:%s\" '%(folder.strip(),type,username))
				log.error('acls_tmp:%s'%acls_tmp)
			lines_tmp=acls_tmp.split('\n')
			length_tmp=len(lines_tmp)
			log.error('length_tmp:%d'%length_tmp)
			if length-length_tmp+lengthOfEntry> 1020:
				log.error('fail %s'%folder)
				return (1,folder)
		
		log.error('length:%d'%length)
		for line in lines:
			if not line:	
				break
			else:					
				if line.strip().endswith(":"):
					pass
				elif line.strip().startswith("d"):
					pass
				else:
					aclentry=[]		
					spit=line.strip().split(':')
				
					index=spit[0] 
					user=spit[1] 
					if user!='owner@' and user!='group@' and user!='everyone@':
						user=spit[2]

					aclentry.append(folder)
					aclentry.append(index)
					aclentry.append(user)
					#print 'aclentry:',aclentry
					
					acltable.append(aclentry)

	
		#print 'acltable:',acltable
		
		if delacl==0:
			ret,retf = doAddACL(username, type, entries,folder.strip(), acltable)
			if ret==1:
				return (1,retf)
		else:	
			ret,retf =  doDelACL(username,acltable)
			if ret==1:
				return (1,retf)
		if recur!='1':
			break

	
	return (0,startFolder)

#support everyone only
# type == user or group
# type = other indicate all invalid group
def deleteInvalidACL(startFolder, recur):
	deleteAllACL(startFolder, 1, recur)
	

"""
	Delete all ACL except owner@, group@ and everyone@
	if invalidonly ==1, delete those only starts with digits.
"""
def deleteAllACL(startFolder, invalidonly, recur):
	#egreapFolder=replaceForEgrep(startFolder)
	#startFolder=startFolder.decode('string_escape')
	
	folders = commands.getoutput('/usr/bin/find \"%s\"'%startFolder).split('\n')
	
	acltable=[]
	
	for folder in folders:
		#print folder
		if invalidonly==1:
			#os.system('/usr/bin/ls -dv \"%s\" | egrep "%s|:user:[0-9]|:group:[0-9]|^d" >> .acl'%(startFolder,egreapFolder))
			acls=commands.getoutput('/usr/bin/ls -dv \"%s\" | egrep \":user:[0-9]|group:[0-9]\" '%folder.strip())
		else:
			#os.system('/usr/bin/ls -dv \"%s\" | egrep "%s|:user:|:group:|^d" >> .acl'%(startFolder,egreapFolder))		
			#print 
			acls=commands.getoutput('/usr/bin/ls -dv \"%s\" | egrep \":user:|group:\" '%folder.strip())
		#print acls
		
		lines=acls.split('\n')
	
		for line in lines:
			if not line:	
				break
			else:					
				if line.strip().endswith(":"):
					pass
				elif line.strip().startswith("d"):
					pass
				else:
					aclentry=[]		
					spit=line.strip().split(':')
				
					index=spit[0] 
					user=spit[1] 
					if user!='owner@' and user!='group@' and user!='everyone@':
						user=spit[2]
						typetmp=spit[1]
					else:
						typetmp='other'
					# entry = folder, index, user, type
					aclentry.append(folder)
					aclentry.append(index)
					aclentry.append(user)
					aclentry.append(typetmp)
					##print 'aclentry:',aclentry
					#os.system('echo %s >> /tmp/.acl'%(aclentry))
					acltable.append(aclentry)
		if recur!='1':
			break
	
	ret=0
	for entry in reversed(acltable):
		#print('cmd=chmod A%s- %s'%(entry[1],entry[0]))
		status=os.system('/usr/bin/chmod A%s- \"%s\" 2>/dev/null'%(entry[1],entry[0]))
		if status !=0:
			log.error('cmd=chmod A%s- \"%s\" Fail'%(entry[1],entry[0]))
			ret=1 # we will proceed even if there is any error
	
	return ret	

def inheritParentACL(startFolder):
	#egreapFolder=replaceForEgrep(startFolder)
	#startFolder=startFolder.decode('string_escape')
	
	# delete others
	os.system('/usr/bin/chmod A- \"%s\" 2>/dev/null'%(startFolder))
	
	# get parent ACL
	parentPath='/'.join(startFolder.split('/')[:-1])
	#print 'parent path:',parentPath

	lines=commands.getoutput('/usr/bin/ls -dv \"%s\" | egrep -v -e "^d" '%(parentPath))		

	acltable=[]
	entry=''
	
	tmpline=''
	
	for line in lines.split('\n'):
		if line.find('owner@')!=-1 or line.find('group@')!=-1 or line.find('everyone@')!=-1\
		 or line.find(':user:')!=-1  or line.find(':group:')!=-1:
			if tmpline!='':
				entry=':'.join(tmpline.split(':')[1:])
				acltable.append(entry)
			
			tmpline=line.strip()
		else:
			tmpline=tmpline+line.strip()
			
	
	if tmpline!='':
		entry=':'.join(tmpline.split(':')[1:])
		acltable.append(entry)
	
	#print 'acltable',acltable
	
	lines=commands.getoutput('/usr/bin/ls -dv \"%s\" | egrep ":user:|:group:|:owner@:|:group@:|:everyone@:" '%(startFolder))		
	num=len(lines.split('\n'))
	
	
	
	#print('num %d'%(num))
	for idx in range(1,num):
		log.error('cmd=chmod A0- %s'%(startFolder))
		#print('cmd=chmod A0- %s'%(startFolder))
		os.system('/usr/bin/chmod A0- \"%s\"'%(startFolder))
		
	ret=0
	for entry in reversed(acltable):
		# we don't inherit users
		#if entry.find('group:')==-1 and entry.find('user:')==-1:
		log.error('cmd=chmod A1+\"%s\" %s'%(entry,startFolder))
		#print('cmd=chmod A1+\"%s\" %s'%(entry,startFolder))
		os.system('/usr/bin/chmod A1+\"%s\" \"%s\" 2>/dev/null'%(entry,startFolder))
	log.error('cmd=chmod A0- %s'%(startFolder))
	os.system('/usr/bin/chmod A0- \"%s\" 2>/dev/null'%(startFolder))
	return ret	
	
import getACLStr
def createDefaultACL(startFolder,defaultUser):
	#startFolder=startFolder.decode('string_escape')
	
	os.system('/usr/bin/ls -dv \"%s\" | egrep ":user:|:group:|:owner@:|:group@:|:everyone@:" > .acl'%(startFolder))

	f = file(".acl", 'r')
	num=0
	while 1:
		line = f.readline().strip()		
		if not line:	
			break
		else:	
			num=num+1

	for idx in range(1,num):
		##print('cmd=bbchmod A0- %s'%(startFolder))
		os.system('/usr/bin/chmod A0- \"%s\" 2>/dev/null'%(startFolder))
	
	ret=0
	#add default control
	
	acl_read=getACLStr.getACLList('allow',['rnr'])[0]
	acl_write=getACLStr.getACLList('deny',['write'])[0]
	acl_full=getACLStr.getACLList('allow',['full'])[0]
	acl_=getACLStr.getACLList('deny',[''])[0]
	
	### always deny first
	
	if defaultUser!='':
		os.system('/usr/bin/chmod A1+\"user:%s:%s\" \"%s\" 2>/dev/null'%(defaultUser,acl_full,startFolder))
	
	#print('/usr/bin/chmod A1+everyone@:%s %s '%(acl_read,startFolder))
	os.system('/usr/bin/chmod A1+\"everyone@:%s\" \"%s\" 2>/dev/null'%(acl_read,startFolder))
	
	#print('/usr/bin/chmod A1+everyone@:%s %s '%(acl_write,startFolder))
	os.system('/usr/bin/chmod A1+\"everyone@:%s\" \"%s\" 2>/dev/null'%(acl_,startFolder))
	
	if defaultUser!='':
		os.system('/usr/bin/chmod A1+\"user:%s:%s\" \"%s\" 2>/dev/null'%(defaultUser,acl_,startFolder))

	#print('cmd=chmod A0- %s'%(startFolder))
	os.system('/usr/bin/chmod A0- \"%s\" 2>/dev/null'%(startFolder))
	
	f.close()	
	os.system('rm -rf .acl 2>/dev/null')
	return ret
	
ALLOW = 1
DENY = 2
USER_TYPE_OWNER = 0
USER_TYPE_SPECIAL_GROUP = 1
USER_TYPE_EVERYONE = 2
USER_TYPE_USER = 3
USER_TYPE_GROUP = 4
USER_TYPE_LDAP_USER = 5
USER_TYPE_LDAP_GROUP = 6

def parseSimpleAcl(aclData):
	full_control ='0' 
	modify ='0' 
	read_and_run ='0' 
	isList ='0' 
	read ='0' 
	write ='0'
	if len(aclData)==0:
		return full_control + modify + read_and_run + isList + read + write
		
	sections=aclData.split(':')
	#name='everyone@'
	ACL=''
	ACL_extend=''
	if len(sections)==5:
		#name = sections[1]
		ACL	= sections[2]
		ACL_extend	= sections[3]
	else:
		#name = sections[0]
		ACL	= sections[1]
		ACL_extend	= sections[2]
	
	#print 'aclData',aclData
	#print 'name',name
	#print 'ACL',ACL
	#print 'ACL_extend',ACL_extend
	
	if ACL.find("C")!=-1 and ACL.find("D")!=-1:
		full_control='1'
	
	if ACL.find("d")!=-1:
		modify='1'
	
	if ACL.find('r')!=-1 and \
		ACL.find('x') == -1 and\
		ACL_extend.find('f')!=-1 and \
		ACL_extend.find('d')!=-1:		
		read='1'	
	
	if ACL.find('r')!=-1 and \
		ACL.find('x')!=-1 and \
		ACL_extend.find('d')!=-1 and \
		ACL_extend.find('f')==-1:
		isList='1'	
	
	if ACL.find('r')!=-1 and \
		ACL.find('x')!=-1 and \
		ACL_extend.find('f')!=-1 and \
		ACL_extend.find('d')!=-1:
 		read_and_run = '1'
		read='1'		
		isList='1'				
	
	if ACL.find('w')!=-1:
		write='1'
		
	retStr = full_control + modify + read_and_run + isList + read + write
	return retStr
	

def parseAcl(aclData):
	full_control ='0' 
	modify ='0' 
	read_and_run ='0' 
	isList ='0' 
	read ='0' 
	write ='0'
	# #print 'aclData',aclData
	if len(aclData)==0:
		return full_control + modify + read_and_run + isList + read + write
	
	if aclData.find("write_acl")!=-1 and aclData.find("delete_child")!=-1:
		full_control='1'
		# #print 'ful'
	if aclData.find("delete")!=-1:
		modify='1'
		# #print 'mod'
	if aclData.find('list_directory')!=-1 and \
		aclData.find('execute') == -1 and\
		aclData.find('file_inherit')!=-1 and \
		aclData.find('dir_inherit')!=-1:		
		read='1'	
		# #print 'read'		
	if aclData.find('list_directory')!=-1 and \
		aclData.find('execute')!=-1 and \
		aclData.find('dir_inherit')!=-1 and \
		aclData.find('file_inherit')==-1:
		isList='1'	
		# #print 'list'		
	if aclData.find('list_directory')!=-1 and \
		aclData.find('execute')!=-1 and \
		aclData.find('file_inherit')!=-1 and \
		aclData.find('dir_inherit')!=-1:
		# #print 'rnr'
 		read_and_run = '1'
		read='1'		
		isList='1'				
		
	if aclData.find('add_file')!=-1:
		write='1'
		# #print 'write'
		
	retStr = full_control + modify + read_and_run + isList + read + write
	return retStr

	
	
	
	
"""
	old return format : everyone|000000|000001|2|0
	new return format : everyone|000000|000001
"""
def getSimpleACL(path, username=''):	
	# if username=='', get all
	#print 'path',path
	lines=commands.getoutput('/usr/bin/ls -dV \"%s\"| egrep -v -e "^d" '%(path))		
		
	aclList=[]
	aclentry={}
	for line in lines.split('\n'):
		sections=line.split(':')
		name='everyone@'
		auth=''
		if len(sections)==5:
			name = sections[1].strip()
			auth=sections[4].strip()
		else:
			name = sections[0].strip()
			auth=sections[3].strip()
			
		if name=='owner@' or name=='group@':
			continue
		
		formatAcl=parseSimpleAcl(line)
		#print 'formatAcl',formatAcl
		#print 'auth',auth
		
		if username==name or username=='':
			if not name in aclentry:
				##upper=allow,lower=deny
				aclentry[name]='000000000000'
			if auth=='allow':
				aclentry[name]=acl_lib.doOR(formatAcl+'000000',aclentry[name])
			else:
				aclentry[name]=acl_lib.doOR('000000'+formatAcl,aclentry[name])					
	#test
	#print aclentry
	for name in aclentry.keys():
		value=aclentry[name]
		if name=='everyone@':	name='everyone'
		str=name+'|'+value[:6]+'|'+value[6:]
		print str	
	#end of test
	
	return aclentry

# """
	# format : dic['username']={'000000000001'}
# """	
# def setSimpleACL(aclhash):	
	# for name in aclhash.keys():
		# value=aclhash[name]
		# if name=='everyone':
			# name='everyone@'
		# print str	
	
def isReadable(simpleacl):	
def isWritable(simpleacl):	
def isReadable(simpleacl):	
def isReadable(simpleacl):	
def isReadable(simpleacl):	
	
"""
	return format : everyone|000000|000001|2|0
"""
def getAcl(path):	
	escapePath=path.decode('string_escape')
	path="\""+path+"\""
	userArray = []
	userDic = {}	
	cmd = "/bin/ls -dv " + path
	output = commands.getoutput(cmd)
	lines = output.splitlines()
	matchPattern = re.compile('\d+:')
	aclBuf = ""
	name = ""
	userType = 0
	aclType = 0
	userId = "0"
	isFirstLine = 1
	fileUserName = ""
	fileGroupName = ""
	key = ""
	for line in lines:
		done = 0
		if isFirstLine == 1:
			#element = line.split()
			#fileUserName = element[2]
			#fileGroupName = element[3]
			st = os.stat(escapePath)
			fileUserName = '0'
			fileGroupName = '0'
			try:
				fileUserName = pwd.getpwuid(st[ST_UID])[0]
				fileGroupName = grp.getgrgid(st[ST_GID])[0]
			except:
				pass

			isFirstLine = 0
		if matchPattern.search(line):
			aclBuf = ""
			element = line.split(":")
		
			if element[1].find("everyone@") != -1 or element[1].find("group@") != -1 or element[1].find("owner@") != -1:
				name =  element[1]					
				if element[1].find("everyone@") != -1:
					name = "everyone"
					userType = USER_TYPE_EVERYONE
				elif element[1].find("group@") != -1:
					userType = USER_TYPE_SPECIAL_GROUP
					name = fileGroupName
					#name = "group"
				else:
					userType = USER_TYPE_OWNER
					name = fileUserName
					#name = "owner"
				lastIndex = len(element)-1
				if element[len(element)-1].find("allow") != -1:
					aclType = ALLOW
					lastIndex = lastIndex - 1
					done = 1
				elif element[len(element)-1].find("deny") != -1:
					aclType = DENY
					lastIndex = lastIndex - 1
					done = 1
				i = 2
				while i <= lastIndex:
					aclBuf = aclBuf + element[i]
					i = i + 1
			#elif element[1].find("user") != -1 or element[1].find("group") != -1 :
			elif element[1] == "user" or element[1] == "group":
				name = element[2]
				if element[1].find("user") != -1:
					cmd = "cat /etc/ldap_user | cut -d ':' -f 2 | grep -w " + name
					output = commands.getoutput(cmd)
					if output != name:
						userType = USER_TYPE_USER
					else:
						userType = USER_TYPE_LDAP_USER
				else:
					cmd = "cat /etc/ldap_group | cut -d ':' -f 1 | grep -w " + name
					output = commands.getoutput(cmd)
					if output != name:
						userType = USER_TYPE_GROUP
					else:
						userType = USER_TYPE_LDAP_GROUP
				lastIndex = len(element)-1
				if element[len(element)-1].find("allow") != -1:
					aclType = ALLOW
					lastIndex = lastIndex - 1
					done = 1
				elif element[len(element)-1].find("deny") != -1:
					aclType = DENY
					lastIndex = lastIndex - 1
					done = 1
				i = 3
				while i <= lastIndex:
					aclBuf = aclBuf + element[i]
					i = i + 1
		
		else:
			element = line.split(":")
			lastIndex = len(element)-1
			if element[len(element)-1].find("allow") != -1:
				aclType = ALLOW
				lastIndex = lastIndex - 1
				done = 1
			elif element[len(element)-1].find("deny") != -1:
				aclType = DENY
				lastIndex = lastIndex - 1
				done = 1

			i = 0
			while i <= lastIndex:
				aclBuf = aclBuf + element[i]
				i = i + 1
	
		if done == 1:
			if userType == USER_TYPE_USER or userType == USER_TYPE_OWNER or userType == USER_TYPE_LDAP_USER:
				output = commands.getoutput("/bin/id \""+ name+"\"")
				
				idMatchPattern = re.compile('uid=(\d+)')
				match = idMatchPattern.search(output)
				if match:
					userId = match.group(1)		
				key = name + "u"
			elif userType == USER_TYPE_GROUP or  USER_TYPE_LDAP_GROUP == userType or userType == USER_TYPE_SPECIAL_GROUP:
				output = commands.getoutput("/bin/getent group \""+ name+"\"")

				try:
					userId =  output.split(":")[2]
				except:
					userId = "65534"
				key = name + "g"	
			else:
				userId = "0"
				key = name + "g"
					
			if key in userDic:
				if name != "root":	
					user = userDic[key]
					tmp=parseAcl(aclBuf)
					#print '1:',tmp
					tmpstr=''

					if aclType == ALLOW:
						for i in range(0,len(tmp)):
							if tmp[i]=='1':
								tmpstr=tmpstr+'1'
							else:
								tmpstr=tmpstr+user["aclAllow"][i]
						user["aclAllow"]=tmpstr			
					#if aclType == DENY:
					else:
						for i in range(0,len(tmp)):
							if tmp[i]=='1':
								tmpstr=tmpstr+'1'
							else:
								tmpstr=tmpstr+user["aclDeny"][i]
						user["aclDeny"]=tmpstr	
					

			else:
				if name != "root":
					if name[0] >= "0" and name[0] <= "9":
						pass
					#  prevent nfs nobody show
					elif userId == "60001" or userId == "65534":
						pass
					#elif userType == USER_TYPE_OWNER:
					#	pass
					#elif userType == USER_TYPE_SPECIAL_GROUP:
					#	pass
					else:
						newUser = {}
						newUser["aclAllow"] = "000000"
						newUser["aclDeny"] = "000000"
						tmp=parseAcl(aclBuf)
						tmpstr=''
						
						
						if aclType == ALLOW:
							for i in range(0,len(tmp)):
								if tmp[i]=='1':
									tmpstr=tmpstr+'1'
								else:
									tmpstr=tmpstr+newUser["aclAllow"][i]
							newUser["aclAllow"]=tmpstr																
						#if aclType == DENY:
						else:
							for i in range(0,len(tmp)):
								if tmp[i]=='1':
									tmpstr=tmpstr+'1'
								else:
									tmpstr=tmpstr+newUser["aclDeny"][i]
							newUser["aclDeny"]=tmpstr																
							

						newUser["name"] = name
						newUser["userType"] = userType
						newUser["userId"] = userId
						userDic[key] = newUser
						
						userArray.append(userDic[key])
	
	useracls=[]
	for user in userArray:
		useracls.append(user["name"] + "|" + user["aclAllow"] + "|" + user["aclDeny"] + \
			"|" +  str(user["userType"]) +  "|" + user["userId"])
	return useracls
			




if __name__ == '__main__':
	passin=sys.argv[1:]
	
	#print passin, len(passin)
	log.error("in:%s"%passin)
	"""
		This command is used for recursive changing mod
		acl delete(R) @invalid $type[ignore] $startFolder // delete user whose username start with numbers
		acl delete(R) @all $type[ignore] $startFolder // delete all except owner@, group@ and everyone@
		acl delete(R) $username $type[group|user] $startFolder
		acl add(R)	$username $type[group|user] $startFolder acl:allow acl:deny // support modify.
														list_directory:allow	
		acl copyparentacl $startFolder												
		acl defaultacl $startFolder [$user]		// set default acl to the spicific folder									
												// if user is specified, add the access right to the user
	"""
	op=''
	user=''
	folder=''
	entry1=''
	entry2=''
	recur=''
	delacl=0
	
	entries=[]
	defaultUser=''
	try:
		if len(passin) >= 2:
			op=passin[0]
			user=passin[1]
			if op == 'add' or op=='addr':
				type=passin[2]
				folder=passin[3]
				for item in passin[4:]:
					entries.append(item)
				if op=='addr':
					recur='1'
				delacl=0	
			elif op == 'delete' or op=='deleter':
				type=passin[2]
				folder=passin[3]
				if op=='deleter':
					recur='1'
				delacl=1
			elif op == 'copyparentacl' or op=='get':
				folder=passin[1]
				if len(passin)==3:
					user=passin[2]
			elif op=='defaultacl':
				folder=passin[1]
				if len(passin)==3:
					defaultUser=passin[2]		
		else:
			print '-1'
			sys.exit()
	except:
		print '-1'
		#raise
		sys.exit()
	
	ret=0
	
	if op == 'get':
		#log.error("do get")
		
		#acls=getAcl(folder)
		#if len(acls)!=0:
			#for item in acls:
				#print item
		#print 'spli'			
		acls=getSimpleACL(folder, 'everyone@')
		
	elif op=='copyparentacl':
		log.error("do copyparentacl")
		ret=inheritParentACL(folder)
		print ret
	elif op=='defaultacl':	
		log.error("do defaultacl")
		ret=createDefaultACL(folder, defaultUser)
		print ret
	else:	
		if user == '@invalid':
			log.error("do @invalid")
			ret=deleteAllACL(folder,1,recur)
			print ret
		elif user == '@all':
			log.error("do @all")
			ret=deleteAllACL(folder,0,recur)
			print ret
		else:
			log.error("do modifyACL")
			ret,retf=modifyACL(user, type, folder, entries, recur, delacl)
			print "%d:%s"%(ret,retf)
		
	
	
	#os.system("rm -f .acl 2>/dev/null")
