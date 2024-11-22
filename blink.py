import time
import random
from functools import cache

from rpi_ws281x import Color, PixelStrip, ws

# LED strip configuration:
LED_COUNT = 300         # Number of LED pixels.
LED_PIN = 18           # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ = 800_000   # LED signal frequency in hertz (usually 800khz)
LED_DMA = 10           # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 20  # 255   # Set to 0 for darkest and 255 for brightest
LED_INVERT = False     # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL = 0
LED_STRIP = ws.WS2811_STRIP_GRB


@cache
def get_strip():
    # Create NeoPixel object with appropriate configuration.
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
    # Intialize the library (must be called once before other functions).
    strip.begin()
    return strip


class RGB:
    __slots__ = ["r", "g", "b"]

    r: int
    g: int
    b: int

    def __init__(self, r: int | None = None, g: int | None = None, b: int | None = None):
        if r is None:
            assert g is None
            assert b is None
            r = random.randint(0, 0xffffff)
        if g is None:
            assert b is None
            self.r = (r >> 16) & 0xff
            self.g = (r >> 8) & 0xff
            self.b = r & 0xff
        else:
            self.r = r
            self.g = g
            self.b = b

    def __str__(self):
        return f"#{int(self):06x}"

    def __eq__(self, other):
        return int(self) == int(other)

    def __invert__(self):
        return type(self)(0xffffff - int(self))

    def __int__(self):
        return (self.r << 16) | (self.g << 8) | self.b


def wipe(strip, color: int = Color(0, 0, 0)):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
    strip.show()


def random_rain(strip):
    pixels = [x for x in range(0, strip.numPixels())]
    random.shuffle(pixels)
    for i in pixels:
        c = random.randint(0, 0xffffff)
        strip.setPixelColor(i, int(c))
        strip.show()
        time.sleep(0.001)


def random_wipe(strip, c: int = 0):
    pixels = [x for x in range(0, strip.numPixels())]
    random.shuffle(pixels)
    for i in pixels:
        strip.setPixelColor(i, int(c))
        strip.show()
        time.sleep(0.001)


def shuffle(strip):
    for i in range(0, strip.numPixels()):
        c = random.randint(0, 0xffffff)
        strip.setPixelColor(i, int(c))
    strip.show()


def next_val(from_, to):
    if from_ == to:
        return to
    return from_ + (1 if from_ < to else -1)


def slow_transition(strip, c: RGB = None, c_next: RGB = None):
    c = c or RGB(random.randint(1, 0xffffff))
    c_next = c_next or ~c
    wipe(strip, int(c))
    print(c, "->", c_next)
    while c != c_next:
        c.r = next_val(c.r, c_next.r)
        c.g = next_val(c.g, c_next.g)
        c.b = next_val(c.b, c_next.b)
        wipe(strip, int(c))
        time.sleep(0.001)


def to_complex(strip):
    c = RGB(0xff0000)
    while True:
        invert = random.randint(0, 1)
        if invert:
            c_next = ~c
            invert = False
        else:
            c_next = RGB(random.randint(1, 0xffffff))
            invert = True
        print(c, "->", c_next)
        step = random.choice((2, 3, 5))
        for i in (
            range(strip.numPixels(), 0, -step) if invert else
            range(0, strip.numPixels(), step)
        ):
            strip.setPixelColor(i, int(c))
            strip.show()
            time.sleep(0.001)
        while c != c_next:
            c.r = next_val(c.r, c_next.r)
            c.g = next_val(c.g, c_next.g)
            c.b = next_val(c.b, c_next.b)
            for i in range(1, strip.numPixels(), 2):
                strip.setPixelColor(i, int(c))
            strip.show()
            time.sleep(0.001)
        c = c_next



def demo(strip = None):
    strip = strip or get_strip()

    while True:
        c = RGB()
        random_wipe(strip, 0)
        time.sleep(0.1)
        random_rain(strip)
        for i in range(0, 1000, 20):
            shuffle(strip)
            time.sleep((1000 - i) / 1000)
        for i in range(0, 100):
            shuffle(strip)
            time.sleep(0.001)
        for i in range(0, 1000, 100):
            shuffle(strip)
            time.sleep(i / 1000)
        random_wipe(strip, int(c))
        slow_transition(strip, c)
        slow_transition(strip, c, RGB())
        slow_transition(strip, c)


if __name__ == "__main__":
    demo()
