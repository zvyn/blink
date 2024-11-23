from blink import HSI, RGB, TerminalStrip, quicksort, shuffle


def test_quicksort():
    strip = TerminalStrip(80)
    shuffle(strip)
    assert sorted(strip) != strip
    quicksort(strip, lambda x, y: int(x) < int(y))
    assert sorted(strip) == strip


def test_ansi():
    strip = TerminalStrip(1)
    strip[0] = 0xFF00FF
    assert str(strip) == "\x1b[48;2;0;0;0m\x1b[38;2;255;0;255m▪\x1b[0m"


def test_rgb_conversion():
    assert RGB.from_int(0xFF00FF).hsi == HSI(5.0, 1.0, 170.0)
