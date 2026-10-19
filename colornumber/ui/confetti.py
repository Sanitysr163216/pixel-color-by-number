"""
彩带庆祝效果：一堆彩色小方块从上往下飘落、旋转。
"""

import math
import random

from kivy.clock import Clock
from kivy.graphics import Color, PopMatrix, PushMatrix, Rectangle, Rotate
from kivy.uix.widget import Widget

CONFETTI_COLORS = [
    (0.95, 0.35, 0.40), (0.98, 0.75, 0.25), (0.35, 0.75, 0.45),
    (0.30, 0.55, 0.95), (0.70, 0.45, 0.90), (1.00, 0.55, 0.75),
]


class Confetti(Widget):
    """盖在画面上的彩带层，不挡鼠标。"""

    def burst(self, count=140, duration=3.5):
        self.canvas.clear()
        self._pieces = []
        with self.canvas:
            for _ in range(count):
                Color(*random.choice(CONFETTI_COLORS), 1)
                piece = {
                    "x": self.x + random.uniform(0, self.width),
                    "y": self.top + random.uniform(0, self.height * 0.5),
                    "vx": random.uniform(-40, 40),
                    "vy": random.uniform(-260, -120),
                    "spin": random.uniform(-360, 360),
                    "angle": random.uniform(0, 360),
                    "wobble": random.uniform(0, math.tau),
                    "size": (random.uniform(6, 12), random.uniform(10, 18)),
                }
                PushMatrix()
                piece["rotate"] = Rotate(angle=piece["angle"], origin=(piece["x"], piece["y"]))
                piece["rect"] = Rectangle(size=piece["size"])
                PopMatrix()
                self._pieces.append(piece)
        self._time = 0.0
        self._duration = duration
        Clock.unschedule(self._step)
        Clock.schedule_interval(self._step, 1 / 60)

    def _step(self, dt):
        self._time += dt
        for piece in self._pieces:
            piece["wobble"] += dt * 4
            piece["x"] += (piece["vx"] + math.sin(piece["wobble"]) * 40) * dt
            piece["y"] += piece["vy"] * dt
            piece["angle"] += piece["spin"] * dt
            width, height = piece["size"]
            piece["rect"].pos = (piece["x"] - width / 2, piece["y"] - height / 2)
            piece["rotate"].origin = (piece["x"], piece["y"])
            piece["rotate"].angle = piece["angle"]
        if self._time > self._duration:
            self.canvas.clear()
            return False
        return True

    def on_touch_down(self, touch):
        return False
