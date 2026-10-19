"""
用代码合成音效和背景音乐，保存成 WAV 文件。

声音就是一串数字（采样）：每秒 22050 个数字，描述喇叭在每个瞬间的位置。
正弦波 sin(2π × 频率 × 时间) 就是一个纯音，频率越高音越高。
让音量随时间慢慢变小（衰减），听起来就像敲了一下音乐盒。

文件只在第一次运行时生成，之后直接用。
"""

import math
import wave
from array import array
from pathlib import Path

RATE = 22050   # 每秒采样数


def _note_frequency(semitones_from_a4):
    """音高：以 A4（440 Hz）为基准，每高一个半音频率乘以 2 的 1/12 次方。"""
    return 440.0 * 2 ** (semitones_from_a4 / 12)


# C 大调里常用的几个音，相对 A4 的半音数
NOTES = {
    "C3": -21, "E3": -17, "F3": -16, "G3": -14, "A3": -12, "B3": -10,
    "C4": -9, "D4": -7, "E4": -5, "F4": -4, "G4": -2, "A4": 0, "B4": 2,
    "C5": 3, "D5": 5, "E5": 7, "G5": 10, "A5": 12, "C6": 15,
}


def _add_tone(buffer, start, frequency, duration, volume, decay=6.0, attack=0.005):
    """在 buffer 的 start 秒处叠加一个会慢慢变小的音。"""
    first = int(start * RATE)
    count = min(int(duration * RATE), len(buffer) - first)
    step = 2 * math.pi * frequency / RATE
    attack_samples = max(1, int(attack * RATE))
    for i in range(count):
        t = i / RATE
        envelope = math.exp(-decay * t) * min(1.0, i / attack_samples)
        # 加一点高八度的泛音，声音更像乐器而不是"哔"
        sample = math.sin(step * i) + 0.3 * math.sin(2 * step * i)
        buffer[first + i] += volume * envelope * sample


def _save(buffer, path):
    """把 -1 到 1 之间的小数转成 16 位整数，写成 WAV 文件。"""
    peak = max(1.0, max(abs(value) for value in buffer))
    samples = array("h", (int(32767 * 0.9 * value / peak) for value in buffer))
    with wave.open(str(path), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(RATE)
        file.writeframes(samples.tobytes())


def make_pop(path):
    """填一格时的"啵"声：很短的高音。"""
    buffer = [0.0] * int(0.12 * RATE)
    _add_tone(buffer, 0, _note_frequency(NOTES["E5"]), 0.12, 0.5, decay=40)
    _save(buffer, path)


def make_color_done(path):
    """一种颜色填完：三个音快速往上走。"""
    buffer = [0.0] * int(0.7 * RATE)
    for i, note in enumerate(("C5", "E5", "G5")):
        _add_tone(buffer, i * 0.08, _note_frequency(NOTES[note]), 0.5, 0.45, decay=8)
    _save(buffer, path)


def make_complete(path):
    """整张图完成：一段短短的欢快旋律加和弦。"""
    buffer = [0.0] * int(2.2 * RATE)
    melody = ("C5", "E5", "G5", "C6")
    for i, note in enumerate(melody):
        _add_tone(buffer, i * 0.13, _note_frequency(NOTES[note]), 1.2, 0.4, decay=4)
    for note in ("C4", "E4", "G4"):
        _add_tone(buffer, 0.55, _note_frequency(NOTES[note]), 1.6, 0.25, decay=2)
    _save(buffer, path)


def make_music(path):
    """
    轻松的背景音乐：C → Am → F → G 四个和弦循环，
    每个和弦上弹一串分解和弦（像音乐盒），下面垫一个低音。
    """
    beat = 0.75                     # 每拍 0.75 秒（80 BPM）
    chords = [
        ("C3", ["C4", "E4", "G4", "C5", "E5", "C5", "G4", "E4"]),
        ("A3", ["A3", "C4", "E4", "A4", "C5", "A4", "E4", "C4"]),
        ("F3", ["F3", "A3", "C4", "F4", "A4", "F4", "C4", "A3"]),
        ("G3", ["G3", "B3", "D4", "G4", "B4", "G4", "D4", "B3"]),
    ]
    bars_per_chord = 2
    total = len(chords) * bars_per_chord * 4 * beat
    buffer = [0.0] * int(total * RATE)
    time = 0.0
    for bass, arpeggio in chords:
        for _bar in range(bars_per_chord):
            _add_tone(buffer, time, _note_frequency(NOTES[bass]), 4 * beat, 0.25, decay=0.8, attack=0.08)
            for i, note in enumerate(arpeggio):
                _add_tone(buffer, time + i * beat / 2, _note_frequency(NOTES[note]), 1.5, 0.18, decay=3)
            time += 4 * beat
    _save(buffer, path)


SOUNDS = {
    "pop": make_pop,
    "color_done": make_color_done,
    "complete": make_complete,
    "music": make_music,
}


def ensure_sounds(folder):
    """确保所有声音文件都已经生成，返回 {名字: 文件路径}。"""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, make in SOUNDS.items():
        path = folder / f"{name}.wav"
        if not path.exists():
            make(path)
        paths[name] = str(path)
    return paths
