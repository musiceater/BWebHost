import os,sys
import subprocess

# log 
import pyLogger
import addLdapUidGid

log = pyLogger.pylogger('ldap_sync','/var/log/nas.log')	
userTbl = addLdapUidGid.userTbl
groupTbl = addLdapUidGid.groupTbl

log.debug("userTbl len=%d"%(len(userTbl)))
log.debug("groupTbl len=%d"%(len(groupTbl)))
"""
re=os.system("/usr/bin/ldaplist -l cn=users  2> /dev/null | egrep \"cn:|uSNCreated:|gidNumber|uidNumber|unixHomeDirectory|loginShell\" > .ldap_tmp")

if re!=0:
	log.error('Execute \'ldaplist -l cn=users\' Fail.')
	print "1"
	os.system("rm -f .ldap_tmp 2> /dev/null")
	sys.exit()

re=os.system("/usr/bin/ldaplist > /dev/null")
if re!=0:
	log.error('Execute \'ldaplist\' Fail.')
	print "1"
	os.system("rm -f .ldap_tmp 2> /dev/null")
	sys.exit()
	
	
f = file(".ldap_tmp", 'r')
"""
gourp_list="#generated automatically. Should not be modified manually.\n"
user_list="#generated automatically. Should not be modified manually.\n"

args=0
tested=0
for obj in userTbl:
	if len(obj.uidnumber) != 0 and len(obj.gidnumber) != 0 and len(obj.loginshell) != 0 and len(obj.homedir) != 0:
		if tested != 0:
			re=os.system("/usr/bin/getent passwd \"%s\" > /dev/null" % obj.cn_name)
			if re!=0:
				log.error('No reponse from \'getent passwd %s\''% obj.cn_name)
				print "2"
				os.system("rm -f .ldap_tmp 2> /dev/null")
				sys.exit()
			tested=1
		user_list=user_list+obj.uidnumber+":"+obj.uid+":"+obj.homedir+":"+obj.gidnumber+":"+obj.sn+"\n"

for obj in groupTbl:
	if len(obj.gidnumber) != 0:
		gourp_list = gourp_list+obj.cn_name+":"+obj.gidnumber+":"+obj.sn+"\n"
"""
while 1:
	line = f.readline().strip()
	if not line:	break
	else:	
		
		if line.startswith("cn:"):
			name=' '.join(line.split()[1:])
			args=1
		elif line.startswith("uSNCreated:"):
			sn=' '.join(line.split()[1:])
			args=args+1
		elif line.startswith("uidNumber:"):
			uid=' '.join(line.split()[1:])
			args=args+1
		elif line.startswith("gidNumber:"):
			gid=' '.join(line.split()[1:])
			if args == 2:
				gourp_list = gourp_list+name+":"+gid+":"+sn+"\n"
			args=args+1
		elif line.startswith("unixHomeDirectory:"):
			home=' '.join(line.split()[1:])
			args=args+1
		elif line.startswith("loginShell:"):
			shell=' '.join(line.split()[1:])
			args=args+1
		
		if args == 5:
			if tested==0:
				
				re=os.system("/usr/bin/getent passwd %s > /dev/null" % name)
				
				if re!=0:
					log.error('No reponse from \'getent passwd %s\''%name)
					print "2"
					os.system("rm -f .ldap_tmp 2> /dev/null")
					sys.exit()
				tested=1	
			user_list=user_list+uid+":"+name+":"+home+":"+gid+":"+sn+"\n"	
f.close()
"""

# find different 
# we only focuse on removed user
try:
	os.system("mv /etc/ldap_user /etc/ldap_user.old  2> /dev/null")
	os.system("mv /etc/ldap_group /etc/ldap_group.old  2> /dev/null")

	fg = file("/etc/ldap_group", 'w')
	fg.write(gourp_list)
	fg.close()
	fg = file("/etc/ldap_user", 'w')
	fg.write(user_list)
	fg.close()

	os.system("diff -b /etc/ldap_user /etc/ldap_user.old  2> /dev/null | grep '>'  | cut -d ':' -f2 > .ldap_diff_user")
	os.system("diff -b /etc/ldap_group /etc/ldap_group.old 2> /dev/null | grep '>'  | cut -d ':' -f2 > .ldap_diff_group")
except:
	log.error('Updating /etc/ldap_user & ldap_diff_group')
	print "1"
	sys.exit()

# handle ACL for removed user. 

# clear removed user & group
try:
	import clearUser
	fuser = file(".ldap_diff_user", 'r')
	
	users=[]
	while 1:
		line = f.readline().strip()
		if not line:	break
		else:
			users.append(line)
	if len(users) !=0:
		clearUser.execute(users)
	os.system("rm -f .ldap_diff_user 2> /dev/null")				
	fuser.close()
except:
	log.error('clearing removed user')
	pass
try:
	import clearGroup
	fgroup = file(".ldap_diff_group", 'r')
	groups=[]
	while 1:
		line = f.readline().strip()
		if not line:	break
		else:	
			groups.append(line)
	if len(groups) !=0:
		clearGroup.execute(groups)
	os.system("rm -f .ldap_diff_group 2> /dev/null")		
	fgroup.close()
except:
	log.error('clearing removed group')
	pass	

# clear all invalid user
import clearInvalidUserNGroup
try:
	clearInvalidUserNGroup.execute()
except:
	log.error('clearInvalidUserNGroup Fail!')
	

print "0"
log.info('Sync LDAP success.')
os.system("rm -f .ldap_tmp 2> /dev/null")


