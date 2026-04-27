from tkinter import ttk
from PIL import Image, ImageTk, ImageSequence
import cv2
import tkinter as tk

# Class that handles all GIF animations
# Created by Adam Wikström - 2026-04-20
class AnimatedGIF:
    def __init__(self, canvas, path, x, y, size=None, anchor="center"):
        self.canvas = canvas
        self.gif = Image.open(path)

        self.frames = []
        self.durations = []

        for frame in ImageSequence.Iterator(self.gif):
            frame = frame.copy()

            if size:
                frame = frame.resize(size, Image.LANCZOS)

            self.frames.append(ImageTk.PhotoImage(frame))
            self.durations.append(frame.info.get("duration", 50))

        self.index = 0
        self.running = True
        self.speed = 1.0  # 1.0 = normal speed

        self.image_item = canvas.create_image(x, y, image=self.frames[0], anchor=anchor)

        # prevent garbage collection
        if not hasattr(canvas, "_gif_refs"):
            canvas._gif_refs = []
        canvas._gif_refs.append(self.frames)

        self._job = None
        self._animate()

    def _animate(self):
        if not self.running:
            return

        self.index = (self.index + 1) % len(self.frames)
        self.canvas.itemconfig(self.image_item, image=self.frames[self.index])

        delay = int(self.durations[self.index] / self.speed)
        self._job = self.canvas.after(delay, self._animate)

    def pause(self):
        self.running = False
        if self._job:
            self.canvas.after_cancel(self._job)
            self._job = None

    def resume(self):
        if not self.running:
            self.running = True
            self._animate()

    def stop(self):
        self.pause()
        self.index = 0
        self.canvas.itemconfig(self.image_item, image=self.frames[0])

    def set_speed(self, speed):
        """speed > 1 = faster, speed < 1 = slower"""
        self.speed = max(0.1, speed)

    def delete(self):
        self.pause()
        self.canvas.delete(self.image_item)

# Class that handles video playing
# Created by Adam Wikström - 2026-04-20
class VideoPlayer:
    def __init__(self, canvas, path, x, y, size=None):
        self.canvas = canvas
        self.cap = cv2.VideoCapture(path)

        self.x = x
        self.y = y
        self.size = size

        self.running = True

        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        self.delay = int(1000 / self.fps)

        self.image_item = None
        self.frame = None
        self._job = None

        self._read_frame()
        self._update()

    def _read_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if self.size:
            frame = cv2.resize(frame, self.size)

        self.frame = ImageTk.PhotoImage(Image.fromarray(frame))

    def _update(self):
        if not self.running:
            return

        if self.image_item is None:
            self.image_item = self.canvas.create_image(
                self.x, self.y, image=self.frame, anchor="center"
            )
            self.canvas._video_ref = self.frame  # prevent GC
        else:
            self.canvas.itemconfig(self.image_item, image=self.frame)
            self.canvas._video_ref = self.frame

        self._read_frame()

        delay = int(self.delay)
        self._job = self.canvas.after(delay, self._update)

    def pause(self):
        self.running = False
        if self._job:
            self.canvas.after_cancel(self._job)
            self._job = None

    def resume(self):
        if not self.running:
            self.running = True
            self._update()

    def stop(self):
        self.pause()
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def delete(self):
        self.pause()
        self.cap.release()
        if self.image_item:
            self.canvas.delete(self.image_item)

# Class that handles the progress bar
# Created by Adam Wikström - 2026-04-27
class CanvasProgressBar:
    def __init__(self, canvas, x, y, width=370, height=20, max_value=100,
                 bg="#151414", fg="#00EE00", outline="white"):

        self.canvas = canvas
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.max_value = max_value

        self.value = 0

        # Background bar
        self.bg_rect = canvas.create_rectangle(
            x, y,
            x + width, y + height,
            fill=bg,
            outline=outline
        )

        # Foreground (progress fill)
        self.fg_rect = canvas.create_rectangle(
            x, y,
            x, y + height,
            fill=fg,
            outline=""
        )

    def set(self, value):
        self.value = max(0, min(self.max_value, value))
        fill_width = (self.value / self.max_value) * self.width

        self.canvas.coords(
            self.fg_rect,
            self.x, self.y,
            self.x + fill_width, self.y + self.height
        )

    def step(self, amount=1):
        self.set(self.value + amount)

    def destroy(self):
        self.canvas.delete(self.bg_rect)
        self.canvas.delete(self.fg_rect)



