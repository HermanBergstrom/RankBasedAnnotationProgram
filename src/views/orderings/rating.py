import json
import random
import time
from typing import Callable

import customtkinter as ctk

from pop_outs.is_finished_pop_out import IsFinishedPopOut
from views.orderings.ordering import OrderingScreen


class RatingScreen(OrderingScreen):
    """A screen for rating."""

    def __init__(
            self, root: ctk.CTk, save_obj: dict, menu_callback: Callable,
            user: str, reload_ordering_screen: Callable,
            hybrid_transition_made: bool, root_bind_callback: Callable):
        """
        Initialize the RatingScreen.

        Args:
            root (CTk): The root cutom tkinter object.
            save_obj (dict): The save object containing various parameters.
            menu_callback (function): The callback function for the menu.
            user (str): The user currently annotating.
            reload_ordering_screen (function): Callback function to reload the 
                                               ordering screen.
            hybrid_transition_made (bool): Flag indicating whether hybrid 
                                           transition was made.
            root_bind_callback (function): Callback function used to bind events to the
                                           root element.
        """

        super().__init__(root, save_obj, menu_callback, user,
                         reload_ordering_screen, hybrid_transition_made,
                         root_bind_callback)

        self.root_bind_callback = self.root_bind_callback

        self.buttons_frame = ctk.CTkFrame(master=self.root)

        with open('_internal/prompts.json', 'r') as file:
            prompts = json.load(file)

        rating_buttons = prompts['rating_buttons']

        if "custom_ratings" in save_obj:
            rating_buttons = save_obj["custom_ratings"]

        prompt = prompts['rating_prompt']

        if "custom_rating_prompt" in save_obj:
            prompt = save_obj['custom_rating_prompt']

        self.question = ctk.CTkLabel(
            master=self.root,
            text=prompt,
            font=('Helvetica bold', 20))

        self.tab_items = []
        self.tab_index = -1

        for index, button in enumerate(rating_buttons):
            ctk_button = ctk.CTkButton(
                master=self.buttons_frame, text=button +
                ' (' + str(index + 1) + ')',
                width=160, height=40, command=lambda index=index: self.submit(index),
                font=('Helvetica bold', 20))

            self.tab_items.append(ctk_button)

            self.root_bind_callback(str(index + 1), lambda event,
                                    index=index: self.on_shortcmd(index))
            self.root_bind_callback(
                "<KeyRelease-" + str(index + 1) + ">", lambda event,
                index=index: self.on_shortcmd_up(index))

        self.root_bind_callback(
            "<Return>", lambda event: self.on_enter())

        self.root_bind_callback(
            "<Tab>", lambda event: self.on_tab())

    def display(self):
        """
        Display the rating screen.
        """

        self.session_start_time = time.time()
        self.session_elapsed_time_prev = 0

        self.root.grid_rowconfigure(0, weight=3, uniform="ordering")
        self.root.grid_rowconfigure(1, weight=1, uniform="ordering")
        self.root.grid_rowconfigure(2, weight=26, uniform="ordering")
        self.root.grid_rowconfigure(3, weight=1, uniform="ordering")
        self.root.grid_rowconfigure(4, weight=2, uniform="ordering")
        self.root.grid_rowconfigure(5, weight=4, uniform="ordering")
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self.comparison_bar.grid(row=1, column=0, columnspan=2, pady=(10, 0))

        self.images_frame.grid(row=2, column=0, columnspan=2, padx=0, pady=0)

        self.question.grid(row=4, column=0, columnspan=2, pady=10, sticky="S")

        self.buttons_frame.grid(row=5, column=0, columnspan=2, sticky="N")

        for index, button in enumerate(self.tab_items):

            if index <= 0:
                padx = (10, 5)
            elif index >= len(self.tab_items) - 1:
                padx = (5, 10)
            else:
                padx = 10

            button.grid(row=0, column=index, pady=10, padx=padx)

        self.session_duration_label.place(relx=0.98, y=20, anchor="ne")

        self.comp_count_label.grid(row=0, column=0, columnspan=2, sticky="S")

        self.back_button.place(x=20, y=20)

        self.progress_bar.grid(
            row=3, column=0, columnspan=2, sticky="N", pady=5)
        self.progress_bar.grid_remove()

        self.timer_after = self.root.after(1000, self.update_time)

        if not self.is_finished_check():
            self.display_new_comparison()

    def init_image_frames(self):
        """
        Initialize the image frames.
        """

        self.displayed_images = []
        self.image_frames = []

        image_frame = ctk.CTkFrame(master=self.images_frame)

        self.image_frames.append(image_frame)

        image_frame.grid(row=1, column=0, padx=20, pady=20)

        displayed_image = ctk.CTkLabel(
            master=image_frame, text="")

        self.displayed_images.append(displayed_image)

        displayed_image.grid(row=0, column=0, columnspan=2,
                             sticky="ew", padx=10, pady=10)

        image_frame.bind(
            "<MouseWheel>", command=lambda event: self.on_image_scroll(
                event, 0))
        displayed_image.bind(
            "<MouseWheel>", command=lambda event: self.on_image_scroll(
                event, 0))

        image_frame.bind(
            "<Button-4>", command=lambda event: self.on_image_scroll_up(0))
        displayed_image.bind(
            "<Button-4>", command=lambda event: self.on_image_scroll_up(0))

        image_frame.bind(
            "<Button-5>", command=lambda event: self.on_image_scroll_down(0))
        displayed_image.bind(
            "<Button-5>", command=lambda event: self.on_image_scroll_down(0))

        displayed_image.bind(
            "<Enter>", command=lambda event: self.set_image_hover_idx(0))

        displayed_image.bind(
            "<Leave>", command=lambda event: self.set_image_hover_idx(-1))

    def display_new_comparison(self):
        """
        Display a new comparison.
        """

        self.reset_tab()
        key = self.sort_alg.get_comparison(self.user)

        if key:
            # load initial images
            self.images = [[key, self.load_initial_image(key), 0]]
            self.update_images()
            self.root.update()
            if self.scroll_allowed:
                self.progress_bar.grid()
                ctk_imgs = self.file_2_CTkImage(key)
                self.images = [[key, ctk_imgs, len(ctk_imgs)//2]]
                self.update_images()
                self.progress_bar.grid_remove()
                self.progress_bar_progress = 0
            if self.prev_sort_alg is not None:
                self.undo_label.place(x=20, y=70)
        else:
            key = random.choice(self.sort_alg.data)
            self.images = [[key, self.file_2_CTkImage(key), 0]]
            self.update_images()
            IsFinishedPopOut(self.root,
                             self.back_to_menu, 'no annotations')

    def on_tab(self):
        """
        Handle the tab key event.
        """

        if self.tab_index >= 0:
            self.remove_highlight(self.tab_items[self.tab_index])

        self.tab_index += 1
        if self.tab_index >= len(self.tab_items):
            self.tab_index = 0

        self.highlight(self.tab_items[self.tab_index])

    def reset_tab(self):
        """
        Reset the tab index and remove the highlight.
        """
        if self.tab_index != -1:
            self.remove_highlight(self.tab_items[self.tab_index])
            self.tab_index = -1

    def on_shortcmd_up(self, index):
        """
        Handle the key release event for a rating button.
        """

        if index >= len(self.tab_items):
            return

        self.remove_highlight(self.tab_items[index])
        self.root.update()
        self.tab_items[index].invoke()

    def highlight(self, widget):
        """
        Highlight a button widget.
        """
        widget.configure(fg_color=widget.cget("hover_color"))

    def remove_highlight(self, widget):
        """
        Remove the highlight from a button widget.
        """
        widget.configure(fg_color=['#3a7ebf', '#1f538d'])

    def on_enter(self):
        """
        Handle the Enter key event.
        """
        if self.tab_index >= 0:
            self.tab_items[self.tab_index].invoke()

    def on_shortcmd(self, index):
        """
        Handle the key press event for a rating button.
        """

        if index >= len(self.tab_items):
            return

        self.highlight(self.tab_items[index])

    def submit(self, lvl):
        """
        Submit the rating for a comparison.
        """

        if self.is_loading:
            return

        key = [key for key, _, _ in self.images][0]

        self.submit_comparison(key, lvl)
