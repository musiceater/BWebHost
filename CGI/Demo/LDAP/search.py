import os


user_dn='cn=Administrator,cn=Users,DC=nas-test,DC=ad'
password='evt'
base_dn='DC=nas-test,DC=ad'
domain_name='nas-test.ad'
ldap_server_ip='172.18.8.78'


port=389
os.system("ldapsearch -v -h %s -p %d -w \"%s\" -D \"%s\" -b \"%s\" -s base \"objectclass=*\""%(ldap_server_ip,port,password,user_dn,base_dn))



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