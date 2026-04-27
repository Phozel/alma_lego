import os
import sys
import tkinter as tk
from tkinter import ttk

import threading
from playsound3 import playsound

import keyboard
import numpy as np
import serial
from PIL import Image, ImageTk
from astropy.utils import state
import time

import AT_functions
from AT_functions import AnimatedGIF, VideoPlayer, CanvasProgressBar
from functions import functions2run
from functions import vriCalc
from functions.vriCalc import observationManager
import matplotlib.cm as cm


# Class that creates and populates a UI for LEGO ALMA
#
# Created by Adam Wikström - 2026-04-21
class ALMA_UI:
    window = None
    canvas = None
    view_occupied = False
    views = ["video_view",
             "guide_view",
             "selection_view",
             "observation_view",
             "restart_view"]
    current_view_index = 0
    current_view = None

    VIDEO = "video_view"
    SELECTION = "selection_view"
    GUIDE = "guide_view"
    OBSERVATION = "observation_view"
    RESTART = "restart_view"

    BUTTON_PRESS = False
    ANTENNAS_EMPTY = False
    ANTENNAS_ACTIVE = False
    STATE_CHANGE = False

    def __init__(self):
        self.serial_paused = False
        self.window = tk.Tk()
        self.window.geometry("1920x1080")
        self.window.configure(bg="#000000")
        self.window.title("LEGO ALMA - Adam & Tarek")

        self.canvas = tk.Canvas(
            self.window,
            bg="#000000",
            width=1920,
            height=1080,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        self.canvas.place(x=0, y=0)
        self.window.bind_all("q", self.__close_window)
        self.window.bind_all("n", self.__next_view)
        self.window.bind_all("p", self.__previous_view)

        self.window.bind_all("<Any-KeyPress>", self.reset_idle_timer)
        self.window.bind_all("<Any-Button>", self.reset_idle_timer)

        self.idle_timeout_ms = 10 * 60 * 1000 # 10 minutes for timeout in ms
        self.idle_job = None
        self.last_state = None
        self.state = "video_view"

        self.click_sound_path = self.__load_asset("audio/click.mp3")
        self.antenna_state = functions2run.get_attenas_string()
        self.button_state = functions2run.get_buttons_inp()
        self.max_antennas = 42
        self.current_antennas = 0
        self.state_counter = 0

        self.view_switching = False

        try:
            self.ser = functions2run.getserialinterface()
        except:
            self.ser = None

        self.__start()

    def __load_asset(self, path):
        base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        assets = os.path.join(base, "AT_assets")
        return os.path.join(assets, path)

    def __start(self):
        self.change_view("observation_view")

        self.start_serial_loop()

        self.reset_idle_timer()

        self.window.resizable(False, False)
        self.window.mainloop()

    # Method that switches the contents of the window to select preset views
    def change_view(self, view_name):
        self.view_switching = True
        self.serial_paused = True

        if view_name == "observation_view":
            self.state_counter = 0

        self.canvas.delete("all")
        self.play_click_sound()

        self.current_view = view_name
        self.state = view_name

        match view_name:
            case "video_view":
                self.__video_view()
            case "observation_view":
                self.__observation_view()
            case "guide_view":
                self.__guide_view()
            case "restart_view":
                self.__restart_view()
            case "selection_view":
                self.__selection_view()

        self.serial_paused = False
        self.view_switching = False

    # Method that creates the content for the video view
    def __video_view(self):
        video = VideoPlayer(self.canvas, "AT_assets\\video\\ALMA-WSU-9_2.mp4", 960, 499, size=(1703, 958))
        self.canvas.create_rectangle(262, 949, 1659, 1080,
                                fill='#eee9e9',
                                outline="#eeb005",
                                width="5.0",
                                dash=(30, 10))
        self.canvas.create_text(
            298,
            978,
            anchor="nw",
            text="Tryck på valfri knapp nedan för att starta",
            fill="#141414",
            font=("Inter", 60 * -1)
        )
        self.canvas.create_oval(1523, 961, 1628, 1066, fill="#EFB005", outline="")
        self.view_occupied = True

    # Method that creates the content for the selection view
    def __selection_view(self):
        # Galaxy
        self.canvas.create_text(
            311,
            805,
            anchor="nw",
            text="Galax",
            fill="#f2ab6d",
            font=("Inter", 32 * -1)
        )

        self.canvas.create_rectangle(234, 433, 554, 775, fill='#000000', outline="#fff9f9", width="2.0")
        img_8 = Image.open(self.__load_asset("images/galaxy_img/Galaxy 43.png"))
        img_8 = img_8.resize((312, 312), Image.LANCZOS)  # <- new size here
        galaxy_img = ImageTk.PhotoImage(img_8)
        self.canvas.create_image(394, 604, image=galaxy_img)
        self.canvas.galaxy_img = galaxy_img  # keep reference

        # Protoplanetary Disc
        self.canvas.create_text(
            632,
            796,
            anchor="nw",
            text="Protoplanetär Skiva",
            fill="#f2ab6d",
            font=("Inter", 32 * -1)
        )

        self.canvas.create_rectangle(609, 433, 929, 775, fill='#000000', outline="#fff9f9", width="2.0")
        img_9 = Image.open(self.__load_asset("images\\disc_img\\Disk_43.png"))
        img_9 = img_9.resize((312, 312), Image.LANCZOS)  # <- new size here
        disc_img = ImageTk.PhotoImage(img_9)
        self.canvas.create_image(769, 604, image=disc_img)
        self.canvas.disc_img = disc_img

        self.canvas.create_text(
            1072,
            796,
            anchor="nw",
            text="Stjärna",
            fill="#f2ab6d",
            font=("Inter", 32 * -1)
        )

        self.canvas.create_rectangle(983, 433, 1303, 775, fill='#000000', outline="#fff9f9", width="2.0")
        img_10 = Image.open(self.__load_asset("images\\star_img\\star_43.png"))
        img_10 = img_10.resize((312, 312), Image.LANCZOS)  # <- new size here
        star_img = ImageTk.PhotoImage(img_10)
        self.canvas.create_image(1143, 604, image=star_img)
        self.canvas.star_img = star_img

        self.canvas.create_text(
            1346,
            796,
            anchor="nw",
            text="Jetstråle",
            fill="#f2ab6d",
            font=("Inter", 32 * -1)
        )

        self.canvas.create_rectangle(1357, 433, 1677, 775, fill='#000000', outline="#fff9f9", width="2.0")
        img_11 = Image.open(self.__load_asset("images\\jet_img\\Jet_43.png"))
        img_11 = img_11.resize((312, 312), Image.LANCZOS)  # <- new size here
        jet_img = ImageTk.PhotoImage(img_11)
        self.canvas.create_image(1517, 604, image=jet_img)
        self.canvas.jet_img = jet_img

        self.canvas.create_text(
            240,
            152,
            anchor="nw",
            text="Välj vad ni vill se via knapparna \ntill vänster",
            fill="#f2ab6d",
            font=("Inter", 96 * -1),
        )

        arrow_pos = [105, 226, 339, 463]
        arrow_images = []
        for i in range(4):
            temp_image = Image.open(self.__load_asset("gifs\\Arrow_blink.gif"))
            temp_image = temp_image.convert("RGBA")
            temp_image = temp_image.resize((184, 130), Image.LANCZOS)  # <- new size here
            temp_image = temp_image.rotate(76, expand=True)
            arrow_img = ImageTk.PhotoImage(temp_image)
            self.canvas.create_image(arrow_pos[i], 975, image=arrow_img)
            arrow_images.append(arrow_img)

        self.view_occupied = True

    # Method that creates the content for the guide view
    def __guide_view(self):
        self.canvas.create_text(
            260,
            122,
            anchor="nw",
            text="Sätt antenner på de vita brickorna",
            fill="#f2ab6d",
            font=("Inter", 96 * -1)
        )

        AnimatedGIF(self.canvas,
                    "AT_assets\\gifs\\placing-antennas.gif",
                    959, 729,
                    size=(1279, 904))  # Added 2026-04-20 - Adam W
        self.view_occupied = True

    # Method that creates the content for the observation view
    def __observation_view(self):

        # Selected object illustration rectangle
        self.canvas.create_rectangle(269, 63, 528, 324, fill='#000000', outline="#ffffff", width="3.0")
        # Information/Guide GIF rectangle
        #self.canvas.create_rectangle(156, 670, 641, 1013, fill='#000000', outline="#ffffff", width="3.0")
        # Observation Rectangle
        self.canvas.create_rectangle(794, 63, 1744, 1013, fill='#141414', outline="#ffffff", width="3.0")

        # place_gif = AnimatedGIF(self.canvas,
        #             "AT_assets/gifs/placing-antennas.gif",
        #             398, 843,
        #             size=(449, 343))

        spread_gather_gif = AnimatedGIF(self.canvas,
                                        "AT_assets\\gifs\\spread_and_gather_antennas-updated.gif",
                                        415, 843,
                                        size=(449, 343))
        spread_gather_gif.set_speed(1.3)

        # image_5 = tk.PhotoImage(file=load_asset("None"))

        # canvas.create_image(398, 842, image=image_5)

        # image_6 = tk.PhotoImage(file=load_asset("None"))

        # canvas.create_image(398, 843, image=image_6)

        image_7 = Image.open(self.__load_asset("images/antenna icon 1.png"))
        image_7 = image_7.resize((56, 66), Image.LANCZOS)  # <- new size here
        self.canvas.antenna_img = ImageTk.PhotoImage(image_7)
        self.canvas.create_image(1073, 949, image=self.canvas.antenna_img)

        self.antenna_text_id = self.canvas.create_text(
            920,
            930,
            text=f"0/42",
            fill="#ffffff",
            font=("Inter", 40 * -1),
            anchor="nw"
        )

        self.canvas.itemconfig(self.antenna_text_id, text=f"{self.current_antennas}/{self.max_antennas}")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Custom.Horizontal.TProgressbar",
                        troughcolor="#151414",  # match window bg
                        background="#00EE00",  # progress fill color
                        bordercolor="white",
                        lightcolor="green",
                        darkcolor="green")

        self.progress_bar = CanvasProgressBar(
            self.canvas,
            x=1155,
            y=950,
            width=370,
            height=20,
            max_value=1
        )

        self.progress_bar.set(self.current_antennas/self.max_antennas)

        self.view_occupied = True

    # Method that creates the content for the restart view
    def __restart_view(self):
        self.canvas.create_text(
            357,
            65,
            anchor="nw",
            text="   Flytta ALLA antenner till \ninhägnaden för att börja om",
            fill="#f2ab6d",
            font=("Inter", 96 * -1)
        )

        AnimatedGIF(self.canvas,
                    "AT_assets\\gifs\\remove-antennas.gif",
                    959, 644,
                    size=(1455, 1028))  # Added 2026-04-20 - Adam W
        self.view_occupied = True

    # Method that creates the observation that is shown in the observation view
    def create_observation(self, state):
        # Put this as its own method/whatever DONE
        # declare following outside loop ser=functions2run.getserialinterface() DONE
        # Change None to ser DONE
        # Loop the code DONE
        # button and antenna input in functions2run, create some way to change them for testing purposes
        if self.current_view == "observation_view":

            bit_pos1, bit_pos2, buttons_config, buttons_image, ant_pos, xx_antpos, yy_antpos, singledish, fller = state
            # bit_pos1, bit_pos2, buttons_config, buttons_image, ant_pos, xx_antpos, yy_antpos, singledish, fller = functions2run.waitforserialchange(
            #     None, IsThereArdruino=False)
            print("ant", ant_pos)
            print("bit1", bit_pos1)
            print("bit2", bit_pos2)
            imagefile, pixel_scale, integration_time, hourangle, \
                hourangle_start, hourangle_end = \
                functions2run.select_model_and_hourangle(bit_pos2, buttons_config, buttons_image)

            functions2run.write_alma_config_file(ant_pos)
            obsMan = observationManager(verbose=False, debug=True)
            obsMan.get_available_arrays()
            obsMan.select_array('ALMA_Custom-lego-alma', haStart=hourangle_start, haEnd=hourangle_end, sampRate_s=300)
            obsMan.get_selected_arrays()
            obsMan.set_obs_parms(3e5, -40)
            obsMan.calc_uvcoverage()
            obsMan.load_model_image(imagefile)
            obsMan.set_pixscale(pixel_scale)
            obsMan.invert_model()
            obsMan.grid_uvcoverage()
            obsMan.calc_beam()
            obsMan.invert_observation()
            data = np.real(obsMan.obsImgArr)
            norm_data = data / np.max(data)
            colored_data = cm.inferno(norm_data)
            colored_data = (colored_data[:, :, :3] * 255).astype(np.uint8)
            data_img = Image.fromarray(colored_data)

            if hasattr(self, "observation_img_id"):
                try:
                    self.canvas.delete(self.observation_img_id)
                except:
                    pass

            self.canvas.photo_data_img = ImageTk.PhotoImage(data_img)
            self.observation_img_id = self.canvas.create_image(909, 150, image=self.canvas.photo_data_img, anchor="nw")
        #

    # Method to start loop on separate thread for antenna update check - Adam Wikström 2026-04-27
    def start_serial_loop(self):
        threading.Thread(target=self.__serial_loop, daemon=True).start()

    # Method to check for and update the current state of the observation image - Adam Wikström 2026-04-27
    def __serial_loop(self):

        while True:
            if self.view_switching or self.serial_paused:
                time.sleep(0.01)
                continue

            current_state = functions2run.waitforserialchange(self.ser, IsThereArdruino=False)

            if self.states_equal(current_state, self.last_state) and self.state_counter == 0:
                self.window.after(0, lambda s=current_state: self.create_observation(s))
                self.state_counter += 1
            if not self.states_equal(current_state, self.last_state):
                self.last_state = current_state
                # self.latest_state = current_state
                self.window.after(0, self.reset_idle_timer)
                self.window.after(0, self.fsm_update(current_state))

                # The following code was moved to fsm_update but kept here for saftey reasons
                # if self.current_view == "observation_view" and not self.view_switching:
                #     count = functions2run.get_attenas_string().count("1")
                #     self.current_antennas = count
                #     self.canvas.itemconfig(self.antenna_text_id, text=f"{self.current_antennas}/{self.max_antennas}")
                #
                #     # Check for update in antenna count, and if it has increased play click sound
                #     if (self.antenna_state is not functions2run.get_attenas_string()
                #             and self.antenna_state.count("1") > functions2run.get_attenas_string().count("1")):
                #         self.antenna_state = functions2run.get_attenas_string()
                #         self.window.after(0, self.play_click_sound)
                #     else:
                #         self.antenna_state = functions2run.get_attenas_string()
                #
                #     self.progress_bar.set(self.current_antennas / self.max_antennas)
                #     self.window.after(0, lambda s=current_state: self.create_observation(s))

    # Method to handle the finite state machine
    def fsm_update(self, current_state):
        attenas = functions2run.get_attenas_string()
        buttons = functions2run.get_buttons_inp()

        button_pressed = buttons != self.button_state
        attenas_empty = attenas == "0000000000000000000000000000000000000000000000"
        attenas_active = not attenas_empty

        prev_state = self.state

        # VIDEO STATE
        if self.state == "video_view":
            if button_pressed:
                if attenas_empty:
                    self.state = "selection_view"
                else:
                    self.state = "restart_view"
        # SELECTION STATE
        elif self.state == "selection_view":
            if button_pressed:
                self.state = "guide_view"
        # GUIDE STATE
        elif self.state == "guide_view":
            if attenas_active:
                self.state = "observation_view"
        # OBSERVATION STATE
        elif self.state == "observation_view":
            # TO-DO check if live updating of antenna % works on progressbar
            # Update graph if not view switching
            if not self.view_switching:
                count = functions2run.get_attenas_string().count("1")
                self.current_antennas = count
                self.canvas.itemconfig(self.antenna_text_id, text=f"{self.current_antennas}/{self.max_antennas}")

                # Check for update in antenna count, and if it has increased play click sound
                if (self.antenna_state is not functions2run.get_attenas_string()
                        and self.antenna_state.count("1") > functions2run.get_attenas_string().count("1")):
                    self.antenna_state = functions2run.get_attenas_string()
                    self.window.after(0, self.play_click_sound)
                    self.progress_bar.set(self.current_antennas / self.max_antennas)
                else:
                    self.antenna_state = functions2run.get_attenas_string()
                    self.progress_bar.set(self.current_antennas / self.max_antennas)

                self.window.after(0, lambda s=current_state: self.create_observation(s))

        # RESTART STATE
        elif self.state == "restart_view":
            # optional reset logic
            pass

        # save changes to button and antenna states
        self.button_state = buttons
        self.antenna_state = attenas

        # trigger view change if needed
        if prev_state != self.state:
            self.change_view(self.state)

    # Method to close the window, and thus the program - Adam Wikström 2026-04-27
    def __close_window(self, event=None):
        print("Closing window")
        self.window.destroy()

    # Method to go to the next view - Adam Wikström 2026-04-27
    def __next_view(self, event=None):
        self.current_view_index = (self.current_view_index + 1) % len(self.views)
        self.change_view(self.views[self.current_view_index])

    # Method to go back to the previous view - Adam Wikström 2026-04-27
    def __previous_view(self, event=None):
        self.current_view_index = (self.current_view_index - 1) % len(self.views)
        self.change_view(self.views[self.current_view_index])

    # Method to reset the idle timer - Adam Wikström 2026-04-27
    def reset_idle_timer(self, event=None):
        if self.idle_job is not None:
            self.window.after_cancel(self.idle_job)

        self.idle_job = self.window.after(self.idle_timeout_ms, self.on_idle)

    # Method to determine behaviour when idle - Adam Wikström 2026-04-27
    def on_idle(self):
        if functions2run.get_attenas_string() == "0000000000000000000000000000000000000000000000":
            self.change_view("video_view")
        else:
            self.change_view("restart_view")

    # Method to compare the last state of the antennas with the current one - Adam Wikström 2026-04-27
    def states_equal(self, a, b):
        if a is None or b is None:
            return False

        for x, y in zip(a, b):
            if isinstance(x, np.ndarray):
                if not np.array_equal(x, y):
                    return False
            else:
                if x != y:
                    return False
        return True

    def play_click_sound(self):
        self.play_sound(self.click_sound_path)

    def play_sound(self, sound_path):
        def _play():
            try:
                playsound(sound_path)
            except Exception as e:
                print("Audio error:", e)

        threading.Thread(target=_play, daemon=True).start()

