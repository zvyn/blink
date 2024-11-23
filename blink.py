import time
import random
from functools import cache
from typing import Callable, Iterable, NoReturn, Self, Sequence, SupportsIndex, overload
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


@dataclass(slots=True, eq=True)
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

    @property
    def hsi(self) -> tuple[float, float, float]:
        max_ = max(self.r, self.g, self.b)
        min_ = min(self.r, self.g, self.b)
        intensity = (self.r + self.g + self.b) / 3
        saturation = 0.0 if intensity == 0.0 else 1 - (min_ / intensity)
        if (range_ := max_ - min_) != 0:
            match max_:
                case self.r:
                    hue = ((self.g - self.b) / range_) % 6
                case self.g:
                    hue = ((self.b - self.r) / range_) + 2
                case self.b:
                    hue = ((self.r - self.g) / range_) + 4
                case _:
                    raise AssertionError("max of items is one of items")
        else:
            hue = 0.0
        return hue, saturation, intensity


    def __str__(self) -> str:
        return f"#{int(self):06x}"

    def __invert__(self) -> Self:
        return self.from_int(0xffffff - int(self))

    def __int__(self) -> int:
        return (self.r << 16) | (self.g << 8) | self.b

    def __lt__(self, other: Self) -> bool:
        return self.hsi < other.hsi


@cache
def get_strip() -> Strip:
    try:
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
    except RuntimeError:
        return Strip(num=200)


def wipe(strip: Strip, color: int = Color(0, 0, 0)) -> None:
    for i in range(strip.num):
        strip[i] = color
    strip.show()


def random_rain(strip: Strip, pixels: list[int] | None = None, sleep: float = 0.001) -> None:
    positions = list(range(0, len(strip)))
    random.shuffle(positions)
    for pos in positions:
        strip[pos] = pixels[pos] if pixels else int(RGB.random())
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
        time.sleep(0.01)


def quicksort(strip: Strip, lt_func: Callable[[RGB, RGB], bool] = RGB.__lt__, sleep: float = 0.01, from_index: int = 0, to_index: int | None = None):
    """Sort the colors on the strip by their numerical value using quicksort"""
    to_index = len(strip) - 1 if to_index is None else to_index
    if from_index >= to_index:
        return

    i, j = from_index, to_index
    pivot = RGB.from_int(strip[random.randint(from_index, to_index)])

    while i <= j:
        while lt_func(RGB.from_int(strip[i]), pivot):
            i += 1
        while lt_func(pivot, RGB.from_int(strip[j])):
            j -= 1

        if i <= j:
            strip[i], strip[j] = strip[j], strip[i]
            strip.show()
            time.sleep(sleep)
            i, j = i + 1, j - 1
    quicksort(strip, lt_func=lt_func, sleep=sleep, from_index=from_index, to_index=j)
    quicksort(strip, lt_func=lt_func, sleep=sleep, from_index=i, to_index=to_index)


def hsi(strip):
    strip[:] = map(int, sorted(
        RGB.from_int(i * (0xffffff // len(strip)))
        for i in range(len(strip))
    )
    )
    strip.show()


def rgb(strip):
    strip[:] = (
        i * (0xffffff // len(strip))
        for i in range(len(strip))
    )
    strip.show()


def pride(strip):
    new_pride_colors = [
        0xffffff,
        0xf6aab8,
        0x60cdf6,
        0x674018,
        0x050708,
        0xe51e25,
        0xf68d1f,
        0xf9ee14,
        0x0d8040,
        0x3d5fac,
        0x742a85,
    ]
    pixels = [
        new_pride_colors[int(len(new_pride_colors) * (i / len(strip)))]
        for i in range(len(strip))
    ]
    random_rain(strip, pixels)
    quicksort(strip)
    quicksort(strip, lambda x, y: int(x) > int(y))
    quicksort(strip, lambda x, y: False)
    random.shuffle(pixels)
    random_rain(strip, pixels)
    quicksort(strip, lambda x, y: new_pride_colors.index(int(x)) < new_pride_colors.index(int(y)), sleep=0.1)
    time.sleep(1)
    for c in new_pride_colors:
        random_wipe(strip, c)
    c = RGB.from_int(new_pride_colors[-1])
    for c_next in new_pride_colors:
        slow_transition(strip, c, RGB.from_int(c_next))
    random.shuffle(pixels)
    random_rain(strip, pixels)
    quicksort(strip, lambda x, y: new_pride_colors.index(int(x)) < new_pride_colors.index(int(y)))


def all_the_colors(strip):
    random_rain(strip, pixels=[i * (0xffffff // len(strip)) for i in range(len(strip), 0, -1)])
    quicksort(strip, lambda x, y: int(x) < int(y))
    time.sleep(1)
    quicksort(strip)
    time.sleep(1)
    quicksort(strip, lambda x, y: x > y)


if __name__ == "__main__":
    strip = get_strip()
    while True:
        all_the_colors(strip)
        time.sleep(1)
        pride(strip)
        time.sleep(1)
