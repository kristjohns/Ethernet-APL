"""Scene base class shared by every chapter."""

from __future__ import annotations

from manim import *  # noqa: F401,F403

from .narration import NarratedScene
from .style import APL, BG, MUTED, TEXT, T
from .widgets import chapter_title, corner_tag


class APLScene(NarratedScene, MovingCameraScene):
    """Narrated scene with a moving camera and a few house helpers."""

    def setup(self):
        super().setup()
        self.clock = ValueTracker(0)
        self.clock.add_updater(lambda m, dt: m.increment_value(dt))
        self.add(self.clock)
        self.tag = None

    @property
    def t(self) -> float:
        return self.clock.get_value()

    def chapter(self, number, title, subtitle=None, color=APL, hold=0.6, voice_text=None):
        """Animated chapter card; leaves a small corner tag behind."""
        self._chapters.append({"time": self.time, "title": f"{number:02d} · {title}"})
        card = chapter_title(number, title, subtitle, color=color)
        num, bar, words = card
        self.play(
            FadeIn(num, shift=RIGHT * 0.4),
            GrowFromCenter(bar),
            LaggedStart(*[FadeIn(w, shift=UP * 0.15) for w in words], lag_ratio=0.2),
            run_time=1.2,
        )
        if voice_text:
            with self.voice(voice_text):
                pass
        else:
            self.wait(hold)
        new_tag = corner_tag(f"{number:02d} · {title}", color=color)
        anims = [ReplacementTransform(card, new_tag)]
        if self.tag is not None:
            anims.append(FadeOut(self.tag))
        self.play(*anims, run_time=0.9)
        self.tag = new_tag
        return new_tag

    def clear(self, keep=(), run_time=0.7, shift=ORIGIN):
        """Fade out everything except ``keep`` (and the clock / corner tag)."""
        keep = set(keep) | {self.clock}
        if self.tag is not None:
            keep.add(self.tag)
        mobs = [m for m in self.mobjects if m not in keep]
        if mobs:
            self.play(*[FadeOut(m, shift=shift) for m in mobs], run_time=run_time)
