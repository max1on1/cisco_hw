import datetime
import os
import yaml
import re
from netmiko import ConnectHandler

DEVICE_FILE_PATH = 'hosts.yml' 
BACKUP_DIR_PATH = 'backups' 

def get_device_from_yaml(device_file):
    with open(device_file) as file:
        hosts = yaml.load(file, Loader=yaml.FullLoader)
    
    
    print('Device imoprt successful')
    print('-='*15)
    return hosts

def get_time():
    timestamp = datetime.datetime.now()
    print(timestamp.strftime("%Y_%m_%d-%H_%M_%S"))
    return timestamp

def connect_to_device(device):
    connection = ConnectHandler(
        host = device['ip'],
        username = device['username'],
        password=device['password'],
        device_type=device['device_type'],
        port=device['port']
    )
    print ('Opened connection to '+device['ip'])
    print('-*-' * 10)
    print()
    return connection

def disconnect_from_device(connection, hostname):

    connection.disconnect()
    print ('Connection to device {} terminated'.format(hostname))


def get_backup_file_path(hostname,timestamp):

    if not os.path.exists(os.path.join(BACKUP_DIR_PATH, hostname)):
        os.mkdir(os.path.join(BACKUP_DIR_PATH, hostname))


    backup_file_path = os.path.join(BACKUP_DIR_PATH, hostname, '{}-{}.txt'.format(hostname, timestamp))
    print('Backup file path will be '+backup_file_path)
    print('-=' * 10)
    print()

    return backup_file_path


def get_backup(connection, backup_file_path, hostname):
    try:
        connection.enable()
        output = connection.send_command('sh run')

        with open(backup_file_path, 'w') as file:
            file.write(output)
        print("Backup of" + hostname + "was done!")
        print('-='*10)

        return True

    except Error:
        print('Something went wrong!')
        return False

def check_cdp(connection,hostname):
    connection.enable()
    output = connection.send_command('sh cdp nei')
    if '% CDP is not enabled' in output:
        print('CDP is not enable')
        cdp_stat = 'OFF'
        return cdp_stat
    else:
        print('CDP is enabled')
        neighbor_count = re.search(r'Total cdp entries displayed : \d+',output)
        find = neighbor_count.group(0)
        find = find.split(':')
        count = find[1]
        return count


def check_software(connection,hostname):

    connection.enable()
    output = connection.send_command('sh version')
    if 'npe' in output:
        software_version = 'NPE'
    else:
        software_version = 'NE'
    return software_version


def set_ntp(connection,hostname,ntp_server):
    connection.enable()
    output = connection.send_command('ping '+ntp_server)
    if '!' in output:
        ntp = 'ntp server '+ntp_server
        print(ntp)
        connection.send_config_set('timezone GMT 0',ntp)
        connection.send_config_set(ntp)
        ntp_stat = connection.send_command('sh ntp ass')
        if 'Clock is synchronized' in ntp_stat:
                clock_stat = 'sync'
        else:
                clock_stat = 'unsync'
                
    else: 
        print('Server dont ask for ping')

    return clock_stat

def show_platform(connection):
    connection.enable()
    output = connection.send_command('sh version')

    find_platform = re.search(r'Cisco IOS XE Software, Version \S+', output)
    find = find_platform.group(0)
    find = find.split('Version')
    platform = find[1]
    return platform

hosts = get_device_from_yaml(DEVICE_FILE_PATH)
time=get_time()
ntp_server='10.10.20.200'

for host in hosts:
    connection = connect_to_device(host)
    backup_path = get_backup_file_path( host['hostname'], time)
    get_backup(connection,backup_path,host['hostname'])
    cdp_stat = check_cdp(connection, host['hostname'])
    clock_stat =set_ntp(connection, host['hostname'],ntp_server )
    software_version = check_software(connection,host['hostname'])
    platform = show_platform(connection)
    print('================')
    print('Hostname:'+host['hostname'],'|','NTP is '+clock_stat,'|', 'CDP is: '+cdp_stat, '|','Software ver: '+software_version,'|','IOS Version: '+platform)
