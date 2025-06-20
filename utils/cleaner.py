# utils/cleaner.py
import os
import time
from threading import Thread

def delete_file_later(filename, delay):
    def delete_task():
        time.sleep(delay)
        if os.path.exists(filename):
            os.remove(filename)
            print(f"✅ {filename} deleted after {delay} seconds")
    Thread(target=delete_task).start()
