import os
import sys
import json
import time
import ntptime
import _thread
import logfile
from machine import UART

file = "config.txt"
init_count = 0
BUFFSIZE = 128

#################################################
# config file check                             #
#################################################
def get_config_default(file):
    try:
        with open(file,"r") as fd:
            return json.load(fd)

    except OSError:
        with open(file, "w") as fd:
            config = {
                'ssid': 'eprotech-ap',
                'pw': '',
                'broker' : '192.168.200.1',
                'port' : 1883,
                'edge_id' : 'cb-23-0000',
            }
            json.dump(config, fd)
            return config
        
def uart_response(uart):
    global init_count

#    try:
    while(1):
        if uart.any():
            recv = uart.read()
            print("uart read data = ", recv)          
            buf=json.loads(recv)
            res=buf["RS"]
            print("RS =" , res)
#            if(res != "OK"):
#                return False
#            else:
#                init_count = +1
#                break
#        return True

#    except KeyError as e:
#        print("Response Message error: ", e)
#        return False
#    finally:
#        return False

def config_info_check(config):
    global init_count

    broker=config['broker']
    pw=config['pw']
    port=config['port']
    ssid=config['ssid']
    edge_id=config['edge_id']
    if((len(broker) * len(ssid) * len(edge_id)) == 0):
        print("system config file context error !!!")
        return False
    
    ## NRC7292 UART 통신모듈에게 config.txt 시스템 정보 전달
    uart = UART(0, 115200) 												
    uart.init(115200, bits=8, parity=None, stop=0, txbuf=BUFFSIZE, rxbuf=BUFFSIZE)

    # NRC7292 initialize ready confirm
    send_buff='INIT'   
    while(init_count == 0):
        uart.write(send_buff)
        time.sleep(1)
        print("NRC7292 initialize communication......", send_buff, init_count)
        if uart.any():   
            recv_buff = uart.read()
            print("uart read data = ", recv_buff[:7])
            if(recv_buff[:7] == b"INIT_OK"):
                init_count +=  1
#               logfile.write_log("NRC7292 initialize communication......seccess\n")

    print("init_count =>", init_count)          
    # config file send and confirm
    while(init_count == 1):
        json_string = json.dumps(config)
        send_buff = json_string.encode('utf-8')
        uart.write(send_buff)
        time.sleep(1)
        if uart.any():   
            recv_buff = uart.read()    
            if(recv_buff[:9] == b'CONFIG_OK'):
                print("CONFIG_OK", init_count)
                init_count += 1
#                logfile.write_log("NRC7292 initialize config file sending......success\n")
    return True

#################################################
# log directory check & file mgmt 10Mb max size #
#################################################

# 로그 디렉토리 경로
log_dir = '/log/'

# 로그 파일 이름 패턴
log_pattern = 'edge.log'

# 로그 파일 최대 크기 (10 메가바이트)
max_log_size = 10 * 1024 * 1024

# 로그 파일 최대 갯수
max_log_count = 9

def create_log_dir():
    try:
        os.mkdir("/log")
    finally:
        try:
            os.rename("/log/edge.log", "/log/edge.log0")
        finally:       
            return True
        
def get_log_files():
    return [f for f in os.listdir(log_dir) if f.startswith(log_pattern)]

def get_log_file_sizes():
    log_files = get_log_files()
    sizes = {}
    for filename in log_files:
        file_path = log_dir+filename
        print("file_path = ", file_path)
        sizes[filename] = os.stat(file_path)[6]
    return sizes

def manage_log_files():
    create_log_dir()

    log_files = get_log_files()
    if len(log_files) > max_log_count:
        # 파일명을 정렬하여 가장 큰 파일 삭제
        log_files.sort()
        file_to_delete = log_files.pop()
        os.remove(log_dir+file_to_delete)
    
    sizes = get_log_file_sizes()
    total_size = sum(sizes.values())
    while total_size > max_log_size:
        # 가장 큰 파일을 삭제하여 디렉토리 크기를 조정
        largest_file = max(sizes, key=sizes.get)
        os.remove(os.path.join(log_dir, largest_file))
        total_size -= sizes[largest_file]
        del sizes[largest_file]
    
    if len(log_files) > 0:
        # 파일 이름 업데이트
        log_files.sort(reverse=True)
        count = 1

        for i, filename in enumerate(log_files):
            file_no=int(filename[8])+count
            new_filename = f"{log_pattern}{file_no}"
            os.rename(log_dir+filename, log_dir+new_filename)
            count + 1
    
    # 새로운 로그 파일 생성
    new_log_file =log_dir+f"{log_pattern}"
    with open(new_log_file, 'w') as f:
        # 로그 데이터 작성 (이 부분을 실제 로깅 로직으로 대체)
        tm=time.localtime()
        log_tm = f"{tm[0:6]}"
        print("log file create  ==> ", new_log_file)
        log_data = log_tm + "loging start : This is a log message.\n"
        f.write(log_data)


#################################################
# system booting error => endless loop process  #
#################################################

def system_err_boot_fail():
    print("[LCD diplay] System Boot Error")   #lcd에 시스템 오류 메시지를 표시한다
#    while(1):
#       time.sleep(60)

############################################
#   main process routine                   #
############################################

# 로그파일 관리 실행
#machine.freq(200000000) #over clocking 200Mhz
manage_log_files()

# config 파일 관리 실행
config = get_config_default(file)

#ntptime.settime()
print("time ::", time.localtime())

rc = config_info_check(config)
if(rc != True):
    system_err_boot_fail()
else:    
    print("system boot ok......................")