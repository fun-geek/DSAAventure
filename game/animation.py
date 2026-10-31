"""Tiny frame animator for sprite walk cycles."""


class Animator:
    CYCLE = (1, 0, 2, 0)  # frame indices: 0 = idle, 1/2 = left/right step

    def __init__(self, fps: float = 8.0):
        self.fps = fps
        self.t = 0.0

    def update(self, dt: float, moving: bool, speed_mult: float = 1.0) -> None:
        self.t = self.t + dt * speed_mult if moving else 0.0

    @property
    def frame(self) -> int:
        return self.CYCLE[int(self.t * self.fps) % len(self.CYCLE)] if self.t else 0
