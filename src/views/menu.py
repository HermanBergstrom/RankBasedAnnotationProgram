import json
import os
import pickle
import sys
from pathlib import Path
from typing import Callable, List, Optional, Tuple
import traceback

import customtkinter as ctk
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import utils.convergence as conv
import utils.ctk_utils as ctk_utils
import utils.saves_handler as saves_handler
from pop_outs.creation_pop_out import CreationPopOut
from pop_outs.delete_pop_out import DeletePopOut


class MenuScreen():
    """
    Represents the menu screen of the Rank-Based Annotation application.
    """

    def __init__(
            self, root: ctk.CTk, display_menu_callback: Callable,
            ordering_callback: Callable,
            open_user_selection: Callable,
            advanced_settings_callback: Callable,
            information_page_callback: Callable):
        """
        Initializes the MenuScreen instance.

        Args:
            root (CTk): The root window of the application.
            display_menu_callback (function): The callback function used to refresh the
                                              menu.
            ordering_callback (function): The callback function for loading a 
                                          saved annotation.
            open_user_selection (function): The function to open user selection.
            advanced_settings_callback (function): Calback function to bring up the
            advanced settings menu.
        """

        self.root = root
        self.root.protocol("WM_DELETE_WINDOW", root.quit)
        plt.style.use("dark_background")
        font = {'weight': 'bold',
                'size': 10}
        matplotlib.rc('font', **font)

        self.selected_user = None

        self.display_menu_callback = display_menu_callback
        self.ordering_callback = ordering_callback
        self.advanced_settings_callback = advanced_settings_callback
        self.information_page_callback = information_page_callback
        self.open_user_selection = open_user_selection

        with open('_internal/prompts.json', 'r') as file:
            prompts = json.load(file)

        path = saves_handler.get_full_path("saves")

        self.paths = list(Path(path).glob('*.pickle'))

        self.selected_save = -1
        self.annotation_rows = []
        self.open_plot = None
        self.og_row_color = None

        self.saves = [pickle.load(open(path, 'rb')) for path in self.paths]

        self.header = ctk.CTkLabel(
            master=self.root, text="Rank-Based Annotation",
            font=('Helvetica bold', 40))

        self.menu_frame = ctk.CTkFrame(master=self.root)

        self.instructions_frame = ctk.CTkFrame(master=self.root)
        self.save_info_frame = ctk.CTkFrame(self.root)

        self.new_button = ctk.CTkButton(
            master=self.menu_frame, text="New Annotation", width=250,
            height=45, font=('Helvetica bold', 20),
            command=self.new_annotation)
        self.delete_button = ctk.CTkButton(
            master=self.menu_frame, text="Delete Annotation", width=250,
            height=45, font=('Helvetica bold', 20))

        self.saved_annotations_header = ctk.CTkFrame(
            master=self.menu_frame, corner_radius=0,
            fg_color=self.menu_frame.cget("fg_color"))

        self.saved_annotations_header.grid_columnconfigure(
            0, weight=1, uniform="header")
        self.saved_annotations_header.grid_columnconfigure(
            1, weight=1, uniform="header")
        self.saved_annotations_header.grid_columnconfigure(
            2, weight=1, uniform="header")
        self.saved_annotations_header.grid_columnconfigure(
            3, weight=1, uniform="header")
        self.saved_annotations_header.grid_rowconfigure(
            0, weight=1, uniform="header")

        self.header_name_label = ctk.CTkLabel(
            master=self.saved_annotations_header, text="Name:",
            font=('Helvetica bold', 20))

        self.user_label = ctk.CTkLabel(
            master=self.root, text="", font=('Helvetica bold', 24))

        self.user_label.bind("<Enter>", lambda event, og_color=self.user_label.cget(
            'text_color'): self.highlight_label(self.user_label, og_color))
        self.user_label.bind("<Leave>", lambda event, og_color=self.user_label.cget(
            'text_color'): self.remove_highlight_label(self.user_label, og_color))
        self.user_label.bind(
            "<Button-1>", lambda event: self.open_user_selection())

        self.header_algorithm_label = ctk.CTkLabel(
            master=self.saved_annotations_header, text="Algorithm:",
            font=('Helvetica bold', 20))

        self.header_images_label = ctk.CTkLabel(
            master=self.saved_annotations_header, text="Images:",
            font=('Helvetica bold', 20))

        self.header_count_label = ctk.CTkLabel(
            master=self.saved_annotations_header,
            text="Status:", font=('Helvetica bold', 20))

        self.saved_annotations_frame = ctk.CTkScrollableFrame(
            master=self.menu_frame, height=400)

        self.saved_annotations_frame.columnconfigure(0, weight=1)

        self.text_header = ctk.CTkLabel(
            master=self.instructions_frame,
            text="Welcome to the Rank-Based Annotation program",
            font=('Helvetica bold', 24),
            wraplength=400)

        self.text = ctk.CTkLabel(
            master=self.instructions_frame,
            text=prompts['instruction_prompt'],
            font=('Helvetica bold', 18),
            wraplength=400, anchor="w", justify=ctk.LEFT)

        self.text.bind(
            '<Configure>', lambda event: self.update_wraplength(self.text))
        self.old_size = self.text.winfo_width()

    def display(self):
        """Displays the menu screen."""

        self.root.grid_rowconfigure(0, weight=1, uniform="header")
        self.root.grid_rowconfigure(1, weight=8, uniform="header")
        self.root.grid_columnconfigure(0, weight=2, uniform="root_column")
        self.root.grid_columnconfigure(1, weight=1, uniform="root_column")

        self.header.grid(row=0, column=0, columnspan=2, sticky="S")
        self.user_label.place(relx=0.98, rely=0.02, anchor='ne')
        self.menu_frame.grid(row=1, column=0, sticky="nsew",
                             padx=(20, 10), pady=20)

        self.menu_frame.grid_columnconfigure(0, weight=1)
        self.menu_frame.grid_columnconfigure(1, weight=1)
        self.menu_frame.grid_rowconfigure(0, weight=1)
        self.menu_frame.grid_rowconfigure(1, weight=3)
        self.menu_frame.grid_rowconfigure(2, weight=1)

        self.instructions_frame.grid(
            row=1, column=1, sticky="nsew", padx=(20, 10), pady=20)

        self.instructions_frame.grid_columnconfigure(0, weight=1)
        self.instructions_frame.grid_rowconfigure(0, weight=1)
        self.instructions_frame.grid_rowconfigure(1, weight=5)

        self.new_button.grid(row=2, column=0, columnspan=2, padx=(
            20, 10), pady=10)

        self.saved_annotations_header.grid(
            row=0, column=0, columnspan=2, sticky="sew", padx=(10, 20),
            pady=(20, 0))

        self.header_name_label.grid(
            row=0, column=0, sticky="w", padx=10, pady=4)
        self.header_algorithm_label.grid(
            row=0, column=1, sticky="w", padx=10, pady=4)
        self.header_images_label.grid(
            row=0, column=2, sticky="w", padx=10, pady=4)
        self.header_count_label.grid(
            row=0, column=3, sticky="w", padx=10, pady=4)

        self.saved_annotations_frame.grid(
            row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 0))

        self.display_saves()

        self.text_header.grid(row=0, column=0, padx=10, pady=10, sticky="new")
        self.text.grid(row=1, column=0, padx=20, pady=10, sticky="new")

    def display_user(self, user: str):
        """
        Displays the user label with the provided username.

        Args:
            user (str): The username to display.
        """
        self.selected_user = user
        self.user_label.configure(text=user)

    def display_saves(self):
        """
        Displays the saved annotations in the menu.
        """
        for i, save in enumerate(self.saves):
            self.append_row(i, save)

    def append_row(self, index: int, save: dict):
        """
        Appends a row with save information to the saved annotations frame.

        Args:
            index (int): The index of the save.
            save (dict): The save object.
        """

        saved_annotations_row = ctk.CTkFrame(
            master=self.saved_annotations_frame)

        if not self.og_row_color:
            self.og_row_color = saved_annotations_row.cget("fg_color")

        self.annotation_rows.append(saved_annotations_row)

        saved_annotations_row.bind(
            "<Button-1>", command=lambda event, i=index: self.target_save(i))

        saved_annotations_row.grid(row=index, column=0, sticky="ew", pady=3)

        saved_annotations_row.grid_columnconfigure(0, weight=1, uniform="row")
        saved_annotations_row.grid_columnconfigure(1, weight=1, uniform="row")
        saved_annotations_row.grid_columnconfigure(2, weight=1, uniform="row")
        saved_annotations_row.grid_columnconfigure(3, weight=1, uniform="row")
        saved_annotations_row.grid_rowconfigure(0, weight=1, uniform="row")

        save_name_label = ctk.CTkLabel(
            master=saved_annotations_row, text=save["name"],
            font=('Helvetica bold', 20))
        save_name_label.grid(row=0, column=0, padx=10, pady=4, sticky="w")

        sort_alg = save["sort_alg"]

        algorithm_label = ctk.CTkLabel(
            master=saved_annotations_row, text=type(sort_alg).__name__,
            font=('Helvetica bold', 20))

        algorithm_label.grid(row=0, column=1, padx=10, pady=4, sticky="w")

        total_images = len(sort_alg.data)

        total_images_label = ctk.CTkLabel(
            master=saved_annotations_row, text=total_images,
            font=('Helvetica bold', 20))

        total_images_label.grid(row=0, column=2, padx=10, pady=4, sticky="w")

        text, text_color = self.get_status(
            sort_alg.get_comparison_count(), sort_alg.get_comparison_max())

        count_label = ctk.CTkLabel(
            master=saved_annotations_row, text=text, text_color=text_color,
            font=('Helvetica bold', 20))

        count_label.grid(row=0, column=3, padx=10, pady=4, sticky="w")

        for child in saved_annotations_row.winfo_children():
            child.bind("<Button-1>", command=lambda event,
                       i=index: self.target_save(i))

        ctk_utils.add_hover(saved_annotations_row)

        if index == self.selected_save:
            ctk_utils.highlight(self.saved_annotations_frame)

    def new_annotation(self):
        """
        Callback function for the new annotation button.
        """

        CreationPopOut(self.root, self.display_menu_callback,
                       self.advanced_settings_callback)

    def target_save(self, index):
        """
        Changes which save is currently displayed, updates highlights in the saves list 
        accordingly.

        Args:
            index (int): The index of the save file that is to be displayed in the 
                         saves list 
        """

        if self.open_plot:
            plt.close(self.open_plot)
            self.open_plot = None

        if self.selected_save < 0:
            self.instructions_frame.grid_remove()
            self.save_info_frame.grid(
                row=1, column=1, sticky="nsew", padx=(20, 10),
                pady=20)
        else:
            for child in self.save_info_frame.winfo_children():
                child.destroy()

            ctk_utils.remove_highlight(
                self.annotation_rows[self.selected_save],
                self.og_row_color)
            ctk_utils.add_hover(self.annotation_rows[self.selected_save])

        ctk_utils.remove_hover(self.annotation_rows[index])
        ctk_utils.highlight(self.annotation_rows[index], self.og_row_color)

        self.selected_save = index
        self.show_save_info(index)

    def show_save_info(self, index: int):
        """
        Displays information related to a save file.

        Args:
            index (int): The index of the save file that is to be displayed in the 
                         saves list 
        """

        save = self.saves[index]

        save_name_label = ctk.CTkLabel(
            self.save_info_frame, text=save["name"],
            font=('Helvetica bold', 24))

        sort_alg = save["sort_alg"]

        alg_name = type(sort_alg).__name__

        save_algorithm_label = ctk.CTkLabel(
            self.save_info_frame, text="Algorithm:",
            font=('Helvetica bold', 20))

        save_algorithm_value = ctk.CTkLabel(
            self.save_info_frame, text=type(sort_alg).__name__,
            font=('Helvetica bold', 20))

        save_image_count_label = ctk.CTkLabel(
            self.save_info_frame, text="Images:",
            font=('Helvetica bold', 20))

        save_image_count_value = ctk.CTkLabel(
            self.save_info_frame, text=str(len(sort_alg.data)),
            font=('Helvetica bold', 20))

        dir_rel_path = ""

        if os.path.isdir(saves_handler.get_full_path(save["image_directory"])):
            dir_rel_path = save["image_directory"]
        elif self.selected_user and self.selected_user in save['user_directory_dict']:
            rel_path = save['user_directory_dict'][self.selected_user]

            if os.path.isdir(saves_handler.get_full_path(rel_path)):
                dir_rel_path = rel_path

        if dir_rel_path:
            save_image_count_value.bind(
                "<Button-1>", command=lambda event,
                path=dir_rel_path: self.open_folder(path))

            og_color = save_image_count_value.cget("text_color")
            save_image_count_value.bind(
                "<Enter>", lambda event,
                og_color=og_color: self.highlight_label(
                    save_image_count_value, og_color))
            save_image_count_value.bind(
                "<Leave>", lambda event,
                og_color=og_color: self.remove_highlight_label(
                    save_image_count_value, og_color))

        comp_count = sort_alg.get_comparison_count()

        max_count = sort_alg.get_comparison_max()

        save_status_label = ctk.CTkLabel(
            self.save_info_frame, text="Status:",
            font=('Helvetica bold', 20))

        text, text_color = self.get_status(comp_count, max_count)

        save_status_value = ctk.CTkLabel(
            self.save_info_frame, text=text,
            text_color=text_color, font=('Helvetica bold', 20))

        save_comp_count_label = ctk.CTkLabel(
            self.save_info_frame, text="Annotations made:",
            font=('Helvetica bold', 20))

        save_comp_count_value = ctk.CTkLabel(
            self.save_info_frame, text=str(comp_count) + "/" + str(max_count),
            font=('Helvetica bold', 20))

        if alg_name == "TrueSkill" or alg_name == "HybridTrueSkill":

            # Rmses takes too long...
            if len(sort_alg.data) < 1000:
                try:
                    values = conv.get_convergence(save)

                    save_convergence_label = ctk.CTkLabel(
                        self.save_info_frame, text="Convergence",
                        font=('Helvetica bold', 20))

                    save_convergence_label.grid(
                        row=5, column=0, pady=(10, 5),
                        columnspan=2)

                    if len(values) > 1:

                        fig, ax = plt.subplots()
                        self.open_plot = fig
                        fig.set_size_inches(4.5, 3)
                        fig.set_facecolor("#212121")
                        ax.set_facecolor("#1a1a1a")

                        ax.plot(values)

                        ax.spines['top'].set_visible(False)
                        ax.spines['right'].set_visible(False)

                        ax.set_xlabel("Comparisons")
                        ax.set_ylabel("RMSE")
                        plt.subplots_adjust(bottom=0.2, left=0.15)
                        canvas = FigureCanvasTkAgg(
                            fig, master=self.save_info_frame)
                        canvas.draw()

                        width, height = canvas.get_width_height()

                        place_holder_frame = ctk.CTkFrame(
                            self.save_info_frame, width=width, height=height,
                            corner_radius=0, fg_color="#1a1a1a")

                        place_holder_frame.grid(
                            row=6, column=0, pady=(5, 10),
                            columnspan=2)

                        # Not a fan of this workaround, but the canvas has not necessarily been
                        # drawn when placed on the display, could not find any event to await so
                        # instead we use a placeholder for the first 100ms...
                        self.root.after(100, lambda: self.replace_placeholder(
                            place_holder_frame, canvas.get_tk_widget()))
                    else:

                        text = "More comparisons are required\n\
before convergence can be displayed"
                        needs_more_comparisons_label = ctk.CTkLabel(
                            self.save_info_frame,
                            text=text,
                            font=('Helvetica bold', 20))
                        needs_more_comparisons_label.grid(
                            row=6, column=0, pady=(5, 10),
                            columnspan=2)
                except:
                    traceback.print_exc()
                    text = "An error occured\n\
while calculating convergence\n\
Check output for more info"
                    needs_more_comparisons_label = ctk.CTkLabel(
                        self.save_info_frame,
                        text=text,
                        font=('Helvetica bold', 20))
                    needs_more_comparisons_label.grid(
                        row=6, column=0, pady=(5, 10),
                        columnspan=2)
            else:

                text = "Dataset too large\n\
Ignoring convergence graph\n\
to avoid slow-down"
                needs_more_comparisons_label = ctk.CTkLabel(
                    self.save_info_frame,
                    text=text,
                    font=('Helvetica bold', 20))
                needs_more_comparisons_label.grid(
                    row=6, column=0, pady=(5, 10),
                    columnspan=2)

        more_information_button = ctk.CTkButton(
            master=self.save_info_frame, text="More information", height=45,
            font=('Helvetica bold', 20),
            command=lambda index=index: self.information_page_callback(
                self.saves[index]))

        load_save_button = ctk.CTkButton(
            master=self.save_info_frame, text="Load", height=45,
            font=('Helvetica bold', 20),
            command=lambda index=index: self.load_save(index))
        delete_save_button = ctk.CTkButton(
            master=self.save_info_frame, text="Delete", height=45,
            fg_color="#ed022a", hover_color="#bf0021",
            font=('Helvetica bold', 20),
            command=lambda index=index: self.open_delete_save_pop_out(index))

        self.save_info_frame.grid_columnconfigure(
            0, weight=1, uniform="save_info")
        self.save_info_frame.grid_columnconfigure(
            1, weight=1, uniform="save_info")

        self.save_info_frame.grid_rowconfigure(
            1, weight=1, uniform="save_info")
        self.save_info_frame.grid_rowconfigure(
            2, weight=1, uniform="save_info")
        self.save_info_frame.grid_rowconfigure(
            3, weight=1, uniform="save_info")
        self.save_info_frame.grid_rowconfigure(
            4, weight=1, uniform="save_info")
        self.save_info_frame.grid_rowconfigure(
            5, weight=1, uniform="save_info")
        self.save_info_frame.grid_rowconfigure(
            6, weight=6, uniform="save_info")
        self.save_info_frame.grid_rowconfigure(
            7, weight=2, uniform="save_info")
        self.save_info_frame.grid_rowconfigure(
            8, weight=2, uniform="save_info")

        save_name_label.grid(row=0, column=0, columnspan=2, pady=20)
        save_algorithm_label.grid(row=1, column=0, pady=10, padx=5, sticky="e")
        save_algorithm_value.grid(row=1, column=1, pady=10, padx=5, sticky="w")
        save_image_count_label.grid(
            row=2, column=0, pady=10, padx=5, sticky="e")
        save_image_count_value.grid(
            row=2, column=1, pady=10, padx=5, sticky="w")
        save_status_label.grid(
            row=3, column=0, pady=10, padx=5, sticky="e")
        save_status_value.grid(
            row=3, column=1, pady=10, padx=5, sticky="w")
        save_comp_count_label.grid(
            row=4, column=0, pady=10, padx=5, sticky="e")
        save_comp_count_value.grid(
            row=4, column=1, pady=10, padx=5, sticky="w")

        more_information_button.grid(
            row=7, column=0, columnspan=2, pady=10, padx=5)

        load_save_button.grid(row=8, column=0, pady=10, padx=5)
        delete_save_button.grid(row=8, column=1, pady=10, padx=5)

    def open_folder(self, rel_path: str):
        """
        Opens a folder in the file explorer of the operating system. If the provided 
        folder does not exist, nothing happens.

        Args:
            rel_path (str): The relative path to the folder that is to be opened. 
        """
        full_path = saves_handler.get_full_path(rel_path)
        if os.path.isdir(full_path):
            if sys.platform == "linux" or sys.platform == "linux2":
                os.system('xdg-open "%s"' % full_path)
            elif sys.platform == "Darwin" or sys.platform == "darwin":
                os.system('open "%s"' % full_path)
            else:
                os.startfile(full_path)

    def get_status(self, count: int, max_count: int) -> Tuple[str,
                                                              Optional[str]]:
        """
        Fetches the status of a save in the form of a string as well as color 
        information for that string. 

        Args:
            count (int): The amount of comparisons made.
            max_count (int): The total amount of comparisons allowed.
        Returns:
            Tuple[str, Optional[str]]: The text corresponding to the status of the save
                                       as well as potentially a specific color for the
                                       text.
        """

        if count >= max_count:
            return "Finished", "green"

        return "Ongoing", None

    def replace_placeholder(self, placeholder: ctk.CTkFrame,
                            canvas: ctk.CTkCanvas):
        """
        Function to replace the placeholder frame for flickering workaround.

        Args:
            placeholder (ctk.CTkFrame): The placeholder frame that is to be removed.
            canvas (ctk.CTkCanvas): The Canvas that is to be placed instead.
        """
        placeholder.grid_remove()
        canvas.grid(
            row=6, column=0, pady=(5, 10),
            columnspan=2)

    def load_save(self, index):
        """
        Loads the save object associated with the index

        Args:
            index (int): The index of the save.

        """
        file = open(self.paths[index], 'rb')
        save_obj = pickle.load(file)
        self.ordering_callback(save_obj)

    def open_delete_save_pop_out(self, index):
        """
        Opens a confirmation pop out which allows the user to delete a save.

        Args:
            index (int): The index of the save object that is up for deletion in the 
                         saves list.
        """

        DeletePopOut(self.root,
                     self.display_menu_callback, self.saves[index])

    def update_wraplength(self, label: ctk.CTkLabel):
        """
        Updates the wraplength of the label based on its width.

        Args:
            label (CTkLabel): The label to update.
        """

        if abs(label.winfo_width() - self.old_size) > 20:
            self.old_size = label.winfo_width()
            label.configure(wraplength=label.winfo_width() - 10)

    def highlight_label(self, label: ctk.CTkLabel, og_color: List[str]):
        """
        Highlights the label on mouse hover.

        Args:
            label (ctk.CTkLabel): The label to be highlighted.
            og_color (List[str]): The original color of the label as a list of 
                                  strings representing the color code.
        """
        gray_color = int(og_color[1][-2:]) + 10

        if gray_color > 100:
            gray_color = 100

        label.configure(text_color='gray' + str((gray_color)))

    def remove_highlight_label(self, label: ctk.CTkLabel, og_color: List[str]):
        """
        Removes the highlight from the specified label by restoring its original
        text color.

        Args:
            label (ctk.CTkLabel): The label from which to remove the highlight.
            og_color (List[str]): The original color of the label as a list of 
                                  strings representing the color code.
        """
        label.configure(text_color=og_color)
