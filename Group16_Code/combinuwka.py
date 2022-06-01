from time import sleep
import RPi.GPIO as GPIO
import pigpio
import time, sys
import spidev

pi = pigpio.pi()
GPIO.setmode(GPIO.BCM)

DIR = 20 # Direction GPIO Pin
STEP = 21 # Step GPIO Pin
CW = 1 # Clockwise Rotation
CCW = 0 # Counterclockwise Rotation

pi.set_mode(DIR, pigpio.OUTPUT)
pi.set_mode(STEP, pigpio.OUTPUT)
GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)

valve_pin = 16
GPIO.setup(valve_pin,GPIO.OUT)
spi = spidev.SpiDev()
spi.open(0,0)

def motor_online():
    pps = 300
    for n in range (8):
        pi.set_PWM_dutycycle(STEP, 128) # PWM 1/2 On 1/2 Off, 128
        pi.set_PWM_frequency(STEP, pps)
        pps = pps + 100
        sleep(1.5)   

def level_control(channel):   
    if GPIO.input(24):   
        print ("Tank 3 is full")
        pi.set_PWM_dutycycle(STEP, 0) # PWM off
    else:                
        print ("Everyting is fine")
        motor_online()      
GPIO.add_event_detect(24, GPIO.RISING, callback = level_control)

def analog_read(channel): 
    spi.max_speed_hz = 1350000
    r = spi.xfer2([1, (8 + channel) << 4, 0])
    adc_out = ((r[1]&3) << 8) + r[2]
    return adc_out

flowrate_pin = 13
GPIO.setup(flowrate_pin,GPIO.IN)
time_start = 0.0
time_end = 0.0
gpio_last = 0

pi.write(DIR, CCW) 
MODE = (14, 15, 18) 
RESOLUTION = {'Full': (0, 0, 0),
 '1/2': (1, 0, 0),
 '1/4': (0, 1, 0),
 '1/8': (1, 1, 0),
 '1/16': (0, 0, 1),
 '1/32': (1, 0, 1)}
for i in range(3):
    pi.write(MODE[i], RESOLUTION['1/2'][i])
motor_online()
 
try:
    while True:
        rate_cnt = 0
        pulses = 0
        time_start = time.time()
        while pulses <= 5:
            gpio_cur = GPIO.input(flowrate_pin)
            if gpio_cur != 0 and gpio_cur != gpio_last:
                pulses = pulses + 1
            gpio_last = gpio_cur
        rate_cnt += 1
        time_end = time.time()
        output = rate_cnt/(time_end-time_start)
        print("Water flow is", output)

        reading = analog_read(0)
        print("Pressure is", reading))

        if reading >= 50: 
            GPIO.output(valve_pin,GPIO.HIGH)
        else:
            GPIO.output(valve_pin,GPIO.LOW)
        sleep(0.1)
        
except KeyboardInterrupt:
    print ("\nCtrl-C pressed. Stopping PIGPIO and exiting...")
finally:
    pi.set_PWM_dutycycle(STEP, 0) # PWM off
    pi.stop()
    GPIO.cleanup()
