import time

def log_write(logbuf):
    with open("/log/edge.log", 'a') as f:
        tm=time.localtime()
        log_tm = f"{tm[0:6]}"
        log_data = log_tm + logbuf
        f.write(log_data)
