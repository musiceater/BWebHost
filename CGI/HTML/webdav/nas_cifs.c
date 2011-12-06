/*
 * File:   nas_cifs.c
 * Author: Jason.zhou
 *
 * Created on January 7, 2009, 3:24 PM
 */

#include <assert.h>
#include <ctype.h>
#include <errno.h>
#include <libgen.h>
#include <libintl.h>
#include <libnvpair.h>
#include <locale.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <strings.h>
#include <unistd.h>
#include <fcntl.h>
#include <zone.h>
#include <sys/mkdev.h>
#include <sys/mntent.h>
#include <sys/mnttab.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <sys/avl.h>
#include <arpa/inet.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>
#include <netinet/in_systm.h>
#include <netinet/in.h>
#include <netinet/ip.h>
#include <netinet/ip_icmp.h>
#include <netdb.h>
#include <setjmp.h>
#include <errno.h>
#include "nas_cifs.h"

char domain_name[256] = "";
char dns_server_ip[256] = "";
char domain_controller_name[256] = "";
char domain_administrator[256] = "";
char domain_administrator_passwd[256] = "";
int domain_mode = 0;

static struct CifsShareObject* g_shareObjList = NULL;
static int g_getArraySizeFlag = 0;
static int g_arraySize = 0;

char cifs_last_message[1024] = {0};

int check_cifs_service_status();
void cifs_ensure_nsswitch_ok(char filename[]);

///
/// register error callback function
///
void cifs_register_error_callbackfn(cifs_error_cbfunc err_fn)
{
    g_err_cbfunc = err_fn;
}

//
//verify net connect
//
int verify_net_connect(char netnode[])
{
    int success = 0;
    int i = 0;
    char cmdline[1024] = {0};

    cifs_log_init("/var/log/NAS_Cifs.log");

    if(netnode == NULL || strlen(netnode) == 0)
    {
        cifs_log_it(NAS_ERROR, "verify_net_connect: netnode is null");
        cifs_log_close();
        return 1;
    }

    cifs_log_it(NAS_IMPORTANT, "netnode: %s", netnode);

    //------------------------------------
    #if 0
    if(dns_server_ip == NULL || dns_server_ip[0] == ' ')
    {
        strcpy(dns_server_ip, "127.0.0.1");
    }
    
    //config temp resolv.conf, so as to verify net connectivity
    sprintf(cmdline, "cp /etc/resolv.conf /etc/resolv.conf.bak");
    system(cmdline);

    sprintf(cmdline, "cat /etc/resolv.conf|grep %s", dns_server_ip);
    success = system(cmdline);
    if(success != 0)
    {
        remove("/etc/resolv.conf.tmp");
        sprintf(cmdline, "echo nameserver %s >> /etc/resolv.conf.tmp", dns_server_ip);
        system(cmdline);

        sprintf(cmdline, "cat /etc/resolv.conf >> /etc/resolv.conf.tmp");
        system(cmdline);

        system("mv /etc/resolv.conf.tmp /etc/resolv.conf");
    }
    else
    {
        remove("/etc/resolv.conf.tmp");
        sprintf(cmdline, "cat /etc/resolv.conf|grep %s >> /etc/resolv.conf.tmp", dns_server_ip);
        system(cmdline);

        sprintf(cmdline, "cat /etc/resolv.conf|grep -v %s >> /etc/resolv.conf.tmp", dns_server_ip);
        system(cmdline);

        system("mv /etc/resolv.conf.tmp /etc/resolv.conf");
    }

    sprintf(cmdline, "cat /etc/nsswitch.conf|grep \"host:\"|grep dns");
    success = system(cmdline);
    if(success != 0)
    {
        cifs_log_it(NAS_ERROR,"ensure_nsswitch_conf");
        cifs_ensure_nsswitch_ok("/etc/nsswitch.conf");
    }

    //to avoid nis config corrupt nsswitch.conf
    sprintf(cmdline, "cat /etc/nsswitch.nis|grep \"host:\"|grep dns");
    success = system(cmdline);
    cifs_log_it(NAS_ERROR,"%s, return: %d", cmdline, success);
    if(success != 0)
    {
        cifs_log_it(NAS_ERROR,"ensure_nsswitch_nis");
        cifs_ensure_nsswitch_ok("/etc/nsswitch.nis");
    }

    system("svcadm restart dns/client");

    system("svcadm restart system/name-service-cache");
    #endif
    //---------------------------------------------------
    int argc = 0;
    char** argv = NULL;

    sprintf(cmdline, "ping %s", netnode);
    argc = Cifs_getArgc(cmdline);
    argv = Cifs_parseCmdLine(cmdline);
    success = cifs_call_ping_cmd(argc, argv);
    printf("success: %d\n", success);

    //clear
    for(i = 0; i < argc; i++)
    {
        free(argv[i]);
        argv[i] = NULL;
    }
    free(argv);

    //---------------------------------------------------
    //restore dns
    #if 0
    system("mv /etc/resolv.conf.bak /etc/resolv.conf");
    system("svcadm restart dns/client");
    system("svcadm restart system/name-service-cache");
    #endif

    cifs_log_it(NAS_IMPORTANT, "verify net connect, return: %d", success);
    cifs_log_close();

    return success;
}

void cifs_ensure_nsswitch_ok(char filename[])
{
    FILE* fp = fopen(filename, "r");
    if(fp == NULL)
    {
        return;
    }

    char temp_filename[256] = {0};
    sprintf(temp_filename, "%s.tmp", filename);
    FILE* fp_temp = fopen(temp_filename, "w+");
    if(fp_temp == NULL)
    {
        fclose(fp);
        return;
    }

    while(!feof(fp))
    {
        char line[256] = {0};
        fgets(line, sizeof(line), fp);
        if(line == NULL)
        {
            continue;
        }

        if(strncmp(line, "hosts:", strlen("hosts:")) == 0)
        {
            strcpy(line, "hosts:    files   dns\n");
        }

        fputs(line, fp_temp);
    }
    fclose(fp);
    fclose(fp_temp);

    char cmdline[1024] = {0};
    sprintf(cmdline, "mv %s %s", temp_filename, filename);
    system(cmdline);
}

int cifs_verify_domain_ip(char domain_server_ip[], char domain_name[], char domain_controller_name[])
{
    //check domain server ip
    if(domain_server_ip == NULL || strlen(domain_server_ip) == 0)
    {
        cifs_log_it(NAS_ERROR, "Invalid input parameter, domain_server_ip is null.");
        cifs_log_close();
        return 1;
    }

    int success = verify_net_connect(domain_server_ip);
    if(success != 0)
    {
        cifs_log_it(NAS_ERROR, "Can not connect to domain_server_ip: %s.", domain_server_ip);
        cifs_log_close();
        return 2;
    }

    char cmdline[1024] = {0};

    //------------------------------------
    //config temp resolv.conf, so as to verify net connectivity

    sprintf(cmdline, "cp /etc/resolv.conf /etc/resolv.conf.bak");
    system(cmdline);

    sprintf(cmdline, "cat /etc/resolv.conf|grep %s", domain_server_ip);
    success = system(cmdline);
    if(success != 0)
    {
        remove("/etc/resolv.conf.tmp");
        sprintf(cmdline, "echo nameserver %s >> /etc/resolv.conf.tmp", domain_server_ip);
        system(cmdline);

        sprintf(cmdline, "cat /etc/resolv.conf >> /etc/resolv.conf.tmp");
        system(cmdline);

        system("mv /etc/resolv.conf.tmp /etc/resolv.conf");
    }
    else
    {
        remove("/etc/resolv.conf.tmp");
        sprintf(cmdline, "cat /etc/resolv.conf|grep %s >> /etc/resolv.conf.tmp", domain_server_ip);
        system(cmdline);

        sprintf(cmdline, "cat /etc/resolv.conf|grep -v %s >> /etc/resolv.conf.tmp", domain_server_ip);
        system(cmdline);

        system("mv /etc/resolv.conf.tmp /etc/resolv.conf");
    }

    sprintf(cmdline, "cat /etc/nsswitch.conf|grep \"host:\"|grep dns");
    success = system(cmdline);
    if(success != 0)
    {
        cifs_log_it(NAS_ERROR,"ensure_nsswitch_conf");
        cifs_ensure_nsswitch_ok("/etc/nsswitch.conf");
    }

    //to avoid nis config corrupt nsswitch.conf
    sprintf(cmdline, "cat /etc/nsswitch.nis|grep \"host:\"|grep dns");
    success = system(cmdline);
    cifs_log_it(NAS_ERROR,"%s, return: %d", cmdline, success);
    if(success != 0)
    {
        cifs_log_it(NAS_ERROR,"ensure_nsswitch_nis");
        cifs_ensure_nsswitch_ok("/etc/nsswitch.nis");
    }

    system("svcadm restart dns/client");

    system("svcadm restart system/name-service-cache");

    //------------------------------------
    //get reverse ip address
    char reverse_ip_str[256] = {0};
    char *p = domain_server_ip;
    char parts[4][4];
    int part_no = 0;
    int index = 0;
    for(int i = 0; i < 4; i++)
    {
        memset(parts[i], 0, sizeof(parts[i]));
    }

    while(*p != '\0')
    {
        if(*p == '.')
        {
            part_no++;
            index = 0;
            p++;
            continue;
        }

        parts[part_no][index] = *p;
        index++;
        p++;
    }

    for(int i = 1; i <= 4; i++)
    {
        strcat(reverse_ip_str, parts[4-i]);
        strcat(reverse_ip_str, ".");
    }
    strcat(reverse_ip_str, "in-addr.arpa.");

    cifs_log_it(NAS_INFO, "reverse_ip_str: %s", reverse_ip_str);

    //------------------------------------
    //get domain controller

    sprintf(cmdline, "dig -x %s|grep -w \"%s\" > temp_domain_ip.txt", domain_server_ip, reverse_ip_str);
    int ret = system(cmdline);
    cifs_log_it(NAS_INFO, "%s, return: %d", cmdline, ret);
    if(ret != 0)
    {
        //restore dns
        system("mv /etc/resolv.conf.bak /etc/resolv.conf");
        system("svcadm restart dns/client");
        system("svcadm restart system/name-service-cache");

        cifs_log_it(NAS_ERROR, "Can't execute dig -x %s.", domain_server_ip);
        cifs_log_close();
        return 3;
    }

    FILE* fp = fopen("temp_domain_ip.txt", "r");
    if(fp == NULL)
    {
        //restore dns
        system("mv /etc/resolv.conf.bak /etc/resolv.conf");
        system("svcadm restart dns/client");
        system("svcadm restart system/name-service-cache");

        cifs_log_it(NAS_ERROR, "failed to open temp_domain.txt.");
        cifs_log_close();
        return 4;
    }

    strcpy(domain_controller_name, "");
    while(!feof(fp))
    {
        char line[256] = {0};
        fgets(line, sizeof(line), fp);
        if(line == NULL || strlen(line) == 0 || line[0] == '\r' || line[0] == '\n' || line[0] == ';')
        {
            continue;
        }

        char temp[256] = {0};
        sscanf(line, "%s %s %s %s %s", temp, temp, temp, temp, domain_controller_name);
        if(domain_controller_name != NULL)
        {
            domain_controller_name[strlen(domain_controller_name) - 1] = '\0'; //remove the last dot
            break;
        }
    }
    fclose(fp);
    remove("temp_domain_ip.txt");

    cifs_log_it(NAS_INFO, "domain_controller_name: %s", domain_controller_name);

    //------------------------------------
    //get domain name

    strcpy(domain_name, "");
    char* q = domain_controller_name;
    while(*q != '\0')
    {
        if(*q == '.')
        {
            q++;
            break;
        }

        q++;
    }

    if(q != NULL)
    {
        strcpy(domain_name, q);
    }

    cifs_log_it(NAS_INFO, "domain_name: %s", domain_name);

    //restore dns
    system("mv /etc/resolv.conf.bak /etc/resolv.conf");
    system("svcadm restart dns/client");
    system("svcadm restart system/name-service-cache");

    //save dns server ip
    strcpy(dns_server_ip, domain_server_ip);

    //ok
    return 0;
}

//
//set domain parameter
//
int nas_set_domain_parameter(char domainName[], char dnsServerIp[], char domainControllerName[])
{
    int success = 0;
    char cmdline[1024] = {0};
    int argc = 0;
    char** argv = NULL;

    cifs_log_init("/var/log/NAS_Cifs.log");

    //-----------------------------------------
    if(domainName == NULL || strlen(domainName) == 0)
    {
        cifs_log_it(NAS_ERROR, "Invalid domain parameter, domain name is null.");
        cifs_log_close();
        return 1;
    }

    if(dnsServerIp == NULL || strlen(dnsServerIp) == 0)
    {
        cifs_log_it(NAS_ERROR, "Invalid domain parameter, dns server ip address is null.");
        cifs_log_close();
        return 2;
    }

    if(domainControllerName == NULL || strlen(domainControllerName) == 0)
    {
        cifs_log_it(NAS_ERROR, "Invalid domain parameter, domain controller name is null.");
        cifs_log_close();
        return 3;
    }

    //-----------------------------------------
    strcpy(domain_name, domainName);
    strcpy(dns_server_ip, dnsServerIp);
    strcpy(domain_controller_name, domainControllerName);

    cifs_log_it(NAS_IMPORTANT, "set domain parameter, return: %d", success);
    cifs_log_close();
    return success;
}

//
//join doamin
//
int nas_join_domain(char domainAdministrator[], char domainAdministratorPasswd[])
{
    int success = 0;
    int i = 0;
    char cmdline[1024] = {0};

    cifs_log_init("/var/log/NAS_Cifs.log");

    success = check_cifs_service_status();
    if(success != 0)
    {
        cifs_log_it(NAS_IMPORTANT, "cifs service status is not OK.");
        cifs_log_close();
        return 1;
    }

    //check domain administrator user
    if(domainAdministrator == NULL || strlen(domainAdministrator) == 0)
    {
        cifs_log_it(NAS_IMPORTANT, "domain adminsitrator is null.");
        cifs_log_close();
        return 2;
    }
    else
    {
        strcpy(domain_administrator, domainAdministrator);
    }

    //check domain administrator password
    if(domainAdministratorPasswd == NULL || strlen(domainAdministratorPasswd) == 0)
    {
        strcpy(domain_administrator_passwd, "");
    }
    else
    {
        strcpy(domain_administrator_passwd, domainAdministratorPasswd);
    }

    system("cp /etc/resolv.conf /etc/resolv.conf.bak");
    system("cp /etc/nsswitch.conf /etc/nsswitch.conf.bak");
    system("cp /etc/krb5/krb5.conf /etc/krb5/krb5.conf.bak");

    //config resolv.conf
    success = nas_config_resolv_conf();
    if(success != 0)
    {
        system("cp /etc/resolv.conf.bak /etc/resolv.conf");
        cifs_log_it(NAS_ERROR, "failed to config /etc/resolv.conf");
        cifs_log_close();
        return 3;
    }

    //config nsswitch.conf
    success = nas_config_nsswitch_conf();
    if(success != 0)
    {
        system("cp /etc/resolv.conf.bak /etc/resolv.conf");
        system("cp /etc/nsswitch.conf.bak /etc/nsswitch.conf");
        cifs_log_it(NAS_ERROR, "failed to config /etc/nsswitch.conf");
        cifs_log_close();
        return 4;
    }

    //config krb5.conf
    success = nas_config_krb_conf();
    if(success != 0)
    {
        system("cp /etc/resolv.conf.bak /etc/resolv.conf");
        system("cp /etc/nsswitch.conf.bak /etc/nsswitch.conf");
        system("cp /etc/krb5/krb5.conf.bak /etc/krb5/krb5.conf");
        cifs_log_it(NAS_ERROR, "failed to config /etc/krb5/krb5.conf");
        cifs_log_close();
        return 5;
    }

    //sync system clock
    success = nas_sync_system_clock();

    int to_disable_ldap = 1;

    sprintf(cmdline, "ldapclient list|grep NS_LDAP_SERVERS|cut -d \" \" -f2 > 111.txt");
    success = system(cmdline);
    FILE* fpTemp = fopen("111.txt", "r");
    if(fpTemp == NULL)
    {
        to_disable_ldap = 0;
    }

    if(to_disable_ldap == 1)
    {
        char temp_buf[1024] = {0};
        fgets(temp_buf, sizeof(temp_buf), fpTemp);
        fclose(fpTemp);
        remove("111.txt");
        if(temp_buf == NULL || strlen(temp_buf) == 0)
        {
            to_disable_ldap = 0;
        }
        else
        {
            char ldap_server_ip[32] = {0};
            sscanf(temp_buf, "%s", ldap_server_ip);
            if(ldap_server_ip == NULL)
            {
                to_disable_ldap = 0;
            }
            else
            {
                if(strcmp(ldap_server_ip, dns_server_ip) == 0)
                {
                    to_disable_ldap = 0;
                }
            }
        }
    }

    if(to_disable_ldap == 1)
    {
        system("cp /etc/nsswitch.dns /etc/nsswitch.conf");
        system("svcadm disable ldap/client");
    }


    //------------------------------------
    //config temp resolv.conf, so as to verify net connectivity

    sprintf(cmdline, "cat /etc/resolv.conf|grep %s", dns_server_ip);
    success = system(cmdline);
    if(success != 0)
    {
        remove("/etc/resolv.conf.tmp");
        sprintf(cmdline, "echo nameserver %s >> /etc/resolv.conf.tmp", dns_server_ip);
        system(cmdline);

        sprintf(cmdline, "cat /etc/resolv.conf >> /etc/resolv.conf.tmp");
        system(cmdline);

        system("mv /etc/resolv.conf.tmp /etc/resolv.conf");
    }
    else
    {
        remove("/etc/resolv.conf.tmp");
        sprintf(cmdline, "cat /etc/resolv.conf|grep %s >> /etc/resolv.conf.tmp", dns_server_ip);
        system(cmdline);

        sprintf(cmdline, "cat /etc/resolv.conf|grep -v %s >> /etc/resolv.conf.tmp", dns_server_ip);
        system(cmdline);

        system("mv /etc/resolv.conf.tmp /etc/resolv.conf");
    }

    sprintf(cmdline, "cat /etc/nsswitch.conf|grep \"host:\"|grep dns");
    success = system(cmdline);
    if(success != 0)
    {
        cifs_log_it(NAS_ERROR,"ensure_nsswitch_conf");
        cifs_ensure_nsswitch_ok("/etc/nsswitch.conf");
    }

    //to avoid nis config corrupt nsswitch.conf
    sprintf(cmdline, "cat /etc/nsswitch.nis|grep \"host:\"|grep dns");
    success = system(cmdline);
    cifs_log_it(NAS_ERROR,"%s, return: %d", cmdline, success);
    if(success != 0)
    {
        cifs_log_it(NAS_ERROR,"ensure_nsswitch_nis");
        cifs_ensure_nsswitch_ok("/etc/nsswitch.nis");
    }

    system("svcadm restart dns/client");
    system("svcadm restart system/name-service-cache");
    int ret2 = system("svcs|grep smb/server|grep -w online");
    if(ret2 == 0)
    {
    	system("svcadm restart smb/server");
    }
    else
    {
    	system("svcadm disable smb/server");
    	system("svcadm enable -r smb/server");
    }

     //---------------------------------------

    //to wait a while for cifs service ok
    cifs_log_it(NAS_INFO, "waiting for cifs service restart...");
    int time_out = 30;
    int t = 0;
    for(;;)
    {
        int ret = system("svcs|grep smb/server|grep -w online");
        if(ret == 0)
        {
            break;
        }
        sleep(1);
        t++;
        if(t == time_out)
        {
            cifs_log_it(NAS_ERROR, "failed to restart cifs service");
            cifs_log_close();
            return 5;
        }
    }

    cifs_log_it(NAS_INFO, "cifs service restart...OK");

    //---------------------------------------
    //join domain

    int current_domain_mode = 0; //default to workgroup mode
    sprintf(cmdline, "smbadm list|grep \"Workgroup:\"");
    success = system(cmdline);
    if(success != 0)
    {
        current_domain_mode = 1;
    }

    remove("smbadm.exp");
    remove("exp.log");
    FILE* fp = fopen("smbadm.exp", "w+");
    if(fp == NULL)
    {
        cifs_log_it(NAS_ERROR, "failed to create smbadm.exp");
        cifs_log_close();
        return 6;
    }

    fprintf(fp, "#!/usr/bin/expect\n");
    fprintf(fp, "\n");

    fprintf(fp, "spawn smbadm join -u %s %s\n", domain_administrator, domain_name);
    fprintf(fp, "\n");
    
    fprintf(fp, "expect \"no]:\"\n");
    fprintf(fp, "sleep 1\n");
    fprintf(fp, "send \"yes\\n\"\n");

    /*if(current_domain_mode == 0)
    {
        fprintf(fp, "expect \"]:\"\n");
        fprintf(fp, "sleep 1\n");
        fprintf(fp, "send \"yes\\n\"\n");
    }*/

    fprintf(fp, "expect \"*password:\"\n");
    fprintf(fp, "sleep 1\n");
    fprintf(fp, "send \"%s\\n\"\n", domain_administrator_passwd);

    fprintf(fp, "expect eof\n");
    fprintf(fp, "exit\n");
    fclose(fp);

    sprintf(cmdline, "expect smbadm.exp > exp.log");
    system(cmdline);
    int ret = system("cat exp.log|grep -w \"Successfully\"");
    if(ret != 0)
    {
        cifs_log_it(NAS_ERROR, "failed to join domain: %s", domain_name);
        success = 6;
    }
    else
    {
        domain_mode = 1; //domain mode
        success = 0; //successful
    }

    //---------------------------------------
    if(success == 0)
    {
//    	int success2 = 0;
//    	char domain_sid[256];
    	
//    	memset(domain_sid, 0, 256);
        //system("svcadm disable idmap");
    	//make sure idmap enable
    	system("svcadm enable idmap");

        //remove old idmap rules
        sprintf(cmdline, "idmap remove -a");
        system(cmdline);

        //reset idmap
        strcpy(cmdline, "rm -rf /var/run/idmap/idmap.db");
        system(cmdline);
        
        
        system("svcadm disable idmap");
        system("svcadm enable -r idmap");

        //add new winuser map rule
        sprintf(cmdline, "idmap add winuser:*@%s unixuser:*", domain_name);
        system(cmdline);

        //add new wingroup map rule
        sprintf(cmdline, "idmap add wingroup:*@%s unixgroup:*", domain_name);
        system(cmdline);
        
        //success2 = system("svccfg -s smb/server listprop | grep smbd/domain_sid | awk '/astring/{print $3}' > temp_svccfg_output.txt");
//        cifs_log_it(NAS_INFO, "svccfg command result=%d", success2);
//        if(success2 != 0)
//        {
//        	system("cp /etc/resolv.conf.bak /etc/resolv.conf");
//        	system("cp /etc/nsswitch.conf.bak /etc/nsswitch.conf");
//        	system("cp /etc/krb5/krb5.conf.bak /etc/krb5/krb5.conf");
//        	return 7;
//        }
//        fp = fopen("temp_svccfg_output.txt", "r");
//        if(fp == NULL)
//        {
//        	system("cp /etc/resolv.conf.bak /etc/resolv.conf");
//        	system("cp /etc/nsswitch.conf.bak /etc/nsswitch.conf");
//        	system("cp /etc/krb5/krb5.conf.bak /etc/krb5/krb5.conf");
//        	return 8;
//        }
        
//        fscanf(fp, "%s", domain_sid);
//        fclose(fp);
//        remove("temp_svccfg_output.txt");
//        cifs_log_it(NAS_INFO, "svccfg command get domain_sid=[%s]", domain_sid);
        
//        sprintf(cmdline,"svccfg -s idmap setprop config/machine_sid=astring: %s", domain_sid);
//        cifs_log_it(NAS_INFO, "svccfg setprop command [%s]", cmdline);
//        success2 = system(cmdline);
//        cifs_log_it(NAS_INFO, "svccfg setprop command result=%d", success2);
//        if(success2 != 0)
//        {
//        	system("cp /etc/resolv.conf.bak /etc/resolv.conf");
//        	system("cp /etc/nsswitch.conf.bak /etc/nsswitch.conf");
//        	system("cp /etc/krb5/krb5.conf.bak /etc/krb5/krb5.conf");
//        	return 9;
//        }
        
//        sleep(2);
//        cifs_log_it(NAS_INFO, "restart smb/server......");
//        system("svcadm restart smb/server");
//                
//        sleep(2);
//        cifs_log_it(NAS_INFO, "restart idmap......");
//        system("svcadm restart idmap");
        
    }

    //restart cifs service
    //system("svcadm disable smb/server");
    //system("svcadm enable -r smb/server");
    
    //----------------------------------

    if(success != 0)
    {
        system("cp /etc/resolv.conf.bak /etc/resolv.conf");
        system("cp /etc/nsswitch.conf.bak /etc/nsswitch.conf");
        system("cp /etc/krb5/krb5.conf.bak /etc/krb5/krb5.conf");
    }
    
    cifs_log_it(NAS_IMPORTANT, "join domain, return: %d", success);
    cifs_log_close();

    return success;
}

//
//join workgroup
//
int nas_join_workgroup(char workgroup_name[])
{
    int success = 0;
    int i = 0;

    cifs_log_init("/var/log/NAS_Cifs.log");

    //check domain administrator user
    if(workgroup_name == NULL || strlen(workgroup_name) == 0)
    {
        cifs_log_it(NAS_IMPORTANT, "workgroup_name is null.");
        cifs_log_close();
        return 1;
    }

    //enable cifs service
    success = system("svcadm enable -r smb/server");

    //to wait a while for cifs service ok
    cifs_log_it(NAS_INFO, "waiting for cifs service restart...");
    int time_out = 30;
    int t = 0;
    for(;;)
    {
        int ret = system("svcs|grep smb/server|grep -w online");
        if(ret == 0)
        {
            break;
        }
        sleep(1);
        t++;
        if(t == time_out)
        {
            cifs_log_it(NAS_ERROR, "failed to restart cifs service");
            cifs_log_close();
            return 2;
        }
    }
    cifs_log_it(NAS_INFO, "waiting for cifs service restart...ok");

    //config pam.conf
    success = nas_config_pam_conf();
    if(success != 0)
    {
        cifs_log_it(NAS_ERROR, "failed to config /etc/pam.conf");
        cifs_log_close();
        return 3;
    }

    //to ensure the attribute of pam.conf is not being modified
    system("chown root:root /etc/pam.conf");
    system("chmod 644 /etc/pam.conf");

    //join workgroup
    char cmdline[1024] = {0};
    int current_domain_mode = 0; //default to workgroup mode
    sprintf(cmdline, "smbadm list|grep \"Workgroup:\"");
    success = system(cmdline);
    if(success != 0)
    {
        current_domain_mode = 1;
    }

    remove("smbadm.exp");
    remove("exp.log");
    FILE* fp = fopen("smbadm.exp", "w+");
    if(fp == NULL)
    {
        cifs_log_it(NAS_ERROR, "failed to create smbadm.exp");
        cifs_log_close();
        return 6;
    }

    fprintf(fp, "#!/usr/bin/expect\n");
    fprintf(fp, "\n");

    fprintf(fp, "spawn smbadm join -w %s\n", workgroup_name);
    fprintf(fp, "\n");

    if(current_domain_mode != 0)
    {
        fprintf(fp, "expect \"]:\"\n");
        fprintf(fp, "sleep 1\n");
        fprintf(fp, "send \"yes\\n\"\n");
    }

    fprintf(fp, "expect eof\n");
    fprintf(fp, "exit\n");
    fclose(fp);

    sprintf(cmdline, "expect smbadm.exp > exp.log");
    system(cmdline);
    int ret = system("cat exp.log|grep -w \"failed to join\"");
    if(ret == 0)
    {
        cifs_log_it(NAS_ERROR, "failed to join workgroup: %s", workgroup_name);
        success = 6;
    }
    else
    {
        domain_mode = 0; //workgroup mode
        success = 0; //successful
    }
  
    cifs_log_it(NAS_IMPORTANT, "join workgroup, return: %d", success);
    cifs_log_close();

    return success;
}

int check_cifs_service_status()
{
    int success = 0;

    char cmdline[1024] = {0};
    sprintf(cmdline, "svcs smb/server | grep maintenance");
    success = system(cmdline);
    if(success == 0)
    {
        cifs_log_it(NAS_IMPORTANT, "cifs service status is maintenance");
        cifs_log_close();
        return 1;
    }

    sprintf(cmdline, "svcs smb/server | grep online | cut -d \" \" -f1 > 111.txt");
    success = system(cmdline);
    FILE* fp = fopen("111.txt", "r");
    if(fp == NULL)
    {
        cifs_log_it(NAS_IMPORTANT, "failed to check cifs status online*");
        cifs_log_close();
        return 1;
    }
    char status[32] = {0};
    fscanf(fp, "%s", status);
    fclose(fp);
    #if 0
    if(strcmp(status, "online*") == 0)
    {
        cifs_log_it(NAS_IMPORTANT, "cifs service status is online*");
        cifs_log_close();
        return 1;
    }
    #endif

    remove("111.txt");

    return success;
}

//get cifs mode
int nas_cifs_get_domain_group_mode(struct DomainGroupObject* pDomainGroupObject)
{
    int success = 0;
    int i = 0;
    char line[256] = {0};

    cifs_log_init("/var/log/NAS_Cifs.log");

    //-----------------------------------------
    success = check_cifs_service_status();
    if(success != 0)
    {
        cifs_log_it(NAS_IMPORTANT, "cifs service status is not OK.");
        cifs_log_close();
        return 1;
    }

    char cmdline[1024] = {0};

    //-----------------------------------------
    int old_cifs_version = 1;
    char os_version[256];
    sprintf(cmdline, "uname -a|cut -d \" \" -f4|cut -d \"_\" -f2 > temp_build.txt");
    system(cmdline);
    FILE* fp = fopen("temp_build.txt", "r");
    if(fp != NULL)
    {
        fscanf(fp, "%s", os_version);
        if(strcmp(os_version, "105") >= 0)
        {
            old_cifs_version = 0;
        }
        fclose(fp);
        remove("temp_build.txt");
    }

    cifs_log_it(NAS_IMPORTANT, "old_cifs_version: %d", old_cifs_version);

    //-----------------------------------------
    memset(cmdline, 0, sizeof(cmdline));
    if(old_cifs_version)
    {
        sprintf(cmdline, "smbadm list|grep \"Workgroup\"");
        int ret = system(cmdline);
        if(ret == 0)
        {
            pDomainGroupObject->cifs_mode = 0; //workgroup mode
        }
        else
        {
            pDomainGroupObject->cifs_mode = 1; //domain mode
        }
    }
    else
    {
        sprintf(cmdline, "smbadm list|wc -l > temp_cifs.txt");
        system(cmdline);
        fp = fopen("temp_cifs.txt", "r");
        if(fp == NULL)
        {
            pDomainGroupObject->cifs_mode = 0; //default to workgroup mode
        }
        else
        {
            memset(line, 0, sizeof(line));
            fgets(line, sizeof(line), fp);
            fclose(fp);
            remove("temp_cifs.txt");

            if(line == NULL || strlen(line) == 0 || line[0] == '\r' || line[0] == '\n')
            {
                cifs_log_it(NAS_IMPORTANT, "failed to read line from temp result file.");
                cifs_log_close();
                return -2;
            }

            int line_count = 0;
            sscanf(line, "%d", &line_count);
            
            if(line_count < 2)
            {
                pDomainGroupObject->cifs_mode = 0; //workgroup mode
            }
            else
            {
                pDomainGroupObject->cifs_mode = 1; //domain mode
            }
        }
    }

    cifs_log_it(NAS_IMPORTANT, "cifs_mode: %d", pDomainGroupObject->cifs_mode);

    //-----------------------------------------
    if(pDomainGroupObject->cifs_mode == 0)
    {
        memset(cmdline, 0, sizeof(cmdline));
        if(old_cifs_version)
        {
            sprintf(cmdline, "smbadm list|cut -d \" \" -f2 > temp_cifs.txt");
        }
        else
        {
            sprintf(cmdline, "smbadm list|cut -d \" \" -f2|cut -d \"[\" -f2|cut -d \"]\" -f1 > temp_cifs.txt");
        }
        system(cmdline);
        fp = fopen("temp_cifs.txt", "r");
        if(fp == NULL)
        {
            cifs_log_it(NAS_IMPORTANT, "failed to get domain or group mode.");
            cifs_log_close();
            return 2;
        }
        memset(line, 0, sizeof(line));
        fgets(line, sizeof(line), fp);
        fclose(fp);
        remove("temp_cifs.txt");

        if(line == NULL || strlen(line) == 0 || line[0] == '\r' || line[0] == '\n')
        {
            cifs_log_it(NAS_IMPORTANT, "failed to read line from temp result file.");
            cifs_log_close();
            return -2;
        }

        sscanf(line, "%s", pDomainGroupObject->mode_name);
    }
    else //domain mode
    {
        // domain_server_ip
        char domain_server_ip[256];
        sprintf(cmdline, "smbadm list|grep \"Domain Controller\"|cut -d \"(\" -f2|cut -d \")\" -f1 > 111.txt");
        success = system(cmdline);
        FILE* fp = fopen("111.txt", "r");
        if(fp == NULL)
        {
            cifs_log_it(NAS_IMPORTANT, "failed to open temp file for reading.");
            cifs_log_close();
            return -1;
        }
        memset(line, 0, sizeof(line));
        fgets(line, sizeof(line), fp);
        fclose(fp);
        remove("111.txt");

        if(line == NULL || strlen(line) == 0 || line[0] == '\r' || line[0] == '\n')
        {
            //try to obtain from /etc/krb5/krb5.conf
            sprintf(cmdline, "cat /etc/krb5/krb5.conf|grep \"domain server ip\"|cut -d \":\" -f2|cut -d \" \" -f2 > 111.txt");
            system(cmdline);
            cifs_log_it(NAS_IMPORTANT,cmdline);
            fp = fopen("111.txt", "r");
            if(fp == NULL)
            {
                cifs_log_it(NAS_IMPORTANT, "failed to open temp file for reading.");
                cifs_log_close();
                return -3;
            }
            memset(line, 0, sizeof(line));
            fgets(line, sizeof(line), fp);
            fclose(fp);
            remove("111.txt");

            if(line == NULL || strlen(line) == 0 || line[0] == '\r' || line[0] == '\n')
            {
                cifs_log_it(NAS_IMPORTANT, "failed to read line from temp result file.");
                cifs_log_close();
                return -2;
            }
        }

        sscanf(line, "%s", domain_server_ip);
        if(domain_server_ip == NULL || strlen(domain_server_ip) == 0)
        {
            cifs_log_it(NAS_IMPORTANT, "failed to get domain_server_ip");
            cifs_log_close();
            return -3;
        }

        // domain_name
        char domain_name[256];
        char temp_buf[256];
        sprintf(cmdline, "more /etc/krb5/krb5.conf | grep \"default_realm =\" | cut -d \" \" -f3 > 111.txt");
        success = system(cmdline);
        fp = fopen("111.txt", "r");
        if(fp == NULL)
        {
            cifs_log_it(NAS_IMPORTANT, "failed to open temp file for reading.");
            cifs_log_close();
            return -3;
        }
        memset(line, 0, sizeof(line));
        fgets(line, sizeof(line), fp);
        fclose(fp);
        remove("111.txt");

        if(line == NULL || strlen(line) == 0 || line[0] == '\r' || line[0] == '\n')
        {
            cifs_log_it(NAS_IMPORTANT, "failed to read line from temp result file.");
            cifs_log_close();
            return -2;
        }

        sscanf(line, "%s", temp_buf);
        if(temp_buf == NULL || strlen(temp_buf) == 0)
        {
            cifs_log_it(NAS_IMPORTANT, "failed to get domain name");
            cifs_log_close();
            return -4;
        }

        int i = 0;
        for(i = 0; i < strlen(temp_buf); i++)
        {
            domain_name[i] = tolower(temp_buf[i]);
        }
        domain_name[i] = '\0';

        // domain_controller_name
        char domain_controller_name[256];
        sprintf(cmdline, "more /etc/krb5/krb5.conf | grep admin_server | cut -d \" \" -f3 > 111.txt");
        success = system(cmdline);
        fp = fopen("111.txt", "r");
        if(fp == NULL)
        {
            cifs_log_it(NAS_IMPORTANT, "failed to open temp file for reading.");
            cifs_log_close();
            return -3;
        }
        memset(line, 0, sizeof(line));
        fgets(line, sizeof(line), fp);
        fclose(fp);
        remove("111.txt");

        if(line == NULL || strlen(line) == 0 || line[0] == '\r' || line[0] == '\n')
        {
            cifs_log_it(NAS_IMPORTANT, "failed to read line from temp result file.");
            cifs_log_close();
            return -2;
        }

        sscanf(line, "%s", temp_buf);
        if(temp_buf == NULL || strlen(temp_buf) == 0)
        {
            cifs_log_it(NAS_IMPORTANT, "failed to get ldap server port");
            cifs_log_close();
            return -4;
        }

        strcpy(domain_controller_name, temp_buf);

        //
        strcpy(pDomainGroupObject->mode_name, domain_name);
        strcpy(pDomainGroupObject->domain_ip, domain_server_ip);
        strcpy(pDomainGroupObject->domain_server_name, domain_controller_name);
    }

    cifs_log_it(NAS_IMPORTANT, "mode_name: %s", pDomainGroupObject->mode_name);
    //-----------------------------------------
   
    cifs_log_it(NAS_IMPORTANT, "nas_cifs_get_domain_group_mode, return: %d", success);
    cifs_log_close();

    return success;
}

int nas_set_workgroup_access_user(char access_username[], char access_password[])
{
    int success = 0;
    char username[256] = {0};
    char password[256] = {0};

    cifs_log_init("/var/log/NAS_Cifs.log");

    if(access_username == NULL || strlen(access_username) == 0)
    {
        cifs_log_it(NAS_IMPORTANT, "access_username is null. default to root user.");
        strcpy(username, "root");
    }
    else
    {
        strcpy(username, access_username);
    }

    if(access_password == NULL || strlen(access_password) == 0)
    {
        cifs_log_it(NAS_IMPORTANT, "access_password is null. default to \"nas5100\"");
        strcpy(password, "nas5100");
    }
    else
    {
        strcpy(password, access_password);
    }

    success = nas_user_passwd(username, password);

    cifs_log_it(NAS_IMPORTANT, "nas_set_workgroup_access_user, return: %d", success);
    cifs_log_close();

    return success;
}

///
/// Add shared folder to array
///
/// It is a callback function, called by "show_share" of libsharemgr/commands.c
///
void AddShareObjectToList(struct CifsShareObject shareObj)
{
    if(g_getArraySizeFlag != 1)
    {
        *g_shareObjList = shareObj;
        g_shareObjList++;
    }

    g_arraySize++;
}

//
//list all shared folders
//
int nas_get_share_list(struct CifsShareObject shareArray[], int* arraySize)
{
    int success = 0;
    int i = 0;
	printf("123\n");
    cifs_log_init("/var/log/NAS_Cifs.log");

    int array_size = 0;
    int get_array_size_flag = 0;
    if(&shareArray[0] == NULL)
    {
        get_array_size_flag = 1;
    }

    char cmdline[1024] = {0};
#if 0
    g_shareObjList = &shareArray[0];
    if(g_shareObjList == NULL)
    {
        g_getArraySizeFlag = 1;
        cifs_log_it(NAS_IMPORTANT, "ready to get array size.");
    }
    else
    {
        g_getArraySizeFlag = 0;
    }
    g_arraySize = 0;

    int argc = 0;
    char** argv = NULL;

    sprintf(cmdline, "sharemgr show -vp cifs_group");
    argc = Cifs_getArgc(cmdline);
    argv = Cifs_parseCmdLine(cmdline);
    if(argv == NULL)
    {
        cifs_log_it(NAS_ERROR, "failed to parse command line, <%s>.", cmdline);
        cifs_log_close();
        return 1;
    }

    cifs_log_it(NAS_IMPORTANT, "cmdline: %s", cmdline);

    sharemgr_register_list_callbackfn(AddShareObjectToList);
    success = call_sharemgr_cmd(argc, argv);

    *arraySize = g_arraySize;
    sharemgr_unregister_list_callbackfn();

    //clear
    for(i = 0; i < argc; i++)
    {
        free(argv[i]);
        argv[i] = NULL;
    }
    free(argv);
#else
    if(get_array_size_flag == 1)
    {
        sprintf(cmdline, "sharemgr show -vp cifs_group|grep -v cifs_group|wc -l > temp_cifsshare.txt");
        system(cmdline);

        FILE* fp = fopen("temp_cifsshare.txt", "r");
        if(fp != NULL)
        {
            char line[256] = {0};
            fgets(line, sizeof(line), fp);
            fclose(fp);

            if(line != NULL && strlen(line) != 0 && line[0] != '\r' && line[0] != '\n')
            {
                sscanf(line, "%d", &array_size);
            }
        }
        remove("temp_cifsshare.txt");
    }
    else
    {
        sprintf(cmdline, "sharemgr show -vp cifs_group|grep -v cifs_group > temp_cifsshare.txt");
        system(cmdline);

        FILE* fp = fopen("temp_cifsshare.txt", "r");
        if(fp != NULL)
        {
            while(!feof(fp))
            {
                char line[256] = {0};
                fgets(line, sizeof(line), fp);
                if(line == NULL || strlen(line) == 0 || line[0] == '\r' || line[0] == '\n')
                {
                    continue;
                }

                cifs_log_it(NAS_ERROR, line);

                char tmp_name[256] = {0};
                char tmp_description[256] = {0};
                sscanf(line, "%s %s", tmp_name, tmp_description);

                if(tmp_name == NULL)
                {
                    continue;
                }

                char name[256] = {0};
                char path[256] = {0};
                char description[256] = {0};

                int index = 0;
                while(tmp_name[index] != '\0')
                {
                    if(tmp_name[index] == '=')
                    {
                        break;
                    }

                    name[index] = tmp_name[index];
                    index++;
                }

                char* p = strstr(tmp_name, "=");
                if(p != NULL)
                {
                    strcpy(path, p+1);
                }

                p = strstr(line, tmp_description);
                if(*p == '\"')
                {
                    strcpy(description, p+1);
                    index = 0;
                    for(;;)
                    {
                        if(description[index] == '\"' || description[index] == '\0')
                        {
                            description[index] = '\0';
                            break;
                        }
                        index++;
                    }
                }

                struct CifsShareObject shareObj;
                memset(&shareObj, 0, sizeof(shareObj));

                if(name == NULL || strlen(name) == 0)
                {
                    continue;
                }
                else
                {
                    strcpy(shareObj.share_name, name);
                }
                if(path == NULL  || strlen(path) == 0)
                {
                    continue;
                }
                else
                {
                    strcpy(shareObj.folder_path, path);
                }
                if(description == NULL || strlen(description) == 0)
                {
                    strcpy(shareObj.description, " ");
                }
                else
                {
                    strcpy(shareObj.description, description);
                }

                memcpy(&shareArray[array_size], &shareObj, sizeof(shareObj));
                array_size++;                
            }
            fclose(fp);
        }
        remove("temp_cifsshare.txt");
    }

    *arraySize = array_size;
    cifs_log_it(NAS_ERROR, "array_size: %d", *arraySize);
#endif
    cifs_log_it(NAS_IMPORTANT, "nas_get_share_list, return: %d", success);
    cifs_log_close();

    return success;
}

//
//modify "/etc/pam.conf"
//
int nas_config_pam_conf()
{
    int success = 0;
    char *com;
    char *str;
    int nfiles;

    int config_pam_smb = 0;

    char* config_file = "/etc/pam.conf";
    char* temp_file = "/etc/pam.tmp";

    //create a temp file
    FILE* fpTemp = fopen(temp_file, "w+");
    if(fpTemp == NULL)
    {
        cifs_log_it(NAS_ERROR, "failed to create temp file: %s", temp_file);
        return 1;
    }

    //open config file
    nfiles = config_open( config_file );
    if ( nfiles == 0 )
    {
        cifs_log_it( NAS_ERROR, "error opening command file: %s", config_file);
    }

    char temp_line[1024] = {0};

    // Process  config files
    if(nfiles > 0)
    {
        // Read next line from active file
        while(config_rd())
        {
            // Get the first token from line
            com = config_str();

            // Ignore blank lines & comments
            if(!com)
            {
                memset(temp_line, 0, sizeof(temp_line));
                sprintf(temp_line, "\n");
                fputs(temp_line, fpTemp);
                continue;
            }
            if(com[0] == '#')
            {
                memset(temp_line, 0, sizeof(temp_line));
                char* line = config_line();
                if(line != NULL)
                {
                    sprintf(temp_line, "%s", line);
                }
                else
                {
                    sprintf(temp_line, "\n");
                }
                fputs(temp_line, fpTemp);
                continue;
            }

            //other password required pam_smb_passwd.so.1 nowarn
            if ( config_its( "other" ) )
            {
                str = config_str();
                if(!str)
                {
                    continue;
                }

                if ( strcmp(str, "password") == 0)
                {
                    str = config_str();
                    if(!str)
                    {
                        continue;
                    }
                    if ( strcmp(str, "required") == 0 )
                    {
                        str = config_str();
                        if(!str)
                        {
                            continue;
                        }
                        if ( strcmp(str, "pam_smb_passwd.so.1") == 0 )
                        {
                            memset(temp_line, 0, sizeof(temp_line));
                            char* line = config_line();
                            if(line != NULL)
                            {
                                sprintf(temp_line, "%s", line);
                            }
                            else
                            {
                                sprintf(temp_line, "\n");
                            }

                            fputs(temp_line, fpTemp);

                            config_pam_smb = 1;
                        }
                    }
                }

                if(config_pam_smb == 0)
                {
                    memset(temp_line, 0, sizeof(temp_line));
                    char* line = config_line();
                    if(line != NULL)
                    {
                        sprintf(temp_line, "%s", line);
                    }
                    else
                    {
                        sprintf(temp_line, "\n");
                    }
                    fputs(temp_line, fpTemp);
                }
            }

            //other
            else
            {
                memset(temp_line, 0, sizeof(temp_line));
                char* line = config_line();
                if(line != NULL)
                {
                    sprintf(temp_line, "%s", line);
                }
                else
                {
                    sprintf(temp_line, "\n");
                }
                fputs(temp_line, fpTemp);
            }
        }
    }

    if(config_pam_smb == 0)
    {
        memset(temp_line, 0, sizeof(temp_line));
        strcat(temp_line, "\nother    password    required    pam_smb_passwd.so.1    nowarn\n");
        fputs(temp_line, fpTemp);
    }


    fclose(fpTemp);
    nfiles = config_close();

    rename(temp_file, config_file);
    return success;
}


//add cifs share
int nas_add_cifs_share(char filePath[], char shareName[], char description[])
{
    int success = 0;
    int i = 0;
    char share_name[256] = {0};
    char share_description[1024] = {0};

    cifs_log_init("/var/log/NAS_Cifs.log");

    //----------------------------------------

    if(filePath == NULL || strlen(filePath) == 0)
    {
        cifs_log_it(NAS_ERROR, "Invalid input paramter, filePath is null.");
        cifs_log_close();
        return 1;
    }

    char folderPath[256] = {0};
    convert_special_character(filePath, folderPath);

    memset(share_name, 0, sizeof(share_name));
    if(shareName == NULL || strlen(shareName) == 0)
    {
        for(i = 0; i < strlen(folderPath); i++)
        {
            if(folderPath[i] == '/')
            {
                share_name[i] = '_';
            }
            else
            {
                share_name[i] = folderPath[i];
            }
        }
    }
    else
    {
        strcpy(share_name, shareName);
    }

    memset(share_description, 0, sizeof(share_description));
    if(description == NULL)
    {
        strcpy(share_description, "    ");
    }
    else
    {
        strcpy(share_description, description);
    }

    char cmdline[1024] = {0};

    //----------------------------------------

    memset(cmdline, 0, sizeof(cmdline));
    char* group_name = "cifs_group";
    sprintf(cmdline, "sharemgr create -P smb %s", group_name);

    cifs_log_it(NAS_IMPORTANT, "cmdline: %s", cmdline);
    system(cmdline);

    //----------------------------------------

    memset(cmdline, 0, sizeof(cmdline));
    sprintf(cmdline, "sharemgr add-share -r %s -d \"%s\" -s \"%s\" %s", share_name, share_description, folderPath, group_name);

    int argc = Cifs_getArgc(cmdline);
    char** argv = Cifs_parseCmdLine(cmdline);
    if(argv == NULL)
    {
        cifs_log_it(NAS_ERROR, "failed to parse command line, <%s>.", cmdline);
        cifs_log_close();
        return 1;
    }

    cifs_log_it(NAS_IMPORTANT, "cmdline: %s", cmdline);
    
	success = system(cmdline);
	
	/*if(strstr(folderPath, "\\$") != NULL)
    {
        success = system(cmdline);
    }
    else
    {
        success = call_sharemgr_cmd(argc, argv);
    }*/

    //clear
    for(i = 0; i < argc; i++)
    {
        free(argv[i]);
        argv[i] = NULL;
    }
    free(argv);

/*
    sprintf(cmdline, "chmod 777 %s", filePath);
    system(cmdline);
*/

    cifs_log_it(NAS_IMPORTANT, "nas_add_cifs_share, return: %d", success);
    cifs_log_close();

    return success;
}


//edit cifs share
int nas_edit_cifs_share(char filePath[], char shareName[], char newShareName[], char description[])
{
    int success = 0;
    int i = 0;
    char new_share_name[256] = {0};
    char share_description[1024] = {0};

    cifs_log_init("/var/log/NAS_Cifs.log");

    //----------------------------------------

    if(filePath == NULL || strlen(filePath) == 0)
    {
        cifs_log_it(NAS_ERROR, "Invalid input paramter, filePath is null.");
        cifs_log_close();
        return 1;
    }

    char folderPath[256] = {0};
    convert_special_character(filePath, folderPath);

    if(shareName == NULL || strlen(shareName) == 0)
    {
        cifs_log_it(NAS_ERROR, "Invalid input paramter, shareName is null.");
        cifs_log_close();
        return 2;
    }

    memset(new_share_name, 0, sizeof(new_share_name));
    if(newShareName == NULL || strlen(newShareName) == 0)
    {
        for(i = 0; i < strlen(filePath); i++)
        {
            if(filePath[i] == '/')
            {
                new_share_name[i] = '_';
            }
            else
            {
                new_share_name[i] = filePath[i];
            }
        }
    }
    else
    {
        strcpy(new_share_name, newShareName);
    }

    memset(share_description, 0, sizeof(share_description));
    if(description == NULL)
    {
        strcpy(share_description, "    ");
    }
    else
    {
        strcpy(share_description, description);
    }

    //----------------------------------------

    char cmdline[1024] = {0};
    char* group_name = "cifs_group";

    memset(cmdline, 0, sizeof(cmdline));
    if(strcmp(shareName, new_share_name) == 0)
    {
        sprintf(cmdline, "sharemgr set-share -r %s -d \"%s\" -s \"%s\" %s", shareName, share_description, folderPath, group_name);
    }
    else
    {
        sprintf(cmdline, "sharemgr set-share -r %s=%s -d \"%s\" -s \"%s\" %s", shareName, new_share_name, share_description, folderPath, group_name);
    }

    int argc = Cifs_getArgc(cmdline);
    char** argv = Cifs_parseCmdLine(cmdline);
    if(argv == NULL)
    {
        cifs_log_it(NAS_ERROR, "failed to parse command line, <%s>.", cmdline);
        cifs_log_close();
        return 1;
    }

    cifs_log_it(NAS_IMPORTANT, "cmdline: %s", cmdline);
    if(strstr(folderPath, "\\$") != NULL)
    {
        success = system(cmdline);
    }
    else
    {
        success = call_sharemgr_cmd(argc, argv);
    }

    //clear
    for(i = 0; i < argc; i++)
    {
        free(argv[i]);
        argv[i] = NULL;
    }
    free(argv);

    //----------------------------------------
    cifs_log_it(NAS_IMPORTANT, "nas_edit_cifs_share, return: %d", success);
    cifs_log_close();

    return success;
}

//remove cifs share
int nas_remove_cifs_share(char filePath[])
{
    int success = 0;

    cifs_log_init("/var/log/NAS_Cifs.log");

    //----------------------------------------

    if(filePath == NULL || strlen(filePath) == 0)
    {
        cifs_log_it(NAS_ERROR, "Invalid input paramter, filePath is null.");
        cifs_log_close();
        return 1;
    }

    char folderPath[256] = {0};
    convert_special_character(filePath, folderPath);

    //----------------------------------------

    char cmdline[1024] = {0};
    char* group_name = "cifs_group";

    memset(cmdline, 0, sizeof(cmdline));
    sprintf(cmdline, "sharemgr remove-share -s \"%s\" %s", folderPath, group_name);

    cifs_log_it(NAS_IMPORTANT, "cmdline: %s", cmdline);
    success = system(cmdline);

    //----------------------------------------
    cifs_log_it(NAS_IMPORTANT, "nas_remove_cifs_share, return: %d", success);
    cifs_log_close();

    return success;
}

//judge file shared cifs or not
int nas_get_cifs_share_name(char filePath[], char share_name[])
{
    int success = 0;
    int matched = 0;

    cifs_log_init("/var/log/NAS_Cifs.log");

    //----------------------------------------

    cifs_log_it(NAS_INFO, "filePath: %s", filePath);
    if(filePath == NULL || strlen(filePath) == 0)
    {
        cifs_log_it(NAS_ERROR, "Invalid input paramter, filePath is null.");
        cifs_log_close();
        return 1; //no shared!!
    }

    //----------------------------------------

    int arraySize = 0;
    success = nas_get_share_list(NULL, &arraySize);
    if(success != 0 || arraySize == 0)
    {
        cifs_log_it(NAS_ERROR, "failed to get all cifs share.");
        cifs_log_close();
        return 2; //no shared!!
    }

    struct CifsShareObject shareArray[arraySize];
    success = nas_get_share_list(shareArray, &arraySize);
    if(success != 0 || arraySize == 0)
    {
        cifs_log_it(NAS_ERROR, "failed to get all cifs share.");
        cifs_log_close();
        return 3; //no shared!!
    }

    //----------------------------------------

    int i = 0;
    for(i = 0; i < arraySize; i++)
    {
        if(strcmp(shareArray[i].folder_path, filePath) == 0)
        {
            matched = 1;
            strcpy(share_name, shareArray[i].share_name);
            break;
        }
    }

    if(matched == 1)
    {
        success = 0;
    }
    else
    {
        success = 4;
    }

    cifs_log_it(NAS_IMPORTANT, "nas_get_cifs_share_name, to return: %d", matched);
    cifs_log_close();
    return success;
}

//
//register netbios name
//
void nas_register_netbios_name()
{
    char cmdline[1024] = {0};
    int ret = 0;

    cifs_log_it(NAS_IMPORTANT,"nas_register_netbios_name ...");

    struct DomainGroupObject domainGroupObject;
    ret = nas_cifs_get_domain_group_mode(&domainGroupObject);
    if(ret != 0 || domainGroupObject.mode_name == NULL)
    {
        return;
    }
    
    char workgroup[256] = {0};
    strcpy(workgroup, domainGroupObject.mode_name);

    if(domainGroupObject.cifs_mode == 1)
    {
        sprintf(cmdline, "smbadm list|grep \"Domain:\"|cut -d \" \" -f2 > temp_domain.txt");
        system(cmdline);
        FILE* fp = fopen("temp_domain.txt", "r");
        if(fp != NULL)
        {
            char temp[256];
            fscanf(fp, "%s", temp);
            fclose(fp);

            if(temp != NULL)
            {
                cifs_log_it(NAS_IMPORTANT,temp);
                strcpy(workgroup, temp);
            }
        }
        remove("temp_domain.txt");
    }
    cifs_log_it(NAS_IMPORTANT,"workgroup: %s", workgroup);
    //----------------------------------------
    //clear old smb config

    for(;;)
    {
        ret = system("pgrep nmbd");
        if(ret != 0)
        {
            break;
        }
        else
        {
            system("pkill nmbd");
        }
    }

    system("rm -rf /etc/sfw/smb.conf");

    //----------------------------------------
    //create a new smb config

    sprintf(cmdline, "echo [global] >> /etc/sfw/smb.conf");
    system(cmdline);

    sprintf(cmdline, "echo workgroup = %s >> /etc/sfw/smb.conf", workgroup);
    system(cmdline);

    sprintf(cmdline, "echo netbios name = `hostname` >> /etc/sfw/smb.conf");
    system(cmdline);

    //call nmbd
    system("nmbd -D");

    //refresh cifs service
    system("svcadm refresh smb/server");
}


//re-join workgroup
int nas_rejoin_workgroup(char workgroup_name[])
{
    int success = 0;
    int i = 0;

    cifs_log_init("/var/log/NAS_Cifs.log");

    success = check_cifs_service_status();
    if(success != 0)
    {
        cifs_log_it(NAS_IMPORTANT, "cifs service status is not OK.");
        cifs_log_close();
        return 1;
    }

    //check domain administrator user
    if(workgroup_name == NULL || strlen(workgroup_name) == 0)
    {
        cifs_log_it(NAS_IMPORTANT, "workgroup_name is null.");
        cifs_log_close();
        return 2;
    }

    //join workgroup
    char cmdline[1024] = {0};
    int argc = 0;
    char** argv = NULL;

    sprintf(cmdline, "smbadm join -w %s", workgroup_name);
    argc = Cifs_getArgc(cmdline);
    argv = Cifs_parseCmdLine(cmdline);
    success = call_smbadm_cmd(argc, argv);
    if(success != 0)
    {
        cifs_log_it(NAS_ERROR, "failed to call cmdline: %s", cmdline);
        success = 5;
    }
    else
    {
        domain_mode = 0; //not domain mode
    }

    //clear
    for(i = 0; i < argc; i++)
    {
        free(argv[i]);
        argv[i] = NULL;
    }
    free(argv);

    cifs_log_it(NAS_IMPORTANT, "rejoin workgroup, return: %d", success);
    cifs_log_close();

    return success;
}

//re-join domain
int nas_rejoin_domain(char domainName[], char domainAdministrator[], char domainAdministratorPasswd[])
{
     int success = 0;
    int i = 0;

    cifs_log_init("/var/log/NAS_Cifs.log");

    success = check_cifs_service_status();
    if(success != 0)
    {
        cifs_log_it(NAS_IMPORTANT, "cifs service status is not OK.");
        cifs_log_close();
        return 1;
    }

    strcpy(domain_name, domainName);

    //check domain administrator user
    if(domainAdministrator == NULL || strlen(domainAdministrator) == 0)
    {
        cifs_log_it(NAS_IMPORTANT, "domain adminsitrator is null.");
        cifs_log_close();
        return 2;
    }
    else
    {
        strcpy(domain_administrator, domainAdministrator);
    }


    //check domain administrator password
    if(domainAdministratorPasswd == NULL || strlen(domainAdministratorPasswd) == 0)
    {
        strcpy(domain_administrator_passwd, "");
    }
    else
    {
        strcpy(domain_administrator_passwd, domainAdministratorPasswd);
    }

    //sync system clock
    success = nas_sync_system_clock();


    //join domain
    char cmdline[1024] = {0};

    int argc = 0;
    char** argv = NULL;

    sprintf(cmdline, "smbadm join -u %s %s", domain_administrator, domain_name);
    argc = Cifs_getArgc(cmdline);
    argv = Cifs_parseCmdLine(cmdline);
    cifs_log_it(NAS_ERROR, "nas_join_domain...:%s", cmdline);
    success = call_smbadm_cmd(argc, argv);
    if(success != 0)
    {
        cifs_log_it(NAS_ERROR, "failed to call cmdline: %s", cmdline);
        success = 6;
    }
    else
    {
        domain_mode = 1; //domain mode
    }

    //clear
    for(i = 0; i < argc; i++)
    {
        free(argv[i]);
        argv[i] = NULL;
    }
    free(argv);

    //----------------------------------

    cifs_log_it(NAS_IMPORTANT, "rejoin domain, return: %d", success);
    cifs_log_close();

    return success;
}

 void cifs_get_last_message(char message[])
 {
     if(cifs_last_message != NULL)
     {
        strcpy(message, cifs_last_message);
     }
 }
