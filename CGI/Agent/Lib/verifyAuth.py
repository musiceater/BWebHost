import crypt, getpass, pwd, spwd 

import os
import commands

# return: 0 - sucess
#		  1 - user not exist
#		  2 - wrong password		
def checkPasswd(username, passwd):
	try:
		cryptpasswd = pwd.getpwnam(username)[1]
		print cryptpasswd
	except:
		return 1
	if cryptpasswd:
		if cryptpasswd == 'x' or cryptpasswd == '*': 
			cryptpasswd = spwd.getspnam(username)[1]
		if crypt.crypt(passwd, cryptpasswd) == cryptpasswd:
			return 0
		return 2
	else:
		return 1

		
	# return : 0 - success	
	#		   1 - user not exist
	#		   2 - wrong password
	#		   3 - LDAP Server Not found
def checkPasswd_LDAP(username, passwd):
	host=commands.getoutput('/usr/sbin/ldapclient list  2>/dev/null| grep LDAP_SERVERS=| cut -d \' \' -f2')
	print 'host',host
	if len(host)==0:
		return 3
	print 'username=',username,'password',passwd,'host',host
	
	if os.system('/usr/sbin/ldaplist cn=users \'%s\' 2>/dev/null'%username)!=0:
		return 1
	
	ret = os.system('./verifyAuth_LDAP_exe %s %s %s > /dev/null'%(host,username,passwd))
	if ret != 0:
		return 2;
	return 0

	# return : 0 - success
	#		   1 - user not exist
	#		   2 - wrong password
def checkPasswd_NIS(username, passwd):
	lines=commands.getoutput('/usr/bin/ypcat passwd | grep \'%s\''%username)
	# print 'host',host
	if len(lines)==0:
		return 1
	un=''
	pwd=''	
	try:
		for line in lines.split('\n'):
			tmp=line.split(':')
			un=tmp[0]
			if un==username:
				cryptpasswd=tmp[1]
				if crypt.crypt(passwd, cryptpasswd) == cryptpasswd:
					return 0
				else:
					return 2
				break;
		return 1		
	except:
		return 1
	#print 'username=',username,un,'password',passwd,pwd
	

def test(username, passwd):
	ret=1
	try:
		# check local user
		ret = checkPasswd(username, passwd)
		if ret==1:
			# check LDAP user
			ret=checkPasswd_LDAP(username, passwd)
		if ret==1:
			# check NIS user
			ret=checkPasswd_NIS(username, passwd)
	except:
		ret=1
	if ret==1:
		print 'can not find user'
	elif ret==2:
		print 'wrong password'
	elif ret==0:
		print 'authencation success'
	

