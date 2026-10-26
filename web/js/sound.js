// 音效：用浏览器的 Web Audio 现场合成，不用下载声音文件。
// 和桌面版一样：拖着填色时"啵"的音一个比一个高（五声音阶），填错是低一点的软声音。

const PENTATONIC = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5, 1174.66, 1318.51];   // C5 D5 E5 G5 A5 C6 D6 E6

let context = null;
let enabled = true;
let popIndex = 0;
let lastPop = 0;

export function setSoundEnabled(value) {
  enabled = value;
}

// 手机浏览器要求声音必须在用户点了屏幕以后才能开始，所以第一次触摸时再创建
export function unlockAudio() {
  if (!context) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    context = new AudioContext();
  }
  if (context.state === "suspended") context.resume();
}

function tone(frequency, { start = 0, duration = 0.12, volume = 0.18, type = "sine", slide = 0.6 } = {}) {
  if (!enabled || !context) return;
  const time = context.currentTime + start;
  const oscillator = context.createOscillator();
  const gain = context.createGain();
  oscillator.type = type;
  oscillator.frequency.setValueAtTime(frequency * 1.25, time);
  oscillator.frequency.exponentialRampToValueAtTime(frequency * slide + frequency * (1 - slide), time + 0.04);
  gain.gain.setValueAtTime(0.0001, time);
  gain.gain.exponentialRampToValueAtTime(volume, time + 0.008);
  gain.gain.exponentialRampToValueAtTime(0.0001, time + duration);
  oscillator.connect(gain).connect(context.destination);
  oscillator.start(time);
  oscillator.stop(time + duration + 0.02);
}

export function startStroke() {
  popIndex = Math.floor(Math.random() * 4);
}

export function pop() {
  const now = performance.now();
  if (now - lastPop < 45) return;          // 拖得很快时不要响成一片
  lastPop = now;
  tone(PENTATONIC[popIndex % PENTATONIC.length]);
  popIndex = Math.min(popIndex + 1, PENTATONIC.length - 1);
}

export function wrong() {
  tone(196, { duration: 0.16, volume: 0.12, type: "triangle", slide: 0.3 });
}

export function colorDone() {
  tone(783.99, { duration: 0.18 });
  tone(1046.5, { start: 0.09, duration: 0.25 });
}

export function complete() {
  [523.25, 659.25, 783.99, 1046.5, 1318.51].forEach((frequency, index) => {
    tone(frequency, { start: index * 0.09, duration: 0.35, volume: 0.15 });
  });
}
