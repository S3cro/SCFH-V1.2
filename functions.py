from tkinter import filedialog
import customtkinter as ctk
import os
import time

root = ctk.CTk()  # creates a ctk root of the whole app


def save_config(config):
    """
    Saves the config dictionary to config.txt.
    :param config: Dictionary containing config data.
    """
    with open("config.txt", "w", encoding="utf-8") as f:
        for section, items in config.items():
            f.write(f"[{section}]\n")
            for key, value in items.items():
                f.write(f"{key}={value}\n")
            f.write("\n")


class Tabs(ctk.CTkTabview):
    """
    Handles Tabs in my app.
    Inherits attributes from ctk.CTKTabview
    main actions:
    1. create tabs
    2. handle each tab logic
    3. collect variables from each tab instead of returning a lot of variables
    and passing them between functions.
    """
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.config = load_config() # Load config once
        self.main_folder = self.config["Paths"].get("main_directory")
        self.project_name = None
        self.modes_list:list = []
        self.inside_cat_path:str = ""
        self.inner_switch = None
        self.category_instance = None
        self.label_widgets = {} # Dictionary to store label widgets

        self.tab_widget = ctk.CTkTabview(master)  # create tabs widget
        self.tab_widget.pack(fill="both", expand=True)

        self.create_tabs() # creates the tabs

    def create_tabs(self):
        """
        handles creation and configuration of tabs.
        """
        self.tab_widget.add("Main")
        self.tab_widget.add("Configure")
        self.tab_widget.add("Modes")

        for button in self.tab_widget._segmented_button._buttons_dict.values():
            """
            ignore the warning here idgaf about the protected class it works.
            allows bypass of font set to tab restriction.
            """
            button.configure(font=("Arial", 18))  # Change font size here

        self.main_tab(self.tab_widget.tab("Main")) # run main tab logic
        self.config_tab(self.tab_widget.tab("Configure"))  # run config tab logic
        self.modes_config(self.tab_widget.tab("Modes"))  # run modes tab logic

    def main_tab(self, tab):
        """
        Handles all actions in the main tab.
        labels,buttons,more frames,segmented buttons, IDK what to write in documentation here.
        :param tab: main tab
        """

        project_creation_frame = ctk.CTkFrame(tab)  # create a frame for project creation (name, checkboxes, category)
        project_creation_frame.pack(fill="both", expand=True)

        project_name_label = ctk.CTkLabel(project_creation_frame, text=self.config["Labels"]["project_name_label"],
                                          font=("Arial", 22, "bold"))  # project name label
        project_name_label.pack(pady=15) # creates label

        self.project_name = get_project_name(project_creation_frame) # Project name entry

        self.category_instance = CategoriesLogic(frame=project_creation_frame, config=self.config)

        # upon Pressing on the Confirm button, you will be sent to the modes tab.
        move_to_modes_tab_button = ctk.CTkButton(project_creation_frame,
                                                 text="Confirm", width=250, height=100,
                                                 command= lambda: (self.tab_widget.set("Modes"), no_category_popup(self.tab_widget) if self.category_instance.cat_path == "" else None),
                                                 font=("Arial", 22, "bold"))
        move_to_modes_tab_button.pack(pady=15, side="bottom")

    def open_config_editor(self):
        """
        Opens a window to edit labels in config.txt and updates the app dynamically.
        """
        editor_window = ctk.CTkToplevel()
        editor_window.title("Edit Labels")
        editor_window.geometry("600x400")

        editor_window.transient(root)
        editor_window.grab_set()
        editor_window.focus_force()

        scroll_frame = ctk.CTkScrollableFrame(editor_window, label_text="Edit Labels", label_font=("Arial", 16, "bold"))
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        entries = {}
        for label_key in self.config["Labels"]:
            frame = ctk.CTkFrame(scroll_frame)
            frame.pack(fill="x", pady=5)
            ctk.CTkLabel(frame, text=label_key, font=("Arial", 14), width=200).pack(side="left", padx=5)
            entry = ctk.CTkEntry(frame, width=300, font=("Arial", 14))
            entry.insert(0, self.config["Labels"][label_key])
            entry.pack(side="left", padx=5)
            entries[label_key] = entry

        def save_changes():
            for key, entry_widget in entries.items():
                self.config["Labels"][key] = entry_widget.get().strip() or self.config["Labels"][key]
            save_config(self.config)
            self.update_labels()
            editor_window.destroy()

        buttons_frame = ctk.CTkFrame(editor_window)
        buttons_frame.pack(side="bottom", pady=10)
        ctk.CTkButton(buttons_frame, text="Save", font=("Arial", 16, "bold"), command=save_changes).pack(side="left",
                                                                                                         padx=10)
        ctk.CTkButton(buttons_frame, text="Cancel", font=("Arial", 16, "bold"), command=editor_window.destroy).pack(
            side="right", padx=10)

    def update_labels(self):
        """
        Updates all labels in the app based on the current config.
        Also refreshes category list and modes display if needed.
        """
        for key, widget in self.label_widgets.items():
            if key == "directory_label":
                widget.configure(text=self.config["Labels"][key].format(path=self.main_folder))
            else:
                widget.configure(text=self.config["Labels"][key])

        self.category_instance.get_categories()
        if self.category_instance.scrl_frame:
            for widget in self.category_instance.scrl_frame.winfo_children():
                widget.destroy()
            self.category_instance.segmented_buttons()

        if hasattr(self, 'modes_list') and self.modes_list:
            display_entries_list = "\n".join(self.modes_list)
            self.label_widgets["mode_display_label"].configure(
                text=f"{self.config['Labels']['mode_display_label']}\n{display_entries_list}")

    def config_tab(self, tab_frame):
        """
        creates a frame to manage main directory.
        adds a switch to toggle Recordings and Pictures folders creation inside the project folder.
        added for customizability in the future.

        things to add here:
        """
        path_frame = ctk.CTkFrame(tab_frame)  # create a frame for path management
        path_frame.pack(side="top", fill="both", expand=True)

        directory_label = ctk.CTkLabel(path_frame, text=self.config["Labels"]["directory_label"].format(path=self.main_folder),
                                       font=("Arial", 16, "bold"))
        directory_label.pack(pady=20) # adds a label that tells us the current main directory

        warning_label = ctk.CTkLabel(path_frame,
                                     text=self.config["Labels"]["warning_label"],
                                     font=("Arial", 16, "bold"), text_color="#ff4249")
        warning_label.pack(pady=20)  # creates label that warns about changing main directory.

        edit_labels_button = ctk.CTkButton(path_frame, width=150, height=50, text="Edit Labels",
                                           font=("Arial", 20, "bold"), command= self.open_config_editor)
        edit_labels_button.pack(pady=10)

        self.inner_switch = inner_folders_switch_state(path_frame)

    def modes_config(self, tab):
        """uses a class AddModeLogic, in the end, stores a mode list in a variable.

        uses the custom class to add a button that
        adds entries and a modes tracker"""
        mode_logic = AddModeLogic(tab, self.config)
        self.modes_list = mode_logic.get_list()

        confirm_button = ctk.CTkButton(tab, text="Create",
                                       width=250, height=100,
                                       command=lambda: self.folder_creation_handler(),  # see folder_creation_handler
                                       font=("Arial", 22, "bold"), )
        confirm_button.pack(pady=15)

    def folder_creation_handler(self):
        """
            Creates a folder structure based on the provided parameters.

            Parameters:
            - main_dir : The main directory where the project will be created.
            - category_path : Path inside the category.
            - project_name : The project name.
            - modes_list : A list of mode names.
            - inner_switch: If True, create "Recordings" and "Pictures" folders and add mode folders in them.

            Shows popup when done.
            """
        self.project_name = self.project_name.get()
        category_path = self.category_instance.cat_path
        if self.project_name == "":
            self.project_name = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())
        if category_path == "":
            uncategorized = os.path.join(self.main_folder, "חסר קטגוריה")
            os.makedirs(uncategorized, exist_ok=True) # in case no category were chosen, create uncategorized directory and store the project there
            category_path = uncategorized
        project_path = str(os.path.join(category_path, self.project_name)) # Define the project path
        os.makedirs(project_path, exist_ok=True) # Create the project folder
            # If the switch is True, create "Recordings" and "Pictures" folders and mode subfolders
        if self.inner_switch.get():
            for subfolder in ['Recordings', 'Pictures']:
                subfolder_path = os.path.join(project_path, subfolder)
                os.makedirs(subfolder_path, exist_ok=True)
                # Create mode subfolders inside "Recordings" and "Pictures"
                for mode in self.modes_list:
                    mode_folder_path = os.path.join(subfolder_path, mode)
                    os.makedirs(mode_folder_path, exist_ok=True)

        else: # Only create modes folders inside project folder.
            for mode in self.modes_list:
                mode_folder_path = os.path.join(project_path, mode)
                os.makedirs(mode_folder_path, exist_ok=True)
        show_project_creation_popup(project_path)


class CategoriesLogic:
    def __init__(self, frame, config):
        self.frame = frame
        self.config = config
        self.main_folder:str = self.config["Paths"].get("main_directory")
        self.cat_list:list = []
        self.cat_dict:dict = {}
        self.cat_path:str = ""  # this is what I need in the end
        self.scrl_frame = None

        self.get_categories()
        self.scrl_frame = self.scrollable_frame_creation()
        self.segmented_buttons()

    def scrollable_frame_creation(self):
        scrollable_frame = ctk.CTkScrollableFrame(self.frame, height=150,
                                                             orientation="horizontal", label_text="Choose Category:",
                                                             label_font=("Arial", 16, "bold"))
        scrollable_frame.pack(pady=10, fill="both")
        # creates a scrollable frame that will store the categories as segmented buttons
        return scrollable_frame

    def get_categories(self):
        """
                    makes a list out of the folders in the main directory,
                    then it assigns to a dictionary the key as the category name and
                    the value as its path (inside the category folder)

                    returns a dict.
                    key: category name.
                    value: path inside corresponding category.
                    """
        self.cat_list = os.listdir(self.main_folder)  # makes a list out of the folders in default path.
        for i in range(len(self.cat_list)):  # makes dictionary,the key is the category and the value is the path
            self.cat_dict[self.cat_list[i]] = os.path.join(self.main_folder,
                                                             self.cat_list[i])  # joins the main path with the
            # category name to form a category path.

    def segmented_buttons(self):
        seg_buttons = ctk.CTkSegmentedButton(self.scrl_frame,
                                                 width=500,
                                             height=150,
                                             font=("Arial", 22),
                                             dynamic_resizing=True,
                                             border_width=10,
                                             corner_radius=10,
                                             values=self.cat_list,
                                             fg_color="#2B2B2B",
                                             command=lambda value: self.get_inside_category_path(value,self.cat_dict))
        seg_buttons.pack(padx=5)  # creates a segmented buttons to choose a category from the main directory.

    def get_inside_category_path(self, category, dictionary):
        self.cat_path = dictionary[category]

class AddModeLogic:
    """Creates a class that has its own frame,
    it creates a button that each time you press it, it adds an entry.
    also, it has an entry counter and a self updating label that indicated the number
    of entries. """
    def __init__(self, frame, config):
        """creates a counter
        creates a frame
        creates a button
        creates a label"""
        self.frame = frame
        self.config = config
        self.entries_list = []  # # This holds the list of entries
        self.alert_label = None  # Initialize the alert label to make sure only 1 label will show at a time


        # Create a Scrollable frame for modes.
        self.modes_frame = ctk.CTkScrollableFrame(frame)
        self.modes_frame.pack(side="top", fill="both", expand=True)

        # Add a Label
        self.modes_tab_label = ctk.CTkLabel(self.modes_frame, text=self.config["Labels"]["modes_tab_label"], font=("Arial", 24, "bold"))
        self.modes_tab_label.pack(pady=10) # creates label
        self.assign_instruction = ctk.CTkLabel(self.modes_frame, text=self.config["Labels"]["assign_instruction"], font=("Arial", 16, "bold"))
        self.assign_instruction.pack(pady=5) # creates label

        self.add_entry()

        # Label to show the entry count
        self.mode_display_label = ctk.CTkLabel(self.modes_frame, text=self.config["Labels"]["mode_display_label"], font=("Arial", 16, "bold"))
        self.mode_display_label.pack(pady=5, side="top")

    def add_entry(self):
        """Adds a new entry field with the number of the mode."""
        new_entry = ctk.CTkEntry(self.modes_frame, width=250, placeholder_text="Enter Mode: ")
        new_entry.pack(pady=5, side="top")
        new_entry.bind("<Return>", self.on_enter)

        return new_entry

    def on_enter(self, event):
        """Gets the text from the entry when Enter is pressed.
        Checks if the mode name is valid and there are no duplicates in the modes list,
        in case an invalid name has been entered, puts an alert on the screen and does not append the mode to the list."""
        entry_text = event.widget.get()  # Get the text from the widget that triggered the event
        if entry_text not in self.entries_list and entry_text.strip():
            # This validates that there are no duplicates in modes list, and an actual name (not just whitespaces)
            self.entries_list.append(entry_text) # Appends the Mode to a modes list
            display_entries_list = "\n".join(self.entries_list)
            self.mode_display_label.configure(
            text=f"{self.config['Labels']['mode_display_label']}\n{display_entries_list}") # displays the number of modes and the modes list
            event.widget.delete(0, ctk.END)  # Clears the entry

        else:
            # Creates an alert label in case the name is invalid
            if self.alert_label is None or not self.alert_label.winfo_exists():
                # Create the alert label only if it doesn't already exist or is not visible
                self.alert_label = ctk.CTkLabel(self.modes_frame, text_color="red", font=("Arial", 16),
                                       text=self.config["Labels"]["invalid_mode_alert"])  # Creates an alert label in case the name is invalid
            self.alert_label.pack()
            self.modes_frame.after(1000, self.alert_label.pack_forget)


    def get_list(self):
        return self.entries_list


def load_default_path():
    """
    This function loads the last default path that has been chosen since changing a main directory.
    It stores the last path in a config.txt file.
    if there is no config file, the default path will be C:/Users/User/Desktop/Iron Swords War like in the StormCase laptop.
    to prevent saving an empty directory, it will save a directory only if one will be chosen.
    """
    config = load_config()
    return config["Paths"].get("main_directory")


def load_config():
    """
    Reads config.txt and returns a dictionary with sections and key-value pairs.
    Creates an empty config if the file is missing or raises an error on parsing issues.
    """
    config_file = "config.txt"
    config = {"Paths": {}, "Labels": {}}

    if not os.path.exists(config_file):
        print(f"Config file '{config_file}' not found. Creating empty config.")
        return config

    try:
        with open(config_file, "r", encoding="utf-8") as f:
            current_section = None
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("[") and line.endswith("]"):
                    current_section = line[1:-1]
                    if current_section not in config:
                        config[current_section] = {}
                elif "=" in line and current_section:
                    key, value = line.split("=", 1)
                    # Decode escaped characters like \n
                    value = bytes(value.strip(), "utf-8").decode("unicode_escape")
                    config[current_section][key.strip()] = value
    except UnicodeDecodeError:
        raise Exception(f"Error: '{config_file}' has invalid encoding. Ensure it is UTF-8.")
    except Exception as e:
        raise Exception(f"Error reading '{config_file}': {e}")

    if "Paths" not in config:
        config["Paths"] = {}
    if "Labels" not in config:
        config["Labels"] = {}

    return config


def save_default_path(path):
    """
    Updates the main directory path in config.txt.
    :param path: str, the new directory path.
    """
    config = load_config()
    config["Paths"]["main_directory"] = path
    save_config(config)


def app_initialization():
    """This is where it all begins..."""
    ctk.set_appearance_mode("dark")  # dark mode
    root.title("RFeye Site Helper V1.2")  # set app title
    root.geometry("500x550")  # Set the window size

    welcome_screen() # runs first welcome screen
    root.mainloop()  # starts GUI

def welcome_screen():
    """
    Creates a main frame and introduction to the app
    creates 2 buttons to either create a new project or close the app.
    """
    config = load_config()
    welcome_frame = ctk.CTkFrame(root)
    welcome_frame.pack(side="top", fill="both", expand=True)  # create welcome frame

    welcome_label = ctk.CTkLabel(welcome_frame, text=config["Labels"]["welcome_label"], font=("Arial", 24, "bold"))
    welcome_label.pack(pady=15) # creates label

    instruction_label = ctk.CTkLabel(welcome_frame, text=config["Labels"]["instruction_label"],
                                     font=("Arial", 18, "bold"))
    instruction_label.pack(pady=5)  # creates label

    instruction_label2 = ctk.CTkLabel(welcome_frame, text=config["Labels"]["instruction_label2"],
                                     font=("Arial", 24, "bold"))
    instruction_label2.pack(pady=15) # creates label

    buttons_frame = ctk.CTkFrame(root)  # create buttons frame
    buttons_frame.pack(side="bottom", expand=True, pady=20, anchor="center")
    new_project_button = ctk.CTkButton(buttons_frame, width=200, height=100, text="New Project", font=("Arial", 22, "bold"),
                                       command=on_new_project_window_button,
                                       hover_color='#6796e0', fg_color="#3873d1")
    new_project_button.pack(side="left", padx=10) # new project button
    close_window_button = ctk.CTkButton(buttons_frame, width=200, height=100, text="Close Window", font=("Arial", 22, "bold"),
                                        command=lambda :root.destroy(),
                                        hover_color='#6796e0', fg_color="#3873d1")
    close_window_button.pack(side="right", padx=10) # close app button

def on_new_project_window_button():
    """Runs in the event of pressing the New Project button.
    Removes all Frames from root,
    runs the Tabs class logic.
    See class Tabs for more documentation.
    """
    forget_all_frames()  # forget current frames
    Tabs(master=root) # runs Class Tabs Logic

def forget_all_frames():
    """Removes all frames, widgets, and scrollableFrames from root"""
    for widget in root.winfo_children():
        if isinstance(widget, (ctk.CTkFrame, ctk.CTkScrollableFrame)):
            widget.pack_forget()

def get_project_name(frame):
    """
    Creates an entry that gets project name, returns type ctk entry of project name.
    :param: frame
    :return: project_name_entry
    """
    entry_placeholder_font = ("Arial", 20)  # custom font for the placeholder text in the project name entry
    project_name_entry = ctk.CTkEntry(frame, width=300, border_color="black",
                                  placeholder_text="Enter Project name here", font=entry_placeholder_font)
    project_name_entry.pack(pady=10) # creates an entry for project name
    return project_name_entry

def inner_folders_switch_state(frame):
    """
    Creates a switch to ask if user wants to create Recordings and Pictures
    folders inside the new project folder.
    Sets switch value as 1 on default.
    :param frame: root/frame
    :return: recs_and_pics_switch
    """
    recs_and_pics_switch = ctk.CTkSwitch(frame,
                                         text="Create Recordings and Photos Folders [Recommended]",
                                         font=("Arial", 16, "bold"), hover=True)
    # create a switch to allow creation of recordings and pictures folders inside the new project folder
    recs_and_pics_switch.select()  # makes the switch turned on by default.
    recs_and_pics_switch.pack(pady=20)
    return  recs_and_pics_switch

def choose_directory(current_path, directory_label, tabs_instance):
    """
    Opens a file dialog to choose a directory to read folders from.
    Updates the main directory in config.txt and Tabs instance.
    :param current_path: Current path from config.txt
    :param directory_label: Label to update with new path
    :param tabs_instance: Tabs instance to update main_folder
    """
    selected_directory = filedialog.askdirectory()
    if selected_directory != current_path and selected_directory:
        tabs_instance.main_folder = selected_directory
        save_default_path(selected_directory)
        directory_label.configure(text=tabs_instance.config["Labels"]["directory_label"].format(path=selected_directory))

def change_directory_popup(current_path, directory_label, tabs_instance):
    """Opens a Popup to confirm main directory change."""
    warning_popup = ctk.CTkToplevel()
    warning_popup.title("Are you sure?")
    warning_label = ctk.CTkLabel(warning_popup, text_color="red", font=("Arial", 18),
                                 text="Are you sure that you\n want to change Main Directory?\n This can make errors in the application.")
    warning_label.pack(pady=10)

    change_button = ctk.CTkButton(warning_popup, text="Change Anyways",
                                  text_color="red", font=("Arial", 16, "bold"),
                                  command=lambda: choose_directory(current_path, directory_label, tabs_instance))
    change_button.pack(pady=10, side="left")

    cancel_button = ctk.CTkButton(warning_popup, text="Cancel", font=("Arial", 16, "bold"),
                                  command=lambda: warning_popup.destroy())
    cancel_button.pack(pady=10, side="right")
    warning_popup.transient(root)
    warning_popup.grab_set()
    warning_popup.focus_force()

def show_project_creation_popup(new_project_path):
    """creates a popup window upon project creation.
    adds a button to close popup and app,
    and button to open containing folder."""
    popup = ctk.CTkToplevel()
    popup.geometry("300x150")
    popup.title("Success!")
    label = ctk.CTkLabel(popup, text=load_config()["Labels"]["success_popup_label"], font=("Arial", 16, "bold"))
    label.pack(pady=20)

    close_button = ctk.CTkButton(popup, text="Open Folder",font=("Arial", 16, "bold"), command=lambda: os.startfile(new_project_path))
    close_button.pack(side="left", pady=10, padx=10)
    close_button = ctk.CTkButton(popup, text="Close App",font=("Arial", 16, "bold"), command=lambda: root.destroy())
    close_button.pack(side="right", pady=10, padx=10)
    # Make the popup modal
    popup.transient(root)
    # Set focus to the popup window
    popup.focus_force()

def no_category_popup(tab):
    """raises a popup in case no category has been chosen. has 2 buttons: either continue in an uncategorized folder or choose category"""
    popup = ctk.CTkToplevel()
    popup.title("Are you Sure?")
    label = ctk.CTkLabel(popup,
                         text=load_config()["Labels"]["no_category_popup_label"],
                         font=("Arial", 16, "bold"))
    label.pack(pady=10)

    close_button = ctk.CTkButton(popup, text="Ok", font=("Arial", 16, "bold"), command=lambda: popup.destroy())
    close_button.pack(side="right", pady=10, padx=10)
    # a button to choose category (sends you to the main tab to choose category)
    close_button = ctk.CTkButton(popup, text="Choose Category", font=("Arial", 16, "bold"), fg_color="green", command=lambda: (tab.set("Main"), popup.destroy()))
    close_button.pack(side="left",pady=10, padx=10)

    # Make the popup modal
    popup.grab_set()
    popup.transient(root)
    # Set focus to the popup window
    popup.focus_force()
