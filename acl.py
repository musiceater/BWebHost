import sys
import os

def doDelACL(indexs,path):
	# delete
	for item in reversed(indexs):
		#print 'cmd=','chmod A%s- %s'%(item,path)
		#cmd='cmd=','chmod A%s- %s'%(item,path)
		#os.system("echo ""cmd %s"" >> /var/log/acl_log"%cmd)
		status=os.system('/usr/bin/chmod A%s- %s'%(item,path))
		if status !=0:
			print '1'
			os.system("rm -f .acl")
			sys.exit()
			
def deleteACL(username, type,startFolder,recur):
	if username == '#':
		if recur == '1':
			os.system('/usr/bin/ls -vR %s | egrep "%s|user:[0-9]|\+" > .acl'%(startFolder,startFolder))
			os.system('echo '':'' >> .acl')
		else:
			os.system('echo '':'' > .acl')
		
		os.system('/usr/bin/ls -dv %s | egrep "%s:[0-9]|\+" >> .acl'%(type,startFolder))
	else:
		if username=='owner@' or username=='group@' or username=='everyone@':
			if recur == '1':
				os.system('/usr/bin/ls -vR %s | egrep "%s|%s:|\+" > .acl'%(startFolder,startFolder,username))
				os.system('echo '':'' >> .acl')
			else:
				os.system('echo '':'' > .acl')
			
			os.system('/usr/bin/ls -dv %s | egrep "%s:|\+" >> .acl'%(startFolder,username))
		else:
			if recur == '1':
				os.system('/usr/bin/ls -vR %s | egrep "%s|%s:%s:|\+" > .acl'%(startFolder,startFolder,type,username))
				os.system('echo '':'' >> .acl')
			else:
				os.system('echo '':'' > .acl')
			os.system('/usr/bin/ls -dv %s | egrep "%s:%s:|\+" >> .acl'%(startFolder,type,username))
	
	f = file(".acl", 'r')
	args=0
	prefix=''
	dir=''
	index=''
	path=''
	indexs=[]
	while 1:
		line = f.readline().strip()
		if not line:	
			if len(indexs) !=0:
				doDelACL(indexs,path)
				pass
			break
		else:	
			
			if line.endswith(":"):
				prefix=line[:-1]
				if args==2:
					doDelACL(indexs,path)
					indexs=[]			
			elif line.startswith("d"):
				if args==2:
					doDelACL(indexs,path)
					indexs=[]			
				dir=line.split()[-1]
				args=2
				#print 'prefix:',prefix	
				#print 'dir:',dir
				if len(prefix) != 0:	path = prefix+'/'+dir
				else:	path = prefix+dir	
				#print 'path:',path
					
			elif line.startswith("-"):
				if len(indexs) !=0:
					doDelACL(indexs,path)
				args=1	
				indexs=[]
			elif args == 2:
				index=line.split(':')[0]
				indexs.append(index)
				
	f.close()	

def doAddACL(path,entry1,entry2):
	
	
	#print 'cmd=','chmod A+%s %s'%(entry1,path)
	#print 'cmd=','chmod A+%s %s'%(entry2,path)
	#cmd1='cmd=','chmod A+%s %s'%(entry1,path)
	#cmd2='cmd=','chmod A+%s %s'%(entry2,path)
	
	#os.system("echo ""cmd1 %s"" >> /var/log/acl_log"%cmd1)
	#os.system("echo ""cmd2 %s"" >> /var/log/acl_log"%cmd2)
	
	status=os.system('/usr/bin/chmod A+%s %s'%(entry1,path))
	if status !=0:	
		print '1'
		os.system("rm -f .acl")
		sys.exit()
	status=os.system('/usr/bin/chmod A+%s %s'%(entry2,path))
	if status !=0:	
		print '1'
		os.system("rm -f .acl")
		sys.exit()
	
def addACL(username, type, folder, entry1,entry2,recur):


	if recur == '1':
		os.system('/usr/bin/ls -R %s | egrep "%s" > .acl'%(folder,folder))
	else:	
		os.system('echo ''%s:'' > .acl'%(folder))

	f = file(".acl", 'r')
	path=''
	
	while 1:
		line = f.readline().strip()
		if not line:	
			break
		else:	
			path=line[:-1]
			entry=''
			if username=='owner@' or username=='group@' or username=='everyone@':
				e1='%s:%s'%(username,entry1)
				e2='%s:%s'%(username,entry2)
			else:
				e1='%s:%s:%s'%(type,username,entry1)
				e2='%s:%s:%s'%(type,username,entry2)		
			#print 'e1',e1
			#print 'e2',e2
			doAddACL(path,e1,e2)
	f.close()

	
args=sys.argv
passin=args[1:]
#print passin, len(passin)

"""
	This command is used for recursive changing mod
	acl delete(R) # $type[ignore] $startFolder // delete user whose username start with numbers
	acl delete(R) $username $type[group|user] $startFolder
	acl add(R)	$username $type[group|user] $startFolder acl:allow acl:deny // support modify.
													list_directory:allow
"""
op=''
user=''
folder=''
entry1=''
entry2=''
recur=''

try:
	if len(passin) > 2 and len(passin) < 7:
		op=passin[0]
		user=passin[1]
		if op == 'add' or op=='addr':
			type=passin[2]
			folder=passin[3]
			entry1=passin[4]
			entry2=passin[5]
			if op=='addr':
				recur='1'
		elif op == 'delete' or op=='deleter':
			type=passin[2]
			folder=passin[3]
			if op=='deleter':
				recur='1'
	else:
		print '-1'
		sys.exit()
except:
	print '-1'
	sys.exit()
	
	
os.system("echo ""op %s"" >> /var/log/acl_log"%op)
os.system("echo ""user %s"" >> /var/log/acl_log"%user)
os.system("echo ""folder %s"" >> /var/log/acl_log"%folder)
os.system("echo ""entry1 %s"" >> /var/log/acl_log"%entry1)
os.system("echo ""entry2 %s"" >> /var/log/acl_log"%entry2)
os.system("echo ""recur %s"" >> /var/log/acl_log"%recur)

if op == 'delete' or op == 'deleter':
	deleteACL(user,type,folder,recur)
elif op == 'add' or op == 'addr':
	deleteACL(user,type,folder,recur)
	addACL(user,type, folder, entry1,entry2,recur)
else:
	print '1'
	os.system("rm -f .acl")
	sys.exit()


print "0"
os.system("rm -f .acl")
