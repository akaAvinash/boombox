import os
import pygame
import tkinter as tk
from tkinter import filedialog, ttk
import cv2
from threading import Thread
from PIL import Image, ImageTk
import time

class MediaPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Video/Audio Player")
        self.root.geometry("800x600")
        self.root.resizable(False, False)

        # Variables
        self.playing = False
        self.file_path = ""
        self.media_type = None
        self.video_thread = None
        self.paused = False
        self.current_position = 0  # For tracking current position in video/audio
        self.total_duration = 0  # Total duration of media

        # Initialize pygame mixer for audio
        pygame.mixer.init()

        # UI Setup
        self.create_ui()

    def create_ui(self):
        # File Selection
        ttk.Button(self.root, text="Open File", command=self.open_file).pack(pady=10)

        # Video Panel
        self.video_panel = tk.Label(self.root, bg="black")
        self.video_panel.pack(padx=10, pady=10, fill="both", expand=True)

        # Control Buttons
        control_frame = tk.Frame(self.root)
        control_frame.pack()

        self.play_button = ttk.Button(control_frame, text="Play", command=self.play_pause)
        self.play_button.pack(side="left", padx=5)

        ttk.Button(control_frame, text="<< 10s", command=self.seek_backward).pack(side="left", padx=5)
        ttk.Button(control_frame, text="10s >>", command=self.seek_forward).pack(side="left", padx=5)

        # Timeline (Scale)
        self.timeline = tk.Scale(self.root, from_=0, to=100, orient="horizontal", length=600, command=self.seek_by_timeline)
        self.timeline.pack(pady=10)

        # Elapsed Time Label
        self.elapsed_time_label = tk.Label(self.root, text="0:00 / 0:00")
        self.elapsed_time_label.pack()

    def open_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=(("Media files", "*.mp4;*.mp3"),))
        if not self.file_path:
            return

        self.media_type = "video" if self.file_path.endswith(".mp4") else "audio"

        if self.media_type == "video":
            if self.video_thread and self.video_thread.is_alive():
                self.playing = False
                time.sleep(1)
            self.play_video()
        elif self.media_type == "audio":
            pygame.mixer.music.load(self.file_path)
            pygame.mixer.music.play()
            self.playing = True
            self.total_duration = pygame.mixer.Sound(self.file_path).get_length()  # Get audio duration
            self.timeline.config(to=self.total_duration)
            self.update_play_button()

    def play_pause(self):
        if self.media_type == "video":
            self.paused = not self.paused
        elif self.media_type == "audio":
            if self.playing:
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()
            self.playing = not self.playing
        self.update_play_button()

    def update_play_button(self):
        self.play_button.config(text="Pause" if self.playing else "Play")

    def seek_backward(self):
        if self.media_type == "audio":
            pos = pygame.mixer.music.get_pos() / 1000.0
            pygame.mixer.music.set_pos(max(0, pos - 10))
        elif self.media_type == "video":
            self.current_position -= 10
            self.current_position = max(0, self.current_position)
            self.timeline.set(self.current_position)
            self.update_video_position()

    def seek_forward(self):
        if self.media_type == "audio":
            pos = pygame.mixer.music.get_pos() / 1000.0
            pygame.mixer.music.set_pos(min(self.total_duration, pos + 10))
        elif self.media_type == "video":
            self.current_position += 10
            self.current_position = min(self.total_duration, self.current_position)
            self.timeline.set(self.current_position)
            self.update_video_position()

    def seek_by_timeline(self, value):
        value = float(value)
        if self.media_type == "audio":
            pygame.mixer.music.set_pos(value)
        elif self.media_type == "video":
            self.current_position = value
            self.update_video_position()

    def update_elapsed_time(self):
        elapsed_time = time.strftime('%M:%S', time.gmtime(self.current_position))
        total_time = time.strftime('%M:%S', time.gmtime(self.total_duration))
        self.elapsed_time_label.config(text=f"{elapsed_time} / {total_time}")

    def play_video(self):
        self.playing = True
        self.video_thread = Thread(target=self._play_video)
        self.video_thread.start()

    def _play_video(self):
        cap = cv2.VideoCapture(self.file_path)
        self.total_duration = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000  # Total video duration
        self.timeline.config(to=self.total_duration)
        while cap.isOpened() and self.playing:
            if self.paused:
                time.sleep(0.1)
                continue

            ret, frame = cap.read()
            if not ret:
                break

            # Resize frame to fit window
            frame = cv2.resize(frame, (800, 450))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Convert frame to ImageTk format
            img = ImageTk.PhotoImage(Image.fromarray(frame))

            # Display frame in video panel
            self.video_panel.config(image=img)
            self.video_panel.image = img

            # Update current position and timeline
            self.current_position = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
            self.timeline.set(self.current_position)
            self.update_elapsed_time()

            # Delay for video playback speed
            time.sleep(1 / cap.get(cv2.CAP_PROP_FPS))

        cap.release()
        self.playing = False

# Main Execution
if __name__ == "__main__":
    root = tk.Tk()
    app = MediaPlayer(root)
    root.mainloop()
