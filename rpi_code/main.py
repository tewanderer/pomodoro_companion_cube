from machine import Pin
from machine import PWM
from esp32_gpio_lcd import GpioLcd
import time

passive_buzzer = PWM(Pin(0))

green_led = Pin(6,Pin.OUT)
blue_led = Pin(7,Pin.OUT)
red_led = Pin(8,Pin.OUT)

notes = [
    (587, 0.09),   # D5
    (740, 0.09),   # F#5
    (880, 0.09),   # A5
    (1175, 0.09),  # D6
    (1480, 0.20),  # F#6 (held, triumphant finish)
]

lcd = GpioLcd(rs_pin=Pin(16),
              enable_pin=Pin(17),
              d4_pin=Pin(18),
              d5_pin=Pin(19),
              d6_pin=Pin(20),
              d7_pin=Pin(21),
              num_lines=2,
              num_columns=16)

button=Pin(15, Pin.IN, Pin.PULL_UP)

skip_button=Pin(14, Pin.IN, Pin.PULL_UP)

#button.value() == 1 means not pressed
#button.value() == 0 means pressed

POMODORO_TIMER = 3
SHORT_BREAK_TIMER = 4
LONG_BREAK_TIMER = 5

def beep():
        red_led.value(1)
        time.sleep_ms(100)
        red_led.value(0)
        passive_buzzer.freq(587)
        passive_buzzer.duty_u16(30000)
        time.sleep(0.1)
        passive_buzzer.duty_u16(0)

def check_pause():
    if button.value() == 0:
        time.sleep_ms(50)
        
        #this basically means wait here until the button is released
        while button.value() == 0:
            pass
        beep()
        
        lcd.clear()
        lcd.putstr("paused")
        lcd.move_to(0,1)
        lcd.putstr("resume? (press)")
        
        #this basically means wait here until a button is pressed
        while button.value() == 1:
            pass
        
        beep()
        time.sleep_ms(50)
        
        while button.value() == 0:
            pass
        
        return True
    
    return False


def check_skip():
    if skip_button.value() == 0:
        time.sleep_ms(50)
        
        # confirm it's still pressed after the bounce settles
        if skip_button.value() == 0:
            
            # wait here until the button is released
            while skip_button.value() == 0:
                pass
            
            return True
    
    return False
        
    
        
def pomodoro():
    time_count=0
    lcd.clear()
    lcd.putstr("ready to begin?")

    
    while button.value() == 1:
        pass
    
    beep()
    
    while button.value() == 0:
        pass
    
    while (time_count <= POMODORO_TIMER):
        lcd.clear()
        lcd.move_to(0,0)
        lcd.putstr("time to focus.")
        lcd.move_to(0,1)
        lcd.putstr(str(POMODORO_TIMER - time_count) + " seconds.")
        
        for i in range(100):
            paused = check_pause()
            skipped = check_skip()
            
            if paused:
                lcd.clear()
                lcd.move_to(0,0)
                lcd.putstr("time to focus.")
                lcd.move_to(0,1)
                lcd.putstr(str(POMODORO_TIMER - time_count) + " seconds.")
            time.sleep_ms(10)
            
            if skipped:
                beep()
                return
            
        time_count += 1
        
    for freq, dur in notes:
        passive_buzzer.freq(freq)
        passive_buzzer.duty_u16(30000)
        time.sleep(dur)
        passive_buzzer.duty_u16(0)
        
def short_break():
    time_count=0
    lcd.clear()
    lcd.putstr("short break?")
    
    while button.value() == 1:
        pass
    
    beep()
    
    while button.value() == 0:
        pass
    
    while (time_count <= SHORT_BREAK_TIMER):
        lcd.clear()
        lcd.move_to(0,0)
        lcd.putstr("breaktime.")
        lcd.move_to(0,1)
        lcd.putstr(str(SHORT_BREAK_TIMER - time_count) + " seconds.")
        
        for i in range(100):
            paused = check_pause()
            skipped = check_skip()
            
            if paused:
                lcd.clear()
                lcd.move_to(0,0)
                lcd.putstr("breaktime.")
                lcd.move_to(0,1)
                lcd.putstr(str(SHORT_BREAK_TIMER - time_count) + " seconds.")
            time.sleep_ms(10)
            
            if skipped:
                beep()
                return
            
        time_count += 1

    for freq, dur in notes[::-1]:
        passive_buzzer.freq(freq)
        passive_buzzer.duty_u16(30000)
        time.sleep(dur)
        passive_buzzer.duty_u16(0)
        
        
def long_break():
    time_count=0
    lcd.clear()
    lcd.putstr("long break?")

    
    while button.value() == 1:
        pass
    
    beep()
    
    while button.value() == 0:
        pass
    
    while (time_count <= LONG_BREAK_TIMER):
        lcd.clear()
        lcd.move_to(0,0)
        lcd.putstr("breaktime.")
        lcd.move_to(0,1)
        lcd.putstr(str(LONG_BREAK_TIMER - time_count) + " seconds.")
        
        for i in range(100):
            paused = check_pause()
            skipped = check_skip()
            
            if paused:
                lcd.clear()
                lcd.move_to(0,0)
                lcd.putstr("breaktime.")
                lcd.move_to(0,1)
                lcd.putstr(str(LONG_BREAK_TIMER - time_count) + " seconds.")
            time.sleep_ms(10)
            
            if skipped:
                beep()
                return
            
        time_count += 1
        
    for freq, dur in notes[::-1]:
        passive_buzzer.freq(freq)
        passive_buzzer.duty_u16(30000)
        time.sleep(dur)
        passive_buzzer.duty_u16(0)
    

while True:
    pomodoro()
    short_break()
    long_break()
