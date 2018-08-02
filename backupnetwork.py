#!/usr/bin/python3
 
import sys
import os
import paramiko
import time
import getpass
import subprocess
import re
from time import localtime, strftime
from ciscoconfparse import CiscoConfParse

timeValue1 = time.time()
 
def parsing_file(READFILE, device_name):
    parse = CiscoConfParse(READFILE)
    Gig_objs = parse.find_objects("^interface Gi")
    if len(Gig_objs) <= 15:
        print (device_name + ' has interfaces:')
        for interface in Gig_objs:
            print(interface.text)
    else:
        print (device_name + ": Has " + str(len(Gig_objs)) + " interfaces")

def create_output_doc(INFO_DISPLAY, device_name, ending):
    FileName = str(device_name) + strftime("_%b_%d_%Y_%H" + ending, localtime())
    APPEND = open(FileName, 'a')
    APPEND.write(INFO_DISPLAY)
    APPEND.close()
    return FileName
 
def relocate_old_backup_files(directory):
    # Does old_folder exist in current directory...if not create folder
    # os.getcwd() provides current dir and os.path.join combines dir with name of folder
    #if not os.path.exists(os.path.join(os.getcwd(), "old_folder/")):
    #    os.mkdir("old_folder")
    for my_file in directory:
        if my_file.endswith("_BACKUP"):
            os.rename(my_file, local_dir_path + "/old_folder/" + my_file)

def make_old_backup_folder(directory):
    if not os.path.exists(os.path.join(os.getcwd(), "old_folder/")):
        os.mkdir("old_folder")
 

 
def delete_redundant_files(SortedList):
    try:
        for DeviceName in devices_dic.values():
            count_list = ([filename for filename in 
                          SortedList if DeviceName in filename])
            #print(count_list)
            if len(count_list) > 1 and any(files.endswith('_VERSION') for
                    files in count_list):
                for files in count_list[:]:
                  #  print(files)
                    os.remove(os.path.join(os.getcwd(), files))
            elif len(count_list) > 2:
                for files in count_list[:-2]:
                    os.remove(os.path.join(os.getcwd() + '/old_folder/', files))
            count_list.clear()  
    except Exception as e:
        print("**ERROR DELETING FILES**")
        print(str(e))
 
def establish_ssh(connection_ip, username, password):
    conn.connect(connection_ip, username=username, password=password,
                 look_for_keys=False, allow_agent=False, timeout=2)

def vty_login_first_steps(device_name):
    shell.send("enable\n")
    shell.send("cisco\n")
    time.sleep(0.5)
    if "ASA" in device_name:
        shell.send("terminal pager 0\n")
    else:
        shell.send("terminal length 0\n")

def check_ssh(self, ip, user, key_file, initial_wait=0, interval=0, retries=2):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) 
    sleep(initial_wait) 
    for x in range(retries):
        try:
            ssh.connect(ip, username=username, password=password) 
            return True 
        except Exception as e: 
            print(e) 
            sleep(interval) 
    return False


 
password = "cisco"
username = "cisco"
 
conn = paramiko.SSHClient()
#conn.load_system_host_keys()
conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
 
file_dir = os.listdir(os.path.expanduser('~/'))

local_dir_path = os.getcwd()
file_dir = os.listdir(local_dir_path)
make_old_backup_folder(file_dir)
relocate_old_backup_files(file_dir)
backup_dir = os.listdir(local_dir_path + '/old_folder/')
sorted_list_version = sorted(([z for z in file_dir if "VERSION" in z]))
sorted_list_backup = sorted(([z for z in backup_dir if "BACKUP" in z]))
devices_dic = {}


#with open(os.getcwd() + "/router_dic.txt") as f:
with open(os.path.expanduser('~') + "/router_dic.txt") as f: 
   for line in f:
       x,y = line.rstrip().split()
       devices_dic.update({x : y})
print(devices_dic)
routerlen = len(devices_dic)
print(routerlen)

for connection_ip,device_name in sorted(devices_dic.items()):
    print(device_name)
    response = os.system("ping -n 1 -w 1 " + connection_ip)
    try:
        if response == 0 and "ASA" not in device_name:
            establish_ssh(connection_ip, username, password)
            print(device_name, 'show run')
            stdin, stdout, stderr = conn.exec_command('show run all')
            INFO_DISPLAY = stdout.read().decode()
            FileName = create_output_doc(INFO_DISPLAY, device_name, '_BACKUP')
            conn.close()
       #     establish_ssh(connection_ip, username, password)
       #     shell = conn.invoke_shell()
        #    vty_login_first_steps(device_name)
        #    shell.send("show clock\n")
        #    print(device_name, 'show clock')
        #    shell.send("show version\n")
        #    print(device_name, 'show version')
        #    time.sleep(0.7)
         #   INFO_DISPLAY = shell.recv(100000).decode()
        #    ExcludeBeginning = INFO_DISPLAY.find('terminal length 0')
        #    INFO_DISPLAY = INFO_DISPLAY[(ExcludeBeginning + 17):]

      #      FileName = create_output_doc(INFO_DISPLAY, device_name, '_VERSION')
        #    conn.close()
            print("\n")
            print("---------------------------------------")

        elif response == 0 and "ASA" in device_name:
            establish_ssh(connection_ip, username, password)
            shell = conn.invoke_shell()
            vty_login_first_steps(device_name)
            shell.send("terminal pager 0\n")
            shell.send("show run\n")
            print(device_name, 'show run all')
            time.sleep(2)
            INFO_DISPLAY = shell.recv(100000).decode()
            run_config_location = INFO_DISPLAY.find('ASA Version')
            run_config_end = INFO_DISPLAY.rfind('end')
            INFO_DISPLAY = INFO_DISPLAY[run_config_location:run_config_end]
            create_output_doc(INFO_DISPLAY, device_name, '_BACKUP')
            print("\n")
            print("---------------------------------------")
        else:
            print ('\n\n*********' + device_name + ' is DOWN!**********\n\n')
            f = open('Offline.txt', 'a')
            f.write('Host ' + device_name + ' was down at ' + strftime("%a_%d_%b_%Y_%H", localtime()) + '\n')
            f.close()
    except paramiko.ssh_exception.AuthenticationException:
        print("\n\n**********AUTHENTICATION ERROR*************\n\n")
    except paramiko.ssh_exception.NoValidConnectionsError:
        print('\n\n**********DEVICE REFUSED CONNECTION [CHECK ACL]***********\n\n')
    except Exception as e:
        raise LookupError
#print(sorted_list_version)
delete_redundant_files(sorted_list_version)
delete_redundant_files(sorted_list_backup)
 
timeValue2 = time.time()
total = float(timeValue2) - float(timeValue1)
print(total)
 

 




