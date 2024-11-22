import time
import random
from functools import cache
from typing import NoReturn, Self
from dataclasses import dataclass

from rpi_ws281x import Color, PixelStrip as Strip, ws


@cache
def get_strip():
    strip = Strip(
        num=300,
        pin=18,
        freq_hz=800_000,
        dma=10,
        brightness=20,
        invert=False,
        channel=0,
        strip_type=ws.WS2811_STRIP_GRB,
    )
    strip.begin()
    return strip


@dataclass(slots=True, eq=True, order=True)
class RGB:
    r: int
    g: int
    b: int

    @classmethod
    def from_int(cls, r: int) -> Self:
        return cls(
            r=(r >> 16) & 0xff,
            g=(r >> 8) & 0xff,
            b=r & 0xff,
        )

    @classmethod
    def random(cls) -> Self:
        return cls.from_int(random.randint(0, 0xffffff))

    def __str__(self) -> str:
        return f"#{int(self):06x}"

    def __invert__(self) -> Self:
        return self.from_int(0xffffff - int(self))

    def __int__(self) -> int:
        return (self.r << 16) | (self.g << 8) | self.b


def wipe(strip: Strip, color: int = Color(0, 0, 0)) -> None:
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
    strip.show()


def random_rain(strip: Strip) -> None:
    pixels = [x for x in range(0, strip.numPixels())]
    random.shuffle(pixels)
    for i in pixels:
        c = random.randint(0, 0xffffff)
        strip.setPixelColor(i, int(c))
        strip.show()
        time.sleep(0.001)


def random_wipe(strip: Strip, c: int = 0) -> None:
    pixels = [x for x in range(0, strip.numPixels())]
    random.shuffle(pixels)
    for i in pixels:
        strip.setPixelColor(i, int(c))
        strip.show()
        time.sleep(0.001)


def shuffle(strip: Strip) -> None:
    for i in range(0, strip.numPixels()):
        c = random.randint(0, 0xffffff)
        strip.setPixelColor(i, int(c))
    strip.show()


def next_val(from_, to):
    if from_ == to:
        return to
    return from_ + (1 if from_ < to else -1)


def slow_transition(strip: Strip, c: RGB | None = None, c_next: RGB  | None = None) -> None:
    c = c or RGB.random()
    c_next = c_next or ~c
    wipe(strip, int(c))
    print(c, "->", c_next)
    while c != c_next:
        c.r = next_val(c.r, c_next.r)
        c.g = next_val(c.g, c_next.g)
        c.b = next_val(c.b, c_next.b)
        wipe(strip, int(c))
        time.sleep(0.001)


def to_complex(strip: Strip) -> NoReturn:
    c = RGB.random()
    while True:
        invert = random.randint(0, 1)
        if invert:
            c_next = ~c
            invert = False
        else:
            c_next = RGB.random()
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



def demo(strip: Strip | None = None) -> NoReturn:
    strip = strip or get_strip()

    while True:
        c = RGB.random()
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
        slow_transition(strip, c, RGB.random())
        slow_transition(strip, c)


if __name__ == "__main__":
    demo()
