from machine import Pin, PWM
from esp32_gpio_lcd import GpioLcd
import time

# --- Hardware setup ---------------------------------------------------

passive_buzzer = PWM(Pin(0))

lcd = GpioLcd(rs_pin=Pin(16),
              enable_pin=Pin(17),
              d4_pin=Pin(18),
              d5_pin=Pin(19),
              d6_pin=Pin(20),
              d7_pin=Pin(21),
              num_lines=2,
              num_columns=16)

button = Pin(15, Pin.IN, Pin.PULL_UP)       # pause/resume
skip_button = Pin(14, Pin.IN, Pin.PULL_UP)  # skip current phase

green_led = Pin(6, Pin.OUT)  # lit during focus
blue_led = Pin(7, Pin.OUT)   # lit during breaks
red_led = Pin(8, Pin.OUT)    # lit while paused

# button.value() == 1 means not pressed
# button.value() == 0 means pressed

# --- Config -------------------------------------------------------------

POMODORO_TIMER = 3
SHORT_BREAK_TIMER = 4
LONG_BREAK_TIMER = 5

FINISH_JINGLE = [
    (587, 0.09),   # D5
    (740, 0.09),   # F#5
    (880, 0.09),   # A5
    (1175, 0.09),  # D6
    (1480, 0.20),  # F#6 (held, triumphant finish)
]

# --- LED helper -----------------------------------------------------------

def set_led(color):
    """Turn on exactly one status LED ('green', 'blue', 'red', or None for off)."""
    green_led.value(1 if color == "green" else 0)
    blue_led.value(1 if color == "blue" else 0)
    red_led.value(1 if color == "red" else 0)

# --- Sound helpers --------------------------------------------------------

def beep(color=None):
    """
    Plays a short confirmation tone. If a color is given, blips that LED
    off-then-on right as the tone plays, so every interaction (start,
    pause, resume, skip) gives a visible flash in the active phase's color.
    """
    if color:
        set_led(None)
        time.sleep_ms(15)
        set_led(color)

    passive_buzzer.freq(587)
    passive_buzzer.duty_u16(30000)
    time.sleep(0.1)
    passive_buzzer.duty_u16(0)

def play_jingle(notes, color):
    """Plays the finish jingle, flashing the LED off/on with each note."""
    for freq, dur in notes:
        set_led(None)
        time.sleep_ms(20)
        set_led(color)

        passive_buzzer.freq(freq)
        passive_buzzer.duty_u16(30000)
        time.sleep(dur)
        passive_buzzer.duty_u16(0)

# --- Display helper ---------------------------------------------------

def show(line1, line2=""):
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr(line1)
    if line2:
        lcd.move_to(0, 1)
        lcd.putstr(line2)

# --- Button handling --------------------------------------------------

def wait_for_press_then_release(btn):
    """Block until btn is pressed, then block until it's released."""
    while btn.value() == 1:
        pass
    while btn.value() == 0:
        pass

def check_pause(phase_color):
    """
    If the pause button is pressed, show the paused screen, light the
    red LED, and block until resumed -- while also listening for a skip
    press during that wait. Restores phase_color's LED before returning.

    Returns (paused, skipped_while_paused).
    """
    if button.value() == 0:
        time.sleep_ms(50)

        # wait here until the button is released
        while button.value() == 0:
            pass
        beep(phase_color)

        set_led("red")
        show("paused", "resume? (press)")

        # wait here until the button is pressed again to resume,
        # but keep an eye on the skip button the whole time
        while button.value() == 1:
            if check_skip():
                set_led(phase_color)
                return True, True

        beep(phase_color)
        time.sleep_ms(50)
        while button.value() == 0:
            pass

        set_led(phase_color)
        return True, False

    return False, False

def check_skip():
    """
    If the skip button is pressed and held long enough to debounce,
    wait for release and return True. Returns False otherwise.
    """
    if skip_button.value() == 0:
        time.sleep_ms(50)

        # confirm it's still pressed after the bounce settles
        if skip_button.value() == 0:
            # wait here until the button is released
            while skip_button.value() == 0:
                pass
            return True

    return False

# --- Core phase runner --------------------------------------------------

def run_phase(start_prompt, active_header, duration, led_color, jingle):
    """
    Runs one timed phase (focus or break): waits for a start press,
    counts down while listening for pause/skip, then plays the jingle.
    """
    show(start_prompt)
    wait_for_press_then_release(button)
    set_led(led_color)
    beep(led_color)

    time_count = 0
    while time_count <= duration:
        seconds_left = duration - time_count
        show(active_header, f"{seconds_left} seconds.")

        for _ in range(100):
            paused, skipped_in_pause = check_pause(led_color)
            skipped = skipped_in_pause or check_skip()

            if paused and not skipped:
                show(active_header, f"{seconds_left} seconds.")

            time.sleep_ms(10)

            if skipped:
                beep(led_color)
                return

        time_count += 1

    play_jingle(jingle, led_color)

# --- Phases --------------------------------------------------------------

def pomodoro():
    run_phase(
        start_prompt="ready to begin?",
        active_header="time to focus.",
        duration=POMODORO_TIMER,
        led_color="green",
        jingle=FINISH_JINGLE,
    )

def short_break():
    run_phase(
        start_prompt="short break?",
        active_header="breaktime.",
        duration=SHORT_BREAK_TIMER,
        led_color="blue",
        jingle=FINISH_JINGLE[::-1],
    )

def long_break():
    run_phase(
        start_prompt="long break?",
        active_header="breaktime.",
        duration=LONG_BREAK_TIMER,
        led_color="blue",
        jingle=FINISH_JINGLE[::-1],
    )

# --- Main loop -------------------------------------------------------

while True:
    pomodoro()
    short_break()
    long_break()
