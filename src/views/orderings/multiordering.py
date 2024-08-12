import time
from tkinter import Event
from typing import Callable

import customtkinter as ctk

import sorting_algorithms as sa
from views.orderings.ordering import OrderingScreen


class MultiOrderingScreen(OrderingScreen):
    """A screen for multi-ordering."""

    def __init__(self, root: ctk.CTkFrame, save_obj: dict,
                 menu_callback: Callable, user: str,
                 reload_ordering_screen: Callable,
                 root_bind_callback: Callable):
        """
        Initialize the MultiOrderingScreen.

        Args:
            root (CTkFrame): The root frame for the screen.
            save_obj (dict): The save object.
            menu_callback (function): The callback function for the menu.
            user (str): The user name.
            reload_ordering_screen (function): The function to reload the 
                                               ordering screen.
            root_bind_callback (function): Callback function used to bind events to the
                                           root element.
        """

        super().__init__(root, save_obj, menu_callback, user,
                         reload_ordering_screen, True, root_bind_callback)

        self.root_bind_callback = root_bind_callback

        self.int_diff_levels = [ctk.IntVar(None, 1)
                                for _ in range(self.comparison_size - 1)]

        self.submit_button = ctk.CTkButton(
            master=self.root, text="Submit Ordering", width=280, height=60,
            command=self.submit, font=('Helvetica bold', 20))

        self.motion_allowed = True

        self.progress_bar.grid(
            row=2, column=0, columnspan=2, sticky="N", pady=5)
        self.progress_bar.grid_remove()

    def display(self):
        """
        Display the multi-ordering screen.
        """

        self.session_start_time = time.time()
        self.session_elapsed_time_prev = 0

        self.root.grid_rowconfigure(0, weight=2, uniform="ordering")
        self.root.grid_rowconfigure(1, weight=16, uniform="ordering")
        self.root.grid_rowconfigure(2, weight=1, uniform="ordering")
        self.root.grid_rowconfigure(3, weight=2, uniform="ordering")
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        if not self.sort_alg.is_finished():
            self.images_frame.grid(
                row=1, column=0, columnspan=2, padx=0, pady=0)

        self.submit_button.grid(row=3, column=0, columnspan=2, sticky="N")

        self.session_duration_label.place(relx=0.98, y=20, anchor="ne")
        self.comp_count_label.grid(row=0, column=0, columnspan=2, sticky="S")

        self.back_button.place(x=20, y=20)

        self.timer_after = self.root.after(1000, self.update_time)

        self.buttons_initialized = False

        self.is_loading = True

        if not self.is_finished_check():
            self.display_new_comparison()

        self.is_loading = False

    def init_image_frames(self):
        """
        Initialize the image frames.
        """

        self.displayed_images = []
        self.image_frames = []

        for i in range(self.comparison_size):

            image_frame = ctk.CTkFrame(master=self.images_frame)

            self.image_frames.append(image_frame)

            image_frame.grid(row=1, column=i, padx=20, pady=(5, 20))

            displayed_image = ctk.CTkLabel(
                master=image_frame, text="")

            self.displayed_images.append(displayed_image)

            displayed_image.grid(row=0, column=0, columnspan=2,
                                 sticky="ew", padx=10, pady=10)

            left_button_state = ctk.NORMAL if i != 0 else ctk.DISABLED

            move_left_button = ctk.CTkButton(
                master=image_frame, text="<", width=120, height=36,
                font=('Helvetica bold', 20),
                command=lambda i=i: self.move_left(i),
                state=left_button_state)
            move_left_button.grid(row=1, column=0, padx=(5, 0), pady=(0, 10))

            if i != self.comparison_size - 1:
                right_button_state = ctk.NORMAL
            else:
                right_button_state = ctk.DISABLED

            move_right_button = ctk.CTkButton(
                master=image_frame, text=">", width=120, height=36,
                font=('Helvetica bold', 20),
                command=lambda i=i: self.move_right(i),
                state=right_button_state)
            move_right_button.grid(row=1, column=1, padx=(0, 5), pady=(0, 10))

            image_frame.bind(
                "<Button-1>", command=lambda event,
                image_frame=image_frame, i=i: self.on_drag_start(
                    event, image_frame, i))
            image_frame.bind(
                "<B1-Motion>", command=lambda event,
                image_frame=image_frame: self.on_drag_motion(
                    event, image_frame))
            image_frame.bind(
                "<ButtonRelease-1>", command=lambda event,
                image_frame=image_frame, i=i: self.on_drag_stop(
                    event, image_frame, i))
            image_frame.bind("<MouseWheel>", command=lambda event,
                             i=i: self.on_image_scroll(event, i))

            displayed_image.bind(
                "<Button-1>", command=lambda event,
                image_frame=image_frame, i=i: self.on_drag_start(
                    event, image_frame, i))

            displayed_image.bind(
                "<B1-Motion>", command=lambda event,
                image_frame=image_frame: self.on_drag_motion(
                    event, image_frame))

            displayed_image.bind(
                "<ButtonRelease-1>", command=lambda event,
                image_frame=image_frame,
                i=i: self.on_drag_stop(event, image_frame, i))

            displayed_image.bind(
                "<MouseWheel>", command=lambda event, i=i:
                self.on_image_scroll(event, i))

            image_frame.bind("<Button-4>", command=lambda event,
                             i=i: self.on_image_scroll_up(i))
            displayed_image.bind("<Button-4>", command=lambda event,
                                 i=i: self.on_image_scroll_up(i))

            image_frame.bind("<Button-5>", command=lambda event,
                             i=i: self.on_image_scroll_down(i))
            displayed_image.bind("<Button-5>", command=lambda event,
                                 i=i: self.on_image_scroll_down(i))

            self.root_bind_callback(
                "<Return>", lambda event: self.submit())

            displayed_image.bind(
                "<Enter>", command=lambda event, i=i: self.set_image_hover_idx(i))

            displayed_image.bind(
                "<Leave>", command=lambda event: self.set_image_hover_idx(-1))

    def init_diff_level_buttons(self):
        """
        Initialize the difference level buttons.
        """

        diff_levels_frame = ctk.CTkFrame(
            master=self.images_frame)

        image_width = self.images[0][1][0]._size[0]

        diff_levels_frame.grid(
            row=0, column=0, columnspan=self.comparison_size,
            padx=(30 + image_width // 2),
            pady=(10, 0),
            sticky="ew")

        for i in range(len(self.int_diff_levels)):
            diff_levels_frame.columnconfigure(i, weight=1)

        for i, int_diff_level in enumerate(self.int_diff_levels):

            diff_level_frame = ctk.CTkFrame(
                master=diff_levels_frame)

            diff_level_frame.grid(row=0, column=i)

            r0 = ctk.CTkRadioButton(
                master=diff_level_frame, variable=int_diff_level, value=0,
                width=22, text="")
            r1 = ctk.CTkRadioButton(
                master=diff_level_frame, variable=int_diff_level, value=1,
                width=22, text="")
            r2 = ctk.CTkRadioButton(
                master=diff_level_frame, variable=int_diff_level, value=2,
                width=22, text="")

            r0.grid(row=1, column=0, padx=(12, 5), pady=2,
                    sticky="ew")
            r1.grid(row=1, column=1, padx=(12, 5), pady=2,
                    sticky="ew")
            r2.grid(row=1, column=2, padx=(12, 5), pady=2,
                    sticky="ew")

            diff_level_label = ctk.CTkLabel(
                text="", master=diff_level_frame, font=('Helvetica bold', 18))
            diff_level_label.grid(row=0, column=0, columnspan=3)

            int_diff_level.trace(
                'w', lambda var, index, mode, int_diff_level=int_diff_level,
                label=diff_level_label: self.update_diff_labels(
                    int_diff_level, label))

        diff_levels_frame.configure(
            fg_color=self.images_frame.cget("fg_color"))

    def reset_diff_levels(self):
        """
        Reset the difference levels to their default values.
        """
        for int_diff_lvl in self.int_diff_levels:
            int_diff_lvl.set(1)

    def update_diff_labels(
            self, int_diff_level: ctk.IntVar, label: ctk.CTkLabel):
        """
        Update the labels for the difference levels.

        Args:
            int_diff_level (IntVar): The difficulty level as an integer 
                                     variable.
            label (CTkLabel): The label to update with the difficulty 
                              level text.
        """
        if int_diff_level.get() == 0:
            label.configure(text="no difference")
        elif int_diff_level.get() == 2:
            label.configure(text="large difference")
        else:
            label.configure(text="")

    def create_image_widget(self, image_idx: int) -> ctk.CTkFrame:
        """
        Create a widget for displaying an image.

        Args:
            image_idx (int): The index of the image.

        Returns:
            CTkFrame: The created image widget.
        """
        image_frame = ctk.CTkFrame(
            master=self.root)

        img = self.displayed_images[image_idx].cget("image")

        displayed_image = ctk.CTkLabel(
            master=image_frame, text="", image=img)

        displayed_image.grid(row=0, column=0, columnspan=2,
                             sticky="ew", padx=10, pady=10)

        move_left_button = ctk.CTkButton(
            master=image_frame, text="<", width=120, height=36,
            font=('Helvetica bold', 20),
            state=ctk.DISABLED)
        move_left_button.grid(row=1, column=0, padx=(5, 0), pady=(0, 10))

        move_right_button = ctk.CTkButton(
            master=image_frame, text=">", width=120, height=36,
            font=('Helvetica bold', 20),
            state=ctk.DISABLED)
        move_right_button.grid(row=1, column=1, padx=(0, 5), pady=(0, 10))

        return image_frame

    def display_new_comparison(self):
        """
        Display a new comparison of images.
        """
        self.reset_diff_levels()

        keys = self.sort_alg.get_comparison(self.user)

        self.images = [[img, self.load_initial_image(img), 0]
                       for img in keys]
        self.update_images()

        if not self.buttons_initialized:
            self.init_diff_level_buttons()
            self.buttons_initialized = True
        self.root.update()

        if self.scroll_allowed:
            self.progress_bar.grid(
                row=2, column=0, columnspan=2, sticky="N", pady=5)

            new_imgs = []
            for img in keys:
                ctk_imgs = self.file_2_CTkImage(img)
                new_imgs.append([img, ctk_imgs, len(ctk_imgs)//2])
            self.images = new_imgs

            self.update_images()
            self.progress_bar.grid_remove()
            self.progress_bar_progress = 0

        if self.prev_sort_alg is not None:
            self.undo_label.place(x=20, y=70)

    def move_left(self, index: int):
        """
        Move an image to the left in the comparison.

        Args:
            index (int): The index of the image to move.
        """

        if self.is_loading:
            return

        if index > 0:
            temp = self.images[index]
            self.images[index] = self.images[index - 1]
            self.images[index - 1] = temp

        self.update_images()

        self.reset_diff_levels()

    def move_right(self, index: int):
        """
        Move an image to the right in the comparison.

        Args:
            index (int): The index of the image to move.
        """

        if self.is_loading:
            return

        if index < len(self.images) - 1:
            temp = self.images[index]
            self.images[index] = self.images[index + 1]
            self.images[index + 1] = temp

        self.update_images()

        self.reset_diff_levels()

    def on_drag_start(self, event: Event, frame: ctk.CTkFrame, idx: int):
        """
        Event handler for when dragging starts.

        Args:
            event (Event): The Tkinter event object.
            frame (CTkFrame): The frame where the event occurred.
            idx (int): The index of the image being dragged.
        """
        if self.is_loading:
            return

        self.black_frame = ctk.CTkFrame(
            master=self.images_frame, width=frame.winfo_width(),
            height=frame.winfo_height())

        self.black_frame.place(x=frame.winfo_x(), y=frame.winfo_y())

        pos_x = self.images_frame.winfo_x() + frame.winfo_x() + event.x
        pos_y = self.images_frame.winfo_y() + frame.winfo_y() + event.y

        dx = frame.winfo_width()//2
        dy = frame.winfo_height()//2

        frame_clone = self.create_image_widget(idx)
        frame_clone.place(x=pos_x-dx, y=pos_y-dy)

        self.drag_frame = frame_clone

    def allow_motion(self):
        """
        Allows motion after a delay.
        """
        self.motion_allowed = True

    def on_drag_motion(self, event: Event, frame: ctk.CTkFrame):
        """
        Event handler for when dragging is in motion.

        Args:
            event (Event): The Tkinter event object.
            frame (CTkFrame): The frame where the event occurred.
        """

        if not self.motion_allowed or self.is_loading:
            return
        else:
            self.motion_allowed = False
            self.root.after(10, self.allow_motion)

        x = self.images_frame.winfo_x() + frame.winfo_x() + event.x - \
            self.drag_frame.winfo_width()//2

        y = self.images_frame.winfo_y() + frame.winfo_y() + event.y - \
            self.drag_frame.winfo_height()//2

        self.drag_frame.place(x=x, y=y)

        self.root.update_idletasks()

    def on_drag_stop(self, event: Event, frame: ctk.CTkFrame, idx: int):
        """
        Event handler for when dragging stops.

        Args:
            event (Event): The Tkinter event object.
            frame (CTkFrame): The frame where the event occurred.
            idx (int): The index of the image being dragged.
        """

        if self.is_loading:
            return

        self.drag_frame.place_forget()
        self.black_frame.place_forget()

        index, row = self.images_frame.grid_location(
            frame.winfo_x() + event.x, event.y)

        if row != 1 or index < 0 or index >= len(self.images) or index == idx:
            return

        widget = self.image_frames[index]

        width = widget.winfo_width()

        relative_x = frame.winfo_x() + event.x - widget.winfo_x() + 20

        from_right_bonus = 0

        if (idx > index):
            from_right_bonus = 1

        image_to_move = self.images.pop(idx)
        if relative_x < width // 3:
            self.images.insert(index - 1 + from_right_bonus, image_to_move)
        elif relative_x < 2*width // 3:
            # If you are coming from above, same as lower third
            # If you are coming from below, same as upper third
            if from_right_bonus:
                self.images.insert(index - 1 + from_right_bonus, image_to_move)
            else:
                self.images.insert(index + from_right_bonus, image_to_move)
        else:
            self.images.insert(index + from_right_bonus, image_to_move)

        self.update_images()
        self.reset_diff_levels()

    def submit(self):
        """
        Submits the comparison.
        """

        keys = [key for key, _, _ in self.images]

        diff_lvls = [sa.DiffLevel(int_diff_lvl.get())
                     for int_diff_lvl in self.int_diff_levels]

        self.submit_comparison(keys, diff_lvls)
