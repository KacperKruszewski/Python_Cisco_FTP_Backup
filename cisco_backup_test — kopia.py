#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import threading
import paramiko
import atexit
import sys
from queue import Queue

# Stała z adresem serwera FTP
FTP_SERVER_IP = '10.10.10.10'

# Liczba wątków obsługujących kopie zapasowe
NUM_THREADS = 4  # Ustaw liczbę wątków na wartość 4 (możesz dostosować)

my_file = open("ipler.txt",)
ip_queue = Queue()

buff = ''
resp = ''

# Lista do przechowywania informacji o niewykonanych kopii
niewykonane_kopie = []

def IPokuyan():
    while True:
        IP = ip_queue.get()
        try:
            print(f"Logowanie do {IP} - rozpoczęcie tworzenia kopii zapasowej...")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(IP, username='test', password='test')  # Zastąp rzeczywistą nazwą użytkownika i hasłem
            chan = ssh.invoke_shell()
            chan.settimeout(20)

            # Wysyłanie poleceń do urządzenia
            ftp_command = f'copy running-config ftp://:{FTP_SERVER_IP}\n'
            chan.send(ftp_command)
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
                print(f"{IP} Kopiowanie OK")

            # Zamykanie połączenia SSH
            chan.send('exit\n')  # Wysyłanie polecenia wyjścia
            ssh.close()
            print(f"Wylogowano z {IP} - zakończenie kopii zapasowej.")
        except paramiko.ssh_exception.SSHException as ssh_error:
            print(f"\nBłąd SSH podczas kopiowania urządzenia {IP}: {str(ssh_error)}")
            niewykonane_kopie.append(IP)  # Dodawanie IP urządzenia do listy niewykonanych kopii
        except Exception as e:
            print(f"\nInny błąd podczas kopiowania urządzenia {IP}: {str(e)}")
            niewykonane_kopie.append(IP)
        finally:
            ip_queue.task_done()

def close_program():
    global program_zamykany
    if not program_zamykany:
        program_zamykany = True
        print("\nZamykanie programu...")
        my_file.close()

        # Sprawdzanie, czy wszystkie oczekiwane kopie zostały zakończone
        if len(niewykonane_kopie) == ip_queue.qsize():
            print("Wszystkie kopie zapasowe zostały pomyślnie wykonane.")
        else:
            print("\nUwaga: Nie wszystkie kopie zapasowe zostały zakończone pomyślnie!")
            print("Niewykonane kopie zapasowe dla urządzeń:")
            for device in niewykonane_kopie:
                print(device)

        while True:
            answer = input("\nProgram można zakończyć poprzez naciśnięcie Ctrl+C.").strip().lower()

if __name__ == "__main__":
    program_zamykany = False

    for i in range(NUM_THREADS):
        t = threading.Thread(target=IPokuyan)
        t.daemon = True
        t.start()

    for line in my_file:
        l = [i.strip() for i in line.split()]
        IP = l[0]
        ip_queue.put(IP)

    atexit.register(close_program)

    ip_queue.join()
    time.sleep(1)
