#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import threading
import paramiko
import atexit
import sys
from queue import Queue

tftp_server = 'your_tftp_server'
site = 'your_site'

ssh_user = 'username'
ssh_password = 'password'

# Liczba wątków obsługujących kopie zapasowe
NUM_THREADS = 10  # Ustaw liczbę wątków na wartość 4 (możesz dostosować)

my_file = open("ip_device.txt")
ip_queue = Queue()

buff = ''
resp = ''

print(f"Lączenie do przełączników w lokalizacji {site}: Kopia TFTP\n")

# Lista do przechowywania informacji o zakończonych kopii
niewykonane_kopie = []

def IPokuyan():
    while True:
        IP = ip_queue.get()
        try:
            print(f"Logowanie do {IP} - rozpoczęcie tworzenia kopii zapasowej...")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(IP, username=f'{ssh_user}', password=f'{ssh_password}')  # Zastąp rzeczywistą nazwą użytkownika i hasłem
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            chan = ssh.invoke_shell()
            chan.settimeout(15)

            # Wysyłanie poleceń do urządzenia
            chan.send('show clock\n')
            time.sleep(1)
            
            tftp_command = f'copy running-config ftp://:{tftp_server}\n'
            chan.send(tftp_command)
            
            time.sleep(1)
            chan.send('\r\n')
            time.sleep(1)
            chan.send('\r\n')
            time.sleep(1)
            buff = ''
            
            while buff.find('copied') < 0:
                resp = chan.recv(9999).decode('utf-8')
                buff += resp
                print(f"\nKopiowanie zakończone {IP}")

            # Zamykanie połączenia SSH
            chan.send('exit\n')  # Wysyłanie polecenia wyjścia
            ssh.close()
            print(f"\nWylogowano z {IP}")
            
        except paramiko.ssh_exception.SSHException as ssh_error:
            print(f"\nBłąd SSH podczas kopiowania urządzenia {IP}: {str(ssh_error)}")
            niewykonane_kopie.append(IP) # Dodawanie IP urządzenia do listy niewykonanych kopii

        except Exception as e:
            print(f"Błąd podczas kopiowania urządzenia {IP}: {str(e)}")
            niewykonane_kopie.append(IP)
            
        finally:
            ip_queue.task_done()

def close_program():
    global program_zamykany
    if not program_zamykany:
        program_zamykany = True
        print("Zamykanie programu...")
        my_file.close()

        # Sprawdzanie, czy wszystkie oczekiwane kopie zostały zakończone
        if len(niewykonane_kopie) == ip_queue.qsize():
            print("Wszystkie kopie zapasowe zostały pomyślnie wykonane.")
        else:
            print("\nUwaga: Nie wszystkie kopie zapasowe zostały zakończone pomyślnie!")
            print("Niewykonane kopue zapasowe dla urządzeń: ")
            for device in niewykonane_kopie:
                print(device)
                
        while True:
            answer = input("\nProgram można zakończyć poprzez naciśnięcie Ctrl+C").strip().lower()
            
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

    atexit.register(close_program)  # Rejestrowanie funkcji do wywołania przy zamykaniu programu

    ip_queue.join()
    time.sleep(1)