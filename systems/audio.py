"""Procedural UI sound effects (no asset files needed). Degrades silently
when no audio device is available."""
import array
import math

import pygame


class Audio:
    def __init__(self, volume: float = 0.7):
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.volume = volume
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(22050, -16, 1, 512, allowedchanges=0)
            self.sounds = {
                "move": self._tone(660, duration=0.04),
                "select": self._tone(880, duration=0.09),
                "back": self._tone(440, duration=0.08),
                "coin": self._tone(988, 1319, duration=0.06),
                "chest": self._tone(523, 659, 784, 1047, duration=0.09),
                "levelup": self._tone(523, 659, 784, 1047, 1319, duration=0.1),
                "talk": self._tone(300, duration=0.03),
            }
        except pygame.error:
            self.sounds = {}
        self.set_volume(volume)

    @staticmethod
    def _tone(*freqs: int, duration: float) -> pygame.mixer.Sound:
        """Square-wave blips, one per frequency, played back to back."""
        rate = pygame.mixer.get_init()[0]
        n = int(rate * duration)
        samples = array.array("h")
        for freq in freqs:
            samples.extend(
                int(7000 * (1 - i / n) * (1 if math.sin(2 * math.pi * freq * i / rate) >= 0 else -1))
                for i in range(n))
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def set_volume(self, volume: float) -> None:
        self.volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.volume)

    def play(self, name: str) -> None:
        sound = self.sounds.get(name)
        if sound and self.volume > 0:
            sound.play()
