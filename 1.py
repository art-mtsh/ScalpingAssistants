from datetime import datetime
import time

while not int(datetime.now().strftime('%S')) == 59 and not int(datetime.now().strftime('%S')) == 29:
    time.sleep(1)
    print(datetime.now().strftime('%S'))