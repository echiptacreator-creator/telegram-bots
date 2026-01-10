import threading
import subprocess
import time

def run_avtobot():
    subprocess.Popen(["python", "avtobot.py"])

def run_admin_bot():
    subprocess.Popen(["python", "admin_bot.py"])

def run_login_server():
    subprocess.Popen(["python", "login_server.py"])

threading.Thread(target=run_avtobot).start()
threading.Thread(target=run_admin_bot).start()
threading.Thread(target=run_login_server).start()

while True:
    time.sleep(3600)
