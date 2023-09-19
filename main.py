from machine import UART
from time import sleep
import time
import heapq as queue
import _thread
from logfile import log_write


count = 0
elapsed_1m_time = 60
start_time = time.time()
sendbuf = '{EDGE:'

def moter_control(cmd):
    print("moter control section")
    sleep(10)
    
def lcd_comtrol(cmd):
    print("lcd control section")
    sleep(10)
    
def ipc_lock_check(mutax):
    mutax.acquire(waitflag=1, timeout=-1)
    print("세마포어 뮤텍스 이용하... ")
    if(mutax.locked()):
        print("세모포어 뮤택스가 사용중입니다.. ")
    mutax.release()
    return 
    
def system_fault():
    # 시스템 가동 불가 상태에 대한 처리
    return
    
def excution_cmd(cmd):  
#    print("명령을 수행하는 메인 루틴입니다")
    exec = queue.heappop(cmd)
    print("execution command = ", exec)
    log_write(exec)
    #if exec == 모터제어:
    #    moter_control()
    #if exec == lcd 표시:
    #   lcd_control
    return    


###############################################################
#        
# 스레드 처리 로직입니다 #1
#
###############################################################    
def comm_recv_thread(uart, cmd):
    # 수신된 데이터를 처리합니다.    
    try:
       while(1):
        if uart.any():
            data = uart.read()
            print("Receive data = {}".format(data.decode()))
            queue.heappush(cmd, data.decode())
              
    except OSError as e:
        print("comm recvive Thread error: ", e)


###############################################################
#        
# 스레드 처리 로직입니다 #2
#
###############################################################        
def main_thread(cmd):
    count = 0
    global start_time

    try:
        while True:
            current_time = time.time()

            # 경과한 시간을 계산
            time_elapsed = current_time - start_time
            
            if time_elapsed >= elapsed_1m_time:
                # 여기에 수행하려는 작업을 추가
                count = count + 1    
                buf = f"{sendbuf}{count}}}"
                uart.write(buf)
                print("Send data =" + buf)
                log_write(buf)             #/log/edge.log file wrtie 
                
                # 작업을 수행한 후 다시 시작 시간 초기화
                start_time = time.time()
         
            while(len(cmd) > 0):
                print("command {} pending",len(cmd))
                excution_cmd(cmd)
    except OSError as e:
        print("Main Thread Error : ", e)        
    
    

###############################################################
#        
# 메인로직 시작부분 입니다(쓰레드는 최대 2개까지 가능합니다)
#
###############################################################
#time.sleep(5)                                                       #booting delay 5 seconds
#machine.freq(200000000) 											# over clocking 20MHz 
uart = UART(0, 115200) 												# uart 1 => GP0(Tx), GP1(Rx)
uart.init(115200, bits=8, parity=None, stop=0, txbuf=16, rxbuf=16) 	#
cmd = []															# comman list queuedic
least_hb_time = time.ticks_us()										# 통신했던 최종 시간을 기록 5분 통신 불가시 통신 에러처
mutax = _thread.allocate_lock()										# Threading semaphore key = mutax
second_thread = _thread.start_new_thread(comm_recv_thread, (uart, cmd,)) #쓰레드 #1 입니다
main_thread(cmd,)														 #쓰레드 #2 입니다


