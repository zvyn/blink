import time
import random
from functools import cache
from typing import Iterable, NoReturn, Self, SupportsIndex, overload
from dataclasses import dataclass

from rpi_ws281x import Color, PixelStrip as LedStrip, ws

RESET_ANSI = '\x1b[0m'



class Strip:
    led_strip: LedStrip | list[int]
    num: int

    @overload
    def __init__(self, *, led_strip: LedStrip): ...
    @overload
    def __init__(self, *, num: int) -> None: ...
    def __init__(self, *, num: int | None = None, led_strip: LedStrip | None = None):
        if led_strip:
            self.led_strip = led_strip
            self.num = led_strip.numPixels()
        elif num:
            self.led_strip = [0] * num
            self.num = num
        else:
            raise TypeError

    @overload
    def __setitem__(self, pos: SupportsIndex, value: int, /) -> None: ...
    @overload
    def __setitem__(self, pos: slice, value: Iterable[int], /) -> None: ...
    def __setitem__(self, pos, value, /) -> None:
        self.led_strip[pos] = value
    
    @overload
    def __getitem__(self, pos: SupportsIndex) -> int: ...
    @overload
    def __getitem__(self, pos: slice) -> Iterable[int]: ...
    def __getitem__(self, pos):
        return self.led_strip[pos]

    def __len__(self):
        return self.num

    def show(self):
        if isinstance(self.led_strip, LedStrip):
            self.led_strip.show()
        else:
            pixels = (
                f"{RGB.from_int(value).ansi}▪"
                for value in self
            )
            print(f"\x1b[48;2;0;0;0m{''.join(pixels)}{RESET_ANSI}", flush=True)


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

    @property
    def ansi(self):
        return f"\x1b[38;2;{self.r};{self.g};{self.b}m"

    def __str__(self) -> str:
        return f"#{int(self):06x}"

    def __invert__(self) -> Self:
        return self.from_int(0xffffff - int(self))

    def __int__(self) -> int:
        return (self.r << 16) | (self.g << 8) | self.b


@cache
def get_strip() -> Strip:
    led_strip = LedStrip(
        num=300,
        pin=18,
        freq_hz=800_000,
        dma=10,
        brightness=20,
        invert=False,
        channel=0,
        strip_type=ws.WS2811_STRIP_GRB,
    )
    led_strip.begin()
    return Strip(led_strip=led_strip)


def wipe(strip: Strip, color: int = Color(0, 0, 0)) -> None:
    for i in range(strip.num):
        strip[i] = color
    strip.show()


def random_rain(strip: Strip) -> None:
    pixels = [x for x in range(0, strip.num)]
    random.shuffle(pixels)
    for i in pixels:
        strip[i] = int(RGB.random())
        strip.show()
        time.sleep(0.001)


def random_wipe(strip: Strip, c: int = 0) -> None:
    pixels = [x for x in range(0, strip.num)]
    random.shuffle(pixels)
    for i in pixels:
        strip[i] = c
        strip.show()
        time.sleep(0.001)


def shuffle(strip: Strip) -> None:
    strip[:] = [
        int(RGB.random())
        for _ in range(len(strip))
    ]
    strip.show()


def _close_in(from_, to):
    if from_ == to:
        return to
    return from_ + (1 if from_ < to else -1)


def slow_transition(strip: Strip, c: RGB | None = None, c_next: RGB  | None = None) -> None:
    c = c or RGB.random()
    c_next = c_next or ~c
    wipe(strip, int(c))
    while c != c_next:
        c.r = _close_in(c.r, c_next.r)
        c.g = _close_in(c.g, c_next.g)
        c.b = _close_in(c.b, c_next.b)
        wipe(strip, int(c))
        time.sleep(0.001)


def quicksort(strip: Strip, from_index: int = 0, to_index: int | None = None):
    """Sort the colors on the strip by their numerical value using quicksort"""
    to_index = len(strip) - 1 if to_index is None else to_index
    if from_index >= to_index:
        return

    i, j = from_index, to_index
    pivot = strip[random.randint(from_index, to_index)]

    while i <= j:
        while strip[i] < pivot:
            i += 1
        while strip[j] > pivot:
            j -= 1

        if i <= j:
            strip[i], strip[j] = strip[j], strip[i]
            strip.show()
            i, j = i + 1, j - 1
    quicksort(strip, from_index, j)
    quicksort(strip, i, to_index)


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
        step = random.choice((2, 3, 5))
        for i in (
            range(len(strip), 0, -step) if invert else
            range(0, len(strip), step)
        ):
            strip[i] = int(c)
            strip.show()
            time.sleep(0.001)
        while c != c_next:
            c.r = _close_in(c.r, c_next.r)
            c.g = _close_in(c.g, c_next.g)
            c.b = _close_in(c.b, c_next.b)
            for i in range(1, len(strip), 2):
                strip[i] = int(c)
            strip.show()
            time.sleep(0.001)
        c = c_next



def demo(strip: Strip | None = None) -> NoReturn:
    strip = strip or get_strip()

    while True:
        random_wipe(strip, 0)
        time.sleep(0.1)
        random_rain(strip)
        quicksort(strip)
        random_rain(strip)
        quicksort(strip)
        c = RGB.random()
        random_wipe(strip, int(c))
        slow_transition(strip, c)
        slow_transition(strip, c, RGB.random())
        slow_transition(strip, c)


if __name__ == "__main__":
    demo()
