from pprint import pprint
from netmiko import ConnectHandler
import json
from time import time
import MySQLdb
import getpass
import textfsm
import threading
import pandas as pd
from multiprocessing.dummy import Pool as ThreadPool

tuser = raw_input("Enter TACACS Username: ")
tpass = getpass.getpass("Enter TACACS Password: ")
muser = raw_input("Enter MySQL Username: ")
mpass = getpass.getpass("Enter MySQL Password: ")


#------------------------------------------------------------
def get_db():
    '''
    MySQL connection
    '''

    db = MySQLdb.connect(host="localhost",
                         user=muser,
                         passwd=mpass,
                         db=muser
                         )

    return db


#-----------------------------------------------------------
def devices_list():
    '''
    Pull list of IPs from MySQL to pass onto netmiko connections
    '''

    cursor = db.cursor()
    cursor.execute("SELECT ip FROM "TABLE NAME" "COLUMN NAME" LIKE 'VAR' AND  "COLUMN NAME" LIKE '%VAR%' limit 20") #CHANGE "" To your values
    items = cursor.fetchall()
    devices = [x[0] for x in items] #convert tuple to list
    #print (devices)

    return devices

#------------------------------------------------------------
def get_xr_info(ip):
    '''
     Netmiko gather info using NTC Templates for output
    '''

    with open('/home/"user directory"/ntc-templates/templates/cisco_xr_show_interfaces.template', 'r') as f1:
        template = textfsm.TextFSM(f1)
        session = ConnectHandler(device_type="cisco_xr", ip=ip, username=tuser, password=tpass)
        pprint("Connecting to "+ip)

        set_term = session.send_command("terminal length 0")
        int_info = session.send_command('show interfaces', use_textfsm=True)

        #insert ip of device into each dictionary {'ip'=str(ip)}
        int_data = [dict(item, **{'ip':str(ip)}) for item in int_info]
        return int_data


#-------------------------------------------------------------
def conv_csv():
    '''
    Convert JSON to CSV
    '''
    df=pd.read_json("temp_int_info.json")
    df.to_csv("results_int_info.csv")
#-------------------------------------------------------------
def insert_data():
# will use this function at a later date
    pass

#--------------------------------------------------------------
def parallel_sessions(threads=2):
    '''
    Create Threads passing to get_xr_info()
    '''
    ip = devcies
    pool = ThreadPool(threads)
    results = pool.map(get_xr_info, ip)
    pool.close()
    pool.join()
    return results





if __name__ == '__main__':
    db = get_db()
    devices = devices_list()
    results = parallel_sessions() #Enter number of threads. Default is 2
    with open ("temp_int_info.json", "w") as file1:
        json.dump(results,file1)
    file1.close
    conv_csv()
    #print json.dumps(results, indent=4)

  
