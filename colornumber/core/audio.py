"""
用代码合成音效和背景音乐，保存成 WAV 文件。

声音就是一串数字（采样）：每秒几万个数字，描述喇叭在每个瞬间的位置。
正弦波 sin(2π × 频率 × 时间) 是一个纯音；把几个不同频率、不同衰减速度的
正弦波叠在一起（"加法合成"），就能模仿音乐盒、钢琴、马林巴、钟琴等乐器。
这里用 numpy 一次算一整段数组，比一个一个采样地算快几百倍。

背景音乐是"自动作曲"的：每首曲子规定调式、速度、和弦进行和乐器，
旋律由固定种子的随机数生成，所以每次生成的曲子都一样。

文件只在第一次运行时生成，之后直接使用。改了声音的设计时，
把 SOUND_VERSION 加 1，就会重新生成。
"""

import wave
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

SOUND_VERSION = 2
EFFECT_RATE = 44100     # 音效的采样率
MUSIC_RATE = 24000      # 背景音乐的采样率（低一点，文件小一些）

# ---------------------------------------------------------------------------
# 音高
# ---------------------------------------------------------------------------

_SEMITONES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi(name):
    """音名转 MIDI 编号：C4 是 60，A4 是 69。支持升降号，比如 F#4、Bb3。"""
    letter, rest = name[0], name[1:]
    offset = 0
    while rest and rest[0] in "#b":
        offset += 1 if rest[0] == "#" else -1
        rest = rest[1:]
    return 12 * (int(rest) + 1) + _SEMITONES[letter] + offset


def frequency(midi_number):
    """MIDI 编号转频率：每高一个半音，频率乘以 2 的 1/12 次方。"""
    return 440.0 * 2 ** ((midi_number - 69) / 12)


# ---------------------------------------------------------------------------
# 乐器（加法合成）
# ---------------------------------------------------------------------------

def _times(duration, rate):
    return np.arange(int(duration * rate)) / rate


def _fade_edges(samples, rate, attack, release):
    """开头淡入、结尾淡出，避免"咔哒"声。"""
    count = len(samples)
    attack_n = min(count, max(1, int(attack * rate)))
    release_n = min(count, max(1, int(release * rate)))
    samples[:attack_n] *= np.linspace(0, 1, attack_n)
    samples[count - release_n:] *= np.linspace(1, 0, release_n)
    return samples


def _partials(freq, duration, rate, partials, attack=0.003, release=0.04):
    """
    叠加多个正弦波（泛音）。partials 是 [(频率倍数, 音量, 衰减速度), ...]。
    衰减速度越大，这个泛音消失得越快。
    """
    t = _times(duration, rate)
    out = np.zeros_like(t)
    for ratio, amplitude, decay in partials:
        f = freq * ratio
        if f >= rate * 0.45:          # 太高的泛音会失真，跳过
            continue
        out += amplitude * np.sin(2 * np.pi * f * t) * np.exp(-decay * t)
    return _fade_edges(out, rate, attack, release)


def music_box(freq, duration, rate):
    return _partials(freq, duration, rate,
                     [(1, 1.0, 2.2), (2, 0.30, 3.5), (3, 0.10, 5.0), (4.2, 0.12, 7.0)], attack=0.002)


def piano(freq, duration, rate):
    # 真实琴弦的泛音会比整数倍稍微高一点（非谐性），听起来更像钢琴
    stretch = 0.0004
    partials = [(k * np.sqrt(1 + stretch * k * k), 1 / k ** 1.4, 1.1 + 0.55 * k) for k in range(1, 9)]
    return _partials(freq, duration, rate, partials, attack=0.004, release=0.12)


def marimba(freq, duration, rate):
    return _partials(freq, duration, rate,
                     [(1, 1.0, 4.5), (3.93, 0.32, 11), (9.2, 0.08, 22)], attack=0.002)


def bell(freq, duration, rate):
    return _partials(freq, duration, rate,
                     [(1, 1.0, 1.0), (2.0, 0.45, 1.6), (2.76, 0.35, 2.2), (5.4, 0.16, 2.8), (8.93, 0.07, 3.6)],
                     attack=0.001)


def guitar(freq, duration, rate):
    # 拨弦：拨的位置靠近琴码，泛音按 sin(π·k·位置) 分配音量
    position = 0.22
    partials = [(k, abs(np.sin(np.pi * k * position)) / k, 1.4 + 0.9 * k) for k in range(1, 11)]
    return _partials(freq, duration, rate, partials, attack=0.002, release=0.08)


def flute(freq, duration, rate):
    """柔和的长笛：带一点颤音（音高轻微起伏），音量不怎么衰减。"""
    t = _times(duration, rate)
    vibrato = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(1, t / 0.4)
    phase = 2 * np.pi * freq * np.cumsum(vibrato) / rate
    out = (np.sin(phase) + 0.15 * np.sin(2 * phase) + 0.05 * np.sin(3 * phase)) * np.exp(-0.35 * t)
    return _fade_edges(out, rate, 0.06, 0.15)


def bass(freq, duration, rate):
    return _partials(freq, duration, rate, [(1, 1.0, 1.2), (2, 0.35, 2.0), (3, 0.12, 3.0)],
                     attack=0.01, release=0.1)


def pad(freq, duration, rate):
    """铺底的和声：几个稍微跑调的音叠在一起，慢慢进来、慢慢消失，像弦乐的背景。"""
    t = _times(duration, rate)
    out = np.zeros_like(t)
    for detune in (-0.004, 0.0, 0.004):
        for k in range(1, 6):
            out += np.sin(2 * np.pi * freq * k * (1 + detune) * t + k * detune * 300) / k
    out *= 1 + 0.08 * np.sin(2 * np.pi * 0.25 * t)
    return _fade_edges(out / 6, rate, min(0.6, duration / 3), min(0.8, duration / 3))


INSTRUMENTS = {
    "music_box": music_box, "piano": piano, "marimba": marimba, "bell": bell,
    "guitar": guitar, "flute": flute, "bass": bass, "pad": pad,
}


# ---------------------------------------------------------------------------
# 效果
# ---------------------------------------------------------------------------

def reverb(samples, rate, seconds=1.8, wet=0.25, seed=7):
    """
    混响：模拟声音在房间里来回反射。做法是和一段"逐渐变小的噪音"做卷积，
    卷积用快速傅里叶变换（FFT）计算。
    """
    count = int(seconds * rate)
    t = np.arange(count) / rate
    rng = np.random.default_rng(seed)
    impulse = rng.standard_normal(count) * np.exp(-6.9 * t / seconds)
    size = 1 << int(np.ceil(np.log2(len(samples) + count)))
    spectrum = np.fft.rfft(impulse, size)
    bins = np.fft.rfftfreq(size, 1 / rate)
    spectrum /= 1 + (bins / 3500) ** 2            # 让混响暗一点、柔和一点
    wet_signal = np.fft.irfft(np.fft.rfft(samples, size) * spectrum, size)[:len(samples) + count]
    wet_signal /= max(1e-9, np.abs(wet_signal).max())
    out = np.zeros(len(samples) + count)
    out[:len(samples)] = samples
    peak = max(1e-9, np.abs(samples).max())
    return out + wet * peak * wet_signal


def _finish(samples, peak=0.85):
    """统一音量，并用 tanh 柔和地压住过大的峰值。"""
    samples = samples / max(1e-9, np.abs(samples).max())
    return np.tanh(samples * 1.2) / np.tanh(1.2) * peak


def save_wav(samples, path, rate):
    data = (np.clip(samples, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(rate)
        file.writeframes(data.tobytes())


# ---------------------------------------------------------------------------
# 音效
# ---------------------------------------------------------------------------

# 填色时依次使用这些音高（五声音阶，怎么组合都好听），拖动时会像弹琴一样往上走
POP_NOTES = ["C5", "D5", "E5", "G5", "A5", "C6", "D6", "E6"]


def make_pop(note_name, rate=EFFECT_RATE):
    """
    "啵"的一声，像气泡弹开：音高在一瞬间从低滑到高，然后很快消失。
    音高往上滑会让声音听起来"Q弹"。
    """
    f = frequency(midi(note_name))
    t = _times(0.16, rate)
    sweep = f * (1 - 0.42 * np.exp(-t / 0.016))
    phase = 2 * np.pi * np.cumsum(sweep) / rate
    body = np.sin(phase) + 0.18 * np.sin(2 * phase)
    envelope = (1 - np.exp(-t / 0.0015)) * np.exp(-t / 0.055)
    click = np.random.default_rng(1).standard_normal(len(t)) * np.exp(-t / 0.0015)
    click = np.diff(click, prepend=0) * 0.04          # 很轻的"嗒"，增加手感
    return _finish(body * envelope + click, peak=0.7)


def make_wrong(rate=EFFECT_RATE):
    """填错颜色：低沉、软软的"噗"，音高往下掉，不刺耳。"""
    t = _times(0.18, rate)
    sweep = 210 * (1 + 0.3 * np.exp(-t / 0.03))
    phase = 2 * np.pi * np.cumsum(sweep) / rate
    body = np.sin(phase) + 0.25 * np.sin(3 * phase)
    envelope = (1 - np.exp(-t / 0.003)) * np.exp(-t / 0.06)
    return _finish(body * envelope, peak=0.55)


def make_color_done(rate=EFFECT_RATE):
    """一种颜色填完："叮叮叮叮"往上走的钟琴，再加一点闪光的尾音。"""
    total = _times(1.3, rate)
    out = np.zeros_like(total)
    for i, name in enumerate(("C6", "E6", "G6", "C7")):
        tone = bell(frequency(midi(name)), 0.9, rate)
        start = int(i * 0.07 * rate)
        out[start:start + len(tone)] += tone * (0.7 + 0.1 * i)
    rng = np.random.default_rng(3)
    for _ in range(6):
        tone = bell(frequency(midi(rng.choice(["G6", "A6", "C7", "D7", "E7"]))), 0.5, rate) * 0.18
        start = int(rng.uniform(0.25, 0.7) * rate)
        out[start:start + len(tone)] += tone[:len(out) - start]
    return _finish(reverb(out, rate, seconds=1.0, wet=0.2), peak=0.75)


def make_complete(rate=EFFECT_RATE):
    """整张图完成：一串上行琶音，接一个温暖的大和弦，最后是闪闪发光的下行小音符。"""
    out = np.zeros(int(3.4 * rate))

    def add(samples, start, gain):
        begin = int(start * rate)
        end = min(len(out), begin + len(samples))
        out[begin:end] += samples[:end - begin] * gain

    for i, name in enumerate(("C5", "E5", "G5", "C6", "E6", "G6")):
        add(marimba(frequency(midi(name)), 0.8, rate), i * 0.085, 0.6)
        add(bell(frequency(midi(name) + 12), 0.8, rate), i * 0.085, 0.15)
    for name in ("C4", "E4", "G4", "C5", "E5"):
        add(piano(frequency(midi(name)), 2.2, rate), 0.55, 0.35)
        add(pad(frequency(midi(name)), 2.4, rate), 0.5, 0.25)
    rng = np.random.default_rng(5)
    for i in range(10):
        name = rng.choice(["C7", "A6", "G6", "E6", "D6"])
        add(bell(frequency(midi(name)), 0.6, rate), 1.0 + i * 0.12, 0.12)
    return _finish(reverb(out, rate, seconds=1.6, wet=0.22), peak=0.8)


# ---------------------------------------------------------------------------
# 自动作曲
# ---------------------------------------------------------------------------

SCALES = {
    "major": [0, 2, 4, 5, 7, 9, 11],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
}

# 分解和弦的节奏型：一小节 8 个八分音符，数字是和弦里第几个音（0 根音，1 三音，2 五音，
# 3 高八度根音，4 高八度三音），None 是休止
ARPEGGIOS = {
    "rolling": [0, 1, 2, 3, 4, 3, 2, 1],
    "alberti": [0, 2, 1, 2, 0, 2, 1, 2],
    "pulse": [0, 2, 3, 2, 0, 2, 3, 2],
    "sparse": [0, None, 2, None, 3, None, 2, None],
    "waves": [0, 2, 4, 2, 1, 3, 4, 3],
}

# 旋律的节奏型：每个数字是一个音的长度（单位：拍），加起来是 4 拍
RHYTHMS = [
    [1, 1, 1, 1], [1.5, 0.5, 1, 1], [0.5, 0.5, 1, 2], [2, 2], [1, 0.5, 0.5, 2],
    [3, 1], [1, 1, 2], [0.5, 0.5, 0.5, 0.5, 2], [2, 1, 1],
]


@dataclass
class Track:
    name: str
    key: str                 # 主音，比如 "C4"
    scale: str
    bpm: int
    progression: list        # 和弦进行：音阶里的第几级（从 0 开始）
    lead: str                # 旋律乐器
    arp: str                 # 分解和弦乐器
    arp_pattern: str
    bars_per_chord: int = 1
    sevenths: bool = False   # 和弦加七音，听起来更爵士
    bass_walk: bool = False  # 低音按四分音符走动
    percussion: bool = False
    swing: float = 0.0       # 摇摆感：反拍的八分音符往后推一点
    wet: float = 0.25        # 混响多少
    seed: int = 1
    sections: list = field(default_factory=lambda: ["intro", "A", "A", "B", "B", "A", "outro"])


MUSIC_TRACKS = [
    Track("music_box", "C4", "major", 84, [0, 4, 5, 3], lead="music_box", arp="music_box",
          arp_pattern="rolling", seed=11),
    Track("rainy", "A3", "minor", 70, [0, 5, 2, 6], lead="piano", arp="piano",
          arp_pattern="alberti", wet=0.32, seed=23),
    Track("garden", "F3", "major", 100, [0, 3, 1, 4], lead="marimba", arp="guitar",
          arp_pattern="pulse", bass_walk=True, percussion=True, swing=0.1, seed=37),
    Track("starry", "D4", "dorian", 64, [0, 3], lead="flute", arp="bell", arp_pattern="sparse",
          bars_per_chord=2, wet=0.4, seed=41),
    Track("sunday", "G3", "major", 92, [0, 5, 1, 4], lead="piano", arp="guitar",
          arp_pattern="waves", sevenths=True, bass_walk=True, percussion=True, swing=0.15, seed=53),
]


def _chord(track, degree):
    """音阶第 degree 级上的和弦，返回相对主音的半音数列表（三和弦或七和弦）。"""
    scale = SCALES[track.scale]
    count = 4 if track.sevenths else 3
    tones = []
    for i in range(count):
        step = degree + 2 * i
        tones.append(scale[step % 7] + 12 * (step // 7))
    return tones


def _scale_notes(track, low, high):
    """主音附近 low 到 high（MIDI）之间所有属于音阶的音。"""
    root = midi(track.key)
    scale = SCALES[track.scale]
    return [n for n in range(low, high + 1) if (n - root) % 12 in scale]


def _melody(track, rng, chords, low, high):
    """
    为一段和弦生成旋律，返回 [(开始拍, 长度拍, MIDI)]。
    强拍用和弦里的音，弱拍沿着音阶一步一步走；每 4 小节的后两小节
    重复前两小节的节奏，听起来像一句"问"和一句"答"。
    """
    root = midi(track.key)
    scale_notes = _scale_notes(track, low, high)
    notes = []
    previous = scale_notes[len(scale_notes) // 2]
    bar_rhythms = []
    for bar, chord in enumerate(chords):
        if bar % 4 in (2, 3):
            rhythm = bar_rhythms[bar - 2]
        else:
            rhythm = RHYTHMS[rng.integers(len(RHYTHMS))]
        if bar % 4 == 3:
            rhythm = [2, 2] if rng.random() < 0.5 else [1, 3]   # 句尾放慢
        bar_rhythms.append(rhythm)
        pitch_classes = {c % 12 for c in chord}
        chord_notes = [n for n in scale_notes if (n - root) % 12 in pitch_classes]
        beat = 0.0
        for length in rhythm:
            if rng.random() < 0.08 and beat > 0:
                beat += length                     # 偶尔休止一下
                continue
            if beat == int(beat) or bar % 4 == 3:
                candidates = chord_notes
            else:
                index = scale_notes.index(min(scale_notes, key=lambda n: abs(n - previous)))
                step = rng.choice([-2, -1, 1, 1, 2])
                candidates = [scale_notes[max(0, min(len(scale_notes) - 1, index + step))]]
            target = previous + rng.integers(-4, 5)
            pitch = min(candidates, key=lambda n: abs(n - target))
            notes.append((bar * 4 + beat, length, pitch))
            previous = pitch
            beat += length
    return notes


def _shaker(rate, duration=0.05):
    t = _times(duration, rate)
    noise = np.random.default_rng(9).standard_normal(len(t))
    noise = np.diff(noise, prepend=0)              # 去掉低频，只留"沙沙"声
    return noise * np.exp(-t / 0.012) * 0.5


def _kick(rate):
    t = _times(0.25, rate)
    sweep = 110 * np.exp(-t / 0.05) + 45
    return np.sin(2 * np.pi * np.cumsum(sweep) / rate) * np.exp(-t / 0.08)


def compose(track, rate=MUSIC_RATE):
    """按照 Track 的设定生成一整首曲子，返回采样数组。"""
    rng = np.random.default_rng(track.seed)
    beat_seconds = 60 / track.bpm
    root = midi(track.key)

    # 把各段落展开成每小节的和弦
    cycle = []
    for degree in track.progression:
        cycle += [_chord(track, degree)] * track.bars_per_chord
    bars = []                                       # (段落名, 和弦)
    for section in track.sections:
        bars += [(section, chord) for chord in cycle]
    total_beats = len(bars) * 4
    out = np.zeros(int((total_beats * beat_seconds + 3) * rate))

    def add(samples, beat, gain):
        start = int(beat * beat_seconds * rate)
        end = min(len(out), start + len(samples))
        if start < len(out):
            out[start:end] += samples[:end - start] * gain

    def swung(beat):
        return beat + (track.swing if (beat * 2) % 2 == 1 else 0)

    lead = INSTRUMENTS[track.lead]
    arp = INSTRUMENTS[track.arp]
    pattern = ARPEGGIOS[track.arp_pattern]

    # 旋律：A 段和 B 段各生成一次，同一段落重复出现时用同一段旋律
    melodies = {}
    for section, register in (("A", (root + 12, root + 24)), ("B", (root + 15, root + 27))):
        melodies[section] = _melody(track, rng, cycle * 2, *register)

    for bar, (section, chord) in enumerate(bars):
        bar_beat = bar * 4

        # 铺底和声
        for tone in chord[:3]:
            add(pad(frequency(root + tone), 4 * beat_seconds + 0.6, rate), bar_beat, 0.10)

        # 分解和弦（结尾段落渐弱）
        arp_gain = 0.22 if section != "outro" else 0.22 * (1 - (bar % len(cycle)) / len(cycle) * 0.7)
        chord_tones = chord[:3] + [chord[0] + 12, chord[1] + 12]
        for i, index in enumerate(pattern):
            if index is None:
                continue
            note = root + chord_tones[index]
            add(arp(frequency(note), beat_seconds * 1.6, rate), swung(bar_beat + i / 2), arp_gain)

        # 低音
        bass_root = root - 12 + chord[0]
        while bass_root > root - 5:
            bass_root -= 12
        if track.bass_walk:
            for i, tone in enumerate((0, chord[1] - chord[0], chord[2] - chord[0], chord[1] - chord[0])):
                add(bass(frequency(bass_root + tone), beat_seconds * 1.1, rate), bar_beat + i, 0.3)
        else:
            add(bass(frequency(bass_root), beat_seconds * 2.2, rate), bar_beat, 0.3)
            add(bass(frequency(bass_root + chord[2] - chord[0]), beat_seconds * 2.2, rate), bar_beat + 2, 0.22)

        # 轻打击乐
        if track.percussion and section not in ("intro", "outro"):
            for i in range(8):
                add(_shaker(rate), swung(bar_beat + i / 2), 0.06 if i % 2 == 0 else 0.1)
            add(_kick(rate), bar_beat, 0.25)
            add(_kick(rate), bar_beat + 2, 0.18)

        # 旋律
        if section in melodies:
            offset_bar = _bar_in_section(bars, bar) % (len(cycle) * 2)
            for start, length, pitch in melodies[section]:
                if offset_bar * 4 <= start < (offset_bar + 1) * 4:
                    add(lead(frequency(pitch), length * beat_seconds + 0.4, rate),
                        swung(bar_beat + start - offset_bar * 4), 0.36)

    out = reverb(out, rate, seconds=2.2, wet=track.wet, seed=track.seed)
    fade_in = int(1.5 * rate)
    out[:fade_in] *= np.linspace(0, 1, fade_in)
    fade_out = int(4 * rate)
    out[-fade_out:] *= np.linspace(1, 0, fade_out) ** 2
    return _finish(out, peak=0.8)


def _bar_in_section(bars, bar):
    """这一小节是所在段落（连续相同段落名的一串小节）里的第几小节。"""
    section = bars[bar][0]
    start = bar
    while start > 0 and bars[start - 1][0] == section:
        start -= 1
    return bar - start


# ---------------------------------------------------------------------------
# 生成文件
# ---------------------------------------------------------------------------

def remove_old_sounds(base):
    """删掉旧版本的声音文件夹。"""
    import shutil
    for folder in Path(base).glob("sounds*"):
        if folder.is_dir() and folder.name != f"sounds-v{SOUND_VERSION}":
            shutil.rmtree(folder, ignore_errors=True)


def sound_folder(base):
    """声音文件放在 base/sounds-v<版本> 里。"""
    folder = Path(base) / f"sounds-v{SOUND_VERSION}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def ensure_effects(base):
    """确保音效文件都已生成，返回 {"pop": [路径...], "wrong": 路径, ...}。"""
    folder = sound_folder(base)
    paths = {"pop": []}
    for name in POP_NOTES:
        path = folder / f"pop_{name}.wav"
        if not path.exists():
            save_wav(make_pop(name), path, EFFECT_RATE)
        paths["pop"].append(str(path))
    for name, make in (("wrong", make_wrong), ("color_done", make_color_done), ("complete", make_complete)):
        path = folder / f"{name}.wav"
        if not path.exists():
            save_wav(make(), path, EFFECT_RATE)
        paths[name] = str(path)
    return paths


def ensure_music(base, track):
    """确保某首背景音乐已生成，返回文件路径。"""
    path = sound_folder(base) / f"music_{track.name}.wav"
    if not path.exists():
        save_wav(compose(track), path, MUSIC_RATE)
    return str(path)
