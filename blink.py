import random
import time
from collections.abc import Callable, Iterable
from functools import cache
from shutil import get_terminal_size
from typing import NamedTuple, Protocol, Self, SupportsIndex, cast, overload

from rpi_ws281x import Color, PixelStrip


class Strip(Protocol):
    @overload
    def __setitem__(self, pos: SupportsIndex, value: int, /) -> None: ...
    @overload
    def __setitem__(self, pos: slice, value: Iterable[int], /) -> None: ...

    @overload
    def __getitem__(self, pos: SupportsIndex, /) -> int: ...
    @overload
    def __getitem__(self, pos: slice, /) -> Iterable[int]: ...

    def __len__(self) -> int: ...

    def show(self) -> None: ...


class TerminalStrip(list[int]):
    """Drop-in replacement for PixelStrip printing pixels to the terminal"""

    def __init__(self, num: int, *_args, **_kwargs):
        super().__init__([0] * num)

    def __str__(self) -> str:
        pixels = (f"{RGB.from_int(value).ansi}▪" for value in self)
        return f"\x1b[48;2;0;0;0m{''.join(pixels)}\x1b[0m"

    def show(self) -> None:
        print(self)


@cache
def get_strip(num: int | None = None, pin: int = 18) -> Strip:
    """Try to initialize real PixelStrip, fall back to terminal output"""
    try:
        strip = PixelStrip(
            num=num or 300,
            pin=pin,
        )
        strip.begin()
        # the cast is half a lie: PixelStrip _technically_ allows using kwargs
        # for `__getitem__` etc. and has no static annotations guaranteeing the
        # the relationship between pos and return type (int->int, slice->list:
        return cast(Strip, strip)
    except RuntimeError:
        return TerminalStrip(num=num or get_terminal_size().columns)


class HSI(NamedTuple):
    hue: float
    saturation: float
    intensity: float


class RGB(NamedTuple):
    r: int
    g: int
    b: int

    @classmethod
    def from_int(cls, r: int) -> Self:
        return cls(
            r=(r >> 16) & 0xFF,
            g=(r >> 8) & 0xFF,
            b=r & 0xFF,
        )

    @classmethod
    def random(cls) -> Self:
        return cls.from_int(random.randint(0, 0xFFFFFF))

    @property
    def ansi(self) -> str:
        return f"\x1b[38;2;{self.r};{self.g};{self.b}m"

    @property
    def hsi(self) -> HSI:
        # see https://en.wikipedia.org/wiki/HSL_and_HSV
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
        return HSI(hue, saturation, intensity)

    def __str__(self) -> str:
        return f"#{int(self):06x}"

    def __invert__(self) -> Self:
        return self.from_int(0xFFFFFF - int(self))

    def __int__(self) -> int:
        return (self.r << 16) | (self.g << 8) | self.b


def wipe(strip: Strip, color: int = Color(0, 0, 0)) -> None:
    for i in range(len(strip)):
        strip[i] = color
    strip.show()


def random_rain(
    strip: Strip, pixels: list[int] | None = None, sleep: float = 0.001
) -> None:
    positions = list(range(len(strip)))
    random.shuffle(positions)
    for pos in positions:
        strip[pos] = pixels[pos] if pixels else int(RGB.random())
        strip.show()
        time.sleep(sleep)


def random_wipe(strip: Strip, c: int = 0) -> None:
    pixels = [x for x in range(len(strip))]
    random.shuffle(pixels)
    for i in pixels:
        strip[i] = c
        strip.show()
        time.sleep(0.001)


def shuffle(strip: Strip) -> None:
    strip[:] = [int(RGB.random()) for _ in range(len(strip))]
    strip.show()


def _close_in(from_: int, to: int) -> int:
    if from_ == to:
        return to
    return from_ + (1 if from_ < to else -1)


def slow_transition(
    strip: Strip, c: RGB | None = None, c_next: RGB | None = None
) -> None:
    c = c or RGB.random()
    c_next = c_next or ~c
    wipe(strip, int(c))
    while c != c_next:
        c = RGB(
            _close_in(c.r, c_next.r),
            _close_in(c.g, c_next.g),
            _close_in(c.b, c_next.b),
        )
        wipe(strip, int(c))
        time.sleep(0.01)


def quicksort(
    strip: Strip,
    lt_func: Callable[[RGB, RGB], bool] = lambda a, b: a.hsi < b.hsi,
    sleep: float = 0.01,
    from_index: int = 0,
    to_index: int | None = None,
) -> None:
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


def pride(strip: Strip) -> None:
    new_pride_colors = [
        0xFFFFFF,
        0xF6AAB8,
        0x60CDF6,
        0x674018,
        0x050708,
        0xE51E25,
        0xF68D1F,
        0xF9EE14,
        0x0D8040,
        0x3D5FAC,
        0x742A85,
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
    quicksort(
        strip,
        lambda x, y: new_pride_colors.index(int(x)) < new_pride_colors.index(int(y)),
        sleep=0.1,
    )
    time.sleep(1)
    for c in new_pride_colors:
        random_wipe(strip, c)
    c = RGB.from_int(new_pride_colors[-1])
    for c_next in map(RGB.from_int, new_pride_colors):
        slow_transition(strip, c, c_next)
        c = c_next
    random.shuffle(pixels)
    random_rain(strip, pixels)
    quicksort(
        strip,
        lambda x, y: new_pride_colors.index(int(x)) < new_pride_colors.index(int(y)),
    )


def all_the_colors(strip: Strip) -> None:
    random_rain(
        strip, pixels=[i * (0xFFFFFF // len(strip)) for i in range(len(strip), 0, -1)]
    )
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
