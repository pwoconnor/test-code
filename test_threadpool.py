"""

1. This will log into all IP addresses gathered in devices_list() func.
2. Each device that has been logged into will have a file created in JSON
3. Each of JSON files will be converted to CSV format
4. Each CSV file will be inserted into MySQL minuse the header row

Currently this script is set to run with 75 threads. This can be changed
in the parallel_sessions() func


"""


from pprint import pprint
import paramiko
from netmiko import ConnectHandler
import json
from time import time
import MySQLdb
import getpass
import textfsm
import threading
import pandas as pd
import csv
import os
from os import listdir
from os.path import isfile,join
from itertools import chain
from multiprocessing.dummy import Pool as ThreadPool

tuser = raw_input("Enter TACACS Username: ")
tpass = getpass.getpass("Enter TACACS Password: ")
muser = raw_input("Enter MySQL Username: ")
mpass = getpass.getpass("Enter MySQL Password: ")
#Creating log file for ssh connections for troubleshooting
#paramiko.util.log_to_file("parmiko.log")


#------------------------------------------------------------
def get_db():
    '''
    MySQL connection
    '''
    # assgin var for MySQL database connection
    db = MySQLdb.connect(host="localhost",
                         user=muser,
                         passwd=mpass,
                         db=muser #my muser is the same name as my database
                         )

    return db


#-----------------------------------------------------------
def devices_list():
    '''
    Pull list of IPs from MySQL to pass onto netmiko connections
    '''

    cursor = db.cursor()
    # MySQL query to return list of IPs. This function could be replaced with a txt file, etc.
    cursor.execute("SELECT IP FROM RC_MDL WHERE netype LIKE 'MKT Router' AND  model_name LIKE '%ASR%'")
    items = cursor.fetchall()
    devices = [x[0] for x in items] #convert tuple to list
    #print (devices)

    return devices

#------------------------------------------------------------
def get_xr_info(ip):
    '''
     Netmiko gather info using NTC Templates for output
    '''
    #Make sure to change this directory to the path of your NTC templates
    with open('your directory path', 'r') as f1:
        template = textfsm.TextFSM(f1)
        try:
            session = ConnectHandler(device_type="cisco_xr",
                                        ip=ip,
                                        username=tuser,
                                        password=tpass,
                                        global_delay_factor=2,
                                        verbose=False
                                        )
            pprint("Connecting to "+ip)

            set_term = session.send_command("terminal length 0")
            int_info = session.send_command('show interfaces', use_textfsm=True)

            #insert ip of device into each dictionary in the list {'ip'=str(ip)}
            int_data = [dict(item, **{'ip':str(ip)}) for item in int_info]
            #Another way of adding a feild to output
            # int_data = [dict(item, ip=str(ip)) for item in int_info]
        except Exception as error:
            print ("Get_ERROR - " +str(error) + "" + str(ip))
            # Errors occured where int_data was not empty for next entry
            int_data = []
            #change file path to your directory
            with open ("your directory path", "a") as efile:
                efile.write(ip+"\n")
            efile.close()

    #Flatten list of lists
    #data = list(chain.from_iterable(int_data))
    #This will create a file per device in the same folder the script is run from
    with open ("your directory path/temp_int_info_"+(ip)+".json", "w") as file1:
        json.dump(int_data,file1)
    file1.close
#-------------------------------------------------------------
def retry_errors():
    '''
    Retrying devices that were logged in the expection section of get_xr_info
    '''
    print "Retrying errors"

    with open("your directory path with NTC template file", "r") as f1:
        template = textfsm.TextFSM(f1)
        hosts = open("your directory path you want the error file to go"/conn_error.txt", "r").readlines()

        for host in hosts:
            try:
                host = host.rstrip("\n")
                session = ConnectHandler(device_type="cisco_xr",
                                            ip=host,
                                            username=tuser,
                                            password=tpass,
                                            global_delay_factor=2,
                                            verbose=False
                                            )
                pprint("Connecting to "+host)

                set_term = session.send_command("terminal length 0")
                int_info = session.send_command('show interfaces', use_textfsm=True)

                #insert ip of device into each dictionary in the list {'ip'=str(ip)}
                int_data = [dict(item, **{'ip':str(host)}) for item in int_info]
                #Another way of adding a feild to output
                # int_data = [dict(item, ip=str(ip)) for item in int_info]
                # return int_data
            except Exception as error:
                print ("SECOND_ERROR - " +str(error) + "" + str(host))
                int_data = []

    with open ("your directory path"/temp_int_info_"+(host)+".json", "w") as file1:
        json.dump(int_data,file1)
    file1.close


#-------------------------------------------------------------
def conv_csv():
    '''
    Convert JSON to CSV
    '''
    path = ("your directory path")
    #file = [f for f in listdir(path) if f.endswith(".json")]
    print "Converting files to CSV"
    for file in os.listdir(path):
        if file.endswith(".json"):
            out_filename = file.split(".json")[0]
            df=pd.read_json(file)
            df.to_csv("results_"+out_filename+".csv")
    #print (file)

#-------------------------------------------------------------
def insert_data():
    '''
    Insert data from CSV file into MySQL
    '''
    print "Sending data to MySQL"
    cursor = db.cursor()
    try:
        for item in os.listdir("your directory path"):
            if item.endswith(".csv"):

                #this file should be in the same folder this script is executed from
                csv_data = csv.reader(file(item))
                headers =next(csv_data)
                for row in csv_data:
                    #print(row)
                    cursor.execute("""INSERT INTO int_list2(row_num,address, admin_state, bandwidth,
                                             bia, description, duplex, encapsulation, hardware_type,
                                             interface, ip, ip_address, link_status, mtu, speed)
                                              VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",row)
        db.commit()
        cursor.close()
        print "MySQL transfer complete"
    except Exception as e:
        print ("Something went wrong")
        print (e)
        db.rollback()
        db.close()

#--------------------------------------------------------------
def parallel_sessions(threads=75):
    '''
    Create Threads passing to get_xr_info()
    '''

    ip = devices
    pool = ThreadPool(threads)
    results = pool.map(get_xr_info, ip)
    pool.close()
    pool.join()
    return results





if __name__ == '__main__':
    db = get_db()
    devices = devices_list()
    parallel_sessions()
    retry_errors()
    #Flatten list of lists
    # data = list(chain.from_iterable(results))
    # #This will create the file in the same folder the script is run from
    # with open ("temp_int_info.json", "w") as file1:
    #     json.dump(data,file1)
    # file1.close
    conv_csv()
    insert_data()
    #print json.dumps(results, indent=4)
