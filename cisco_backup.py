#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import threading
import paramiko
import atexit
import sys
from queue import Queue

my_file = open("ipler.txt", "rb")
ip_queue = Queue()

buff = ''
resp = ''


def IPokuyan():
    while True:
        IP = ip_queue.get()
        print(f"Zalogowano do {IP} - rozpoczęcie kopii zapasowej...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(IP, username='', password='')  # Replace with actual username and password
        chan = ssh.invoke_shell()
        chan.settimeout(20)

        # Sending commands
        chan.send('copy running-config ftp://ftpusername:ftppassword@ftpserveripaddress\n')
        time.sleep(1)
        chan.send('\r\n')
        time.sleep(1)
        chan.send('\r\n')
        time.sleep(1)
        buff = ''
        while buff.find(b'copied') < 0:
            resp = chan.recv(9999)
            buff += resp
            print(resp.decode('utf-8'))
            print(f"{IP} Backup OK")

        # Closing SSH connection
        chan.send('exit\n')  # Sending exit command
        ssh.close()
        print(f"Wylogowano z {IP} - zakończenie kopii zapasowej.")
        ip_queue.task_done()


def close_program():
    print("Zamykanie programu...")
    my_file.close()
    sys.exit(0)


if __name__ == "__main__":
    for i in range(2):
        t = threading.Thread(target=IPokuyan)
        t.daemon = True
        t.start()

    for line in my_file:
        l = [i.strip() for i in line.split()]
        IP = l[0].decode('utf-8')
        ip_queue.put(IP)

    atexit.register(close_program)  # Rejestrowanie funkcji do wywołania przy zamykaniu programu

    ip_queue.join()
    time.sleep(1)
