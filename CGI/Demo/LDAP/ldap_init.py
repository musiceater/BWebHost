import os

"""format2 = "/usr/sbin/ldapclient manual " \
                         "-a credentialLevel=proxy " \
                         "-a authenticationMethod=simple " \
                         "-a proxyDN=%s " \
                         "-a proxyPassword=%s " \
                         "-a defaultSearchBase=%s " \
                         "-a domainName=%s " \
                         "-a defaultServerList=%s " \
                         "-a attributeMap=group:userpassword=userPassword " \
                         "-a attributeMap=group:memberuid=memberUid " \
                         "-a attributeMap=group:gidnumber=gidNumber " \
                         "-a attributeMap=passwd:gecos=cn " \
                         "-a attributeMap=passwd:gidnumber=gidNumber " \
                         "-a attributeMap=passwd:uidnumber=uidNumber " \
                         "-a attributeMap=passwd:uid=uid " \
                         "-a attributeMap=passwd:homedirectory=homeDirectory " \
                         "-a attributeMap=passwd:loginshell=loginShell " \
                         "-a attributeMap=shadow:shadowflag=shadowFlag " \
                         "-a attributeMap=shadow:userpassword=userPassword " \
                         "-a attributeMap=shadow:uid=uid " \
                         "-a objectClassMap=group:posixGroup=posixGroup " \
                         "-a objectClassMap=passwd:posixAccount=posixAccount " \
                         "-a objectClassMap=shadow:shadowAccount=shadowAccount " \
                         "-a serviceSearchDescriptor=passwd:%s?sub " \
                         "-a serviceSearchDescriptor=group:%s?sub";
"""

user_dn='cn=Administrator,cn=Users,DC=nas-test,DC=ad'
password='evt'
base_dn='DC=nas-test,DC=ad'
domain_name='nas-test.ad'
ldap_server_ip='172.18.8.78'
# winArgs = "ldapclient manual \
# -a credentialLevel=proxy \
# -a authenticationMethod=simple \
# -a proxyDN=%s \
# -a proxyPassword=%s \
# -a defaultSearchBase=%s \
# -a domainName=%s \
# -a defaultServerList=%s \
# -a attributeMap=group:userpassword=userPassword \
# -a attributeMap=group:memberuid=memberUid \
# -a attributeMap=group:gidnumber=gidNumber \
# -a attributeMap=passwd:gecos=cn \
# -a attributeMap=passwd:gidnumber=gidNumber \
# -a attributeMap=passwd:uidnumber=uidNumber \
# -a attributeMap=passwd:homedirectory=\'work\' \
# -a attributeMap=passwd:loginshell=loginShell \
# -a attributeMap=shadow:shadowflag=shadowFlag \
# -a attributeMap=shadow:userpassword=userPassword \
# -a objectClassMap=group:posixGroup=group \
# -a objectClassMap=passwd:posixAccount=user \
# -a objectClassMap=shadow:shadowAccount=user \
# -a serviceSearchDescriptor=passwd:%s?sub \
# -a serviceSearchDescriptor=group:%s?sub"%(user_dn, password, base_dn, domain_name, ldap_server_ip, base_dn, base_dn)
# winArgs = "ldapclient manual \
# -a credentialLevel=proxy \
# -a authenticationMethod=simple \
# -a proxyDN=%s \
# -a proxyPassword=%s \
# -a defaultSearchBase=%s \
# -a domainName=%s \
# -a defaultServerList=%s \
# -a attributeMap=group:userpassword=userPassword \
# -a attributeMap=group:memberuid=memberUid \
# -a attributeMap=group:gidnumber=primaryGroupID \
# -a attributeMap=passwd:gecos=cn \
# -a attributeMap=passwd:gidnumber=primaryGroupID \
# -a attributeMap=passwd:uidnumber=uSNCreated \
# -a attributeMap=passwd:homedirectory=\'work\' \
# -a attributeMap=passwd:loginshell=loginShell \
# -a attributeMap=shadow:shadowflag=shadowFlag \
# -a attributeMap=shadow:userpassword=userPassword \
# -a objectClassMap=group:posixGroup=group \
# -a objectClassMap=passwd:posixAccount=user \
# -a objectClassMap=shadow:shadowAccount=user \
# -a serviceSearchDescriptor=passwd:%s?sub \
# -a serviceSearchDescriptor=group:%s?sub"%(user_dn, password, base_dn, domain_name, ldap_server_ip, base_dn, base_dn)

winArgs = "ldapclient manual \
-a credentialLevel=proxy \
-a authenticationMethod=simple \
-a proxyDN=%s \
-a proxyPassword=%s \
-a defaultSearchBase=%s \
-a domainName=%s \
-a defaultServerList=%s \
-a attributeMap=group:userpassword=msSFU30Password \
-a attributeMap=group:memberuid=msSFU30MemberUid \
-a attributeMap=group:gidnumber=msSFU30GidNumber \
-a attributeMap=passwd:gecos=msSFU30Gecos \
-a attributeMap=passwd:gidnumber=msSFU30GidNumber \
-a attributeMap=passwd:uidnumber=msSFU30UidNumber \
-a attributeMap=passwd:homedirectory=msSFU30HomeDirectory \
-a attributeMap=passwd:loginshell=msSFU30LoginShell \
-a attributeMap=shadow:shadowflag=msSFU30ShadowFlag \
-a attributeMap=shadow:userpassword=msSFU30Password \
-a objectClassMap=group:posixGroup=group \
-a objectClassMap=passwd:posixAccount=user \
-a objectClassMap=shadow:shadowAccount=user \
-a serviceSearchDescriptor=passwd:%s?sub \
-a serviceSearchDescriptor=group:%s?sub"%(user_dn, password, base_dn, domain_name, ldap_server_ip, base_dn, base_dn)

os.system("cp /etc/resolv.conf /etc/resolv.conf.bak");

os.system("/usr/sbin/svcadm restart dns/client");
os.system("/usr/sbin/svcadm restart system/name-service-cache");
os.system("/usr/sbin/svcadm disable system/name-service-cache")
os.system("/usr/sbin/svcadm enable system/name-service-cache")
port=389
os.system("ldapsearch -v -h %s -p %d -w \"%s\" -D \"%s\" -b \"%s\" -s base \"objectclass=*\""%(ldap_server_ip,port,password,user_dn,base_dn))

os.system("cp /etc/nsswitch.conf /etc/nsswitch.nas_ldap")
os.system("/usr/sbin/svcadm disable ldap/client")
os.system("rm -rf /var/ldap/*")	
os.system(winArgs)
#os.system("cp /etc/nsswitch.ldap /etc/nsswitch.conf")
os.system("cp /root/LDAP/*.conf /etc/")


os.system("/usr/sbin/svcadm disable ldap/client")
os.system("/usr/sbin/svcadm enable -r ldap/client")

### config

os.system("/usr/sbin/svcadm restart dns/client")

os.system("/usr/sbin/svcadm disable system/name-service-cache")
os.system("/usr/sbin/svcadm enable system/name-service-cache")



### config pam

   
#print winArgs							
"""
       if(ldap_server_is_windows == 1)
       {
            sprintf(cmdline, format3,
                    user_dn,          //proxyDN
                    password,         //proxyPassword
                    base_dn,          //defaultSearchBase
                    domain_name,      //domainName
                    ldap_server_ip,   //defaultServerList
                    base_dn,         //serviceSearchDescriptor
                    base_dn);        //serviceSearchDescriptor
       }
       else
       {
            sprintf(cmdline, format2,
                    user_dn,          //proxyDN
                    password,         //proxyPassword
                    base_dn,          //defaultSearchBase
                    domain_name,      //domainName
                    ldap_server_ip,   //defaultServerList
                    base_dn,         //serviceSearchDescriptor
                    base_dn);        //serviceSearchDescriptor
       }
"""	   