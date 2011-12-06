# -*- coding: utf-8 -*-
import commands
import grp
import pwd
import sys

"""
	return '' if can't find any group for user
"""

def getUserGroup(username):
	groups=[]
	ugid=-1
	try:
		# local users and NIS users, they only have single group		
		ugid = pwd.getpwnam(username)[3]
		#print ugid 
		gname = grp.getgrgid(ugid)[0]		
		#print gname
		groups.append(gname)
	except:		
		try:
			lines=commands.getoutput('/usr/bin/ldaplist -l cn=users %s 2>/dev/null| egrep \'memberOf:|primaryGroupID:\''%username)
			#print lines
			for line in lines.split('\n'):
				if line.strip().startswith('memberOf:'):
					groups.append(((line.split('memberOf:',1))[1].split(',CN')[0]).split('=',1)[1])
				elif line.strip().startswith('primaryGroupID:'):
					ugid=line.split(':',1)[1]
			
			if ugid!=-1:					
				#lines=commands.getoutput('/usr/bin/getent group'%ugid)
				lines=commands.getoutput('/usr/bin/getent group| egrep %s'%ugid)
				for line in lines.split('\n'):
					groups.append(line.split(':')[0])
		except:
			pass
	return groups	
	

if __name__ == '__main__':
	passin=sys.argv[1:]
	if len(passin)==0: 
		print -3
		
	getUserGroup(passin[0])	
	sys.exit()