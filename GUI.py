import os.path
from tkinter import *
import tkinter as tk
import json
from datetime import datetime
from collections import deque
from queue import PriorityQueue
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chromedriver_path = 'chromedriver.exe'
webdriver.chrome.driver = chromedriver_path
chrome_options = Options()
chrome_options.add_argument('--ignore-proxy')

driver = webdriver.Chrome(options=chrome_options)

class GUI:
    def __init__(self, fields, file_paths, start_file=None, checkpoint=None):
        # TKINTER PARAMS
        self.window_geometry = "900x1000"
        self.frame_width = 900
        self.frame_height = 1000

        self.win = Tk()
        self.win.geometry(self.window_geometry)

        self.line_idx = 0
        self.lines = None
        self.current_file_path = ""

        self.properties = fields.pop("list")
        self.fields = fields
        self.file_paths = file_paths

        self.settings_checkboxes_list = ["auto_next", "periodic_cache", "enable_undo"]
        self.unmodifiable_fields_list = ["content_field", "error_field"]
        self.addn_func_list = ["frequently_used", "custom_categories", "recently_used"]

        # MANAGEMENT DICTS
        self.unmodifiable_fields_variable = dict()
        self.property_field_variable = dict()
        self.keep_checkboxes_variable = dict()
        self.auto_inc_checkboxes_variable = dict()
        self.settings_checkboxes_variable = dict()

        self.button_dict = dict()
        self.property_fields = dict()
        self.unmodifiable_fields = dict()

        self.undo_buttons = dict()
        self.add_buttons = dict()
        self.append_buttons = dict()
        self.keep_checkboxes = dict()
        self.auto_inc_checkboxes = dict()
        self.settings_checkboxes = dict()

        self.addn_func = dict()

        self.settings_checkboxes_labels = dict()

        self.undo_cache = dict()

        self.trav_buffer = dict()

        self.field_labels = dict()

        for i in self.unmodifiable_fields_list:
            self.unmodifiable_fields_variable[i] = tk.StringVar()
            self.unmodifiable_fields_variable[i].set("")

        # Property Fields
        for i in self.properties:
            self.property_field_variable[i] = tk.StringVar()
            self.property_field_variable[i].set(self.fields[i]["init"])

        # Keep Text Var
        for i in self.properties:
            self.keep_checkboxes_variable[i] = tk.BooleanVar()

        for i in self.properties:
            if fields[i]["type"] == "numeric":
                self.auto_inc_checkboxes_variable[i] = tk.BooleanVar()

        for i in self.settings_checkboxes_list:
            self.settings_checkboxes_variable[i] = tk.BooleanVar()

        for i in self.properties:
            self.undo_cache[i] = []

        for i in self.properties:
            self.trav_buffer[i] = ""

        for i in self.properties:
            if len(self.fields[i]["additional_functionality"]) >= 1:
                self.addn_func[i] = dict()
                for addn_func in self.fields[i]["additional_functionality"]:
                    if addn_func not in self.addn_func_list: self.warning(
                        f"{i} -> additional_functionality -> {addn_func} is invalid")
                    self.addn_func[i][addn_func] = dict()
                    self.addn_func[i][addn_func]["items"] = []
                    self.addn_func[i][addn_func]["buttons"] = []
                    self.addn_func[i][addn_func]["current_group"] = 1
                    if addn_func == "custom_categories": self.addn_func[i][addn_func]["data"] = 1
                    if addn_func == "recently_used": self.addn_func[i][addn_func]["data"] = deque()
                    if addn_func == "frequently_used": self.addn_func[i][addn_func]["data"] = {}

        # Text Field
        self.periodic_cache_current_value = 0
        self.periodic_cache_max_value = 10

        self.init_config()

        if len(self.file_paths) != len(set(self.file_paths)):
            self.warning("File Path Provided contains duplicates")

        def read_file_init():
            if start_file is None:
                self.read_file(path=self.file_paths[0])
            else:
                if type(start_file) is int:
                    self.read_file(path=self.file_paths[start_file])
                elif type(start_file) is str:
                    self.read_file(path=start_file)

        if checkpoint is None or type(checkpoint) is not str:
            self.warning(
                "Invalid Checkpoint. Starting with empty json")
            self.json_data_list = []
            read_file_init()
        else:
            if not os.path.isfile(checkpoint):
                self.warning(
                    "Checkpoint file does not exist. Starting with empty json. File will be created on Dump")
                self.json_data_list = []
                read_file_init()
            else:
                self.json_data_list = self.load_json(checkpoint)
                if len(self.json_data_list) == 0:
                    self.warning(
                        "Checkpoint file is empty. Starting with empty json")
                    self.json_data_list = []
                    read_file_init()
                else:
                    self.read_file(path=self.json_data_list[-1]['file'])
                    self.line_idx = self.json_data_list[-1]['last_line_idx'] + 1

        self.trav_current_idx = len(self.json_data_list)
        self.update_property_fields(fields='all')

    def warning(self, text, how='beginning'):
        if how == 'beginning':
            self.unmodifiable_fields_variable[self.unmodifiable_fields_list[1]].set(
                text + '\n' + self.unmodifiable_fields_variable[self.unmodifiable_fields_list[1]].get())
        elif how == 'delete':
            self.unmodifiable_fields_variable[self.unmodifiable_fields_list[1]].set(text + '\n')
        self.update_property_fields(fields='warning')

    def create_additional_functionality_buttons(self, property, func_obj):
        for key in func_obj.keys():
            x_init = 0
            group = func_obj[key]["current_group"]

            if len(func_obj[key]["items"]) == 0:
                obj_list = ["", "", "", ""]
            elif len(func_obj[key]["items"]) < group * 4:
                obj_list = func_obj[key]["items"][(group - 1) * 4:]
                while len(obj_list) < 4: obj_list.append("")
            else:
                obj_list = func_obj[key]["items"][(group - 1) * 4:group * 4]

            func_obj[key]["buttons"].append(tk.Button(self.win, text="<",
                                                      command=lambda property=property, addn_func=key:
                                                      self.left_button(property, addn_func), height=1, width=3))
            func_obj[key]["buttons"][0].place(x=x_init, y=self.y)

            x_init += 31

            for i in range(1, 5):
                func_obj[key]["buttons"].append(
                    tk.Button(self.win, text=obj_list[i - 1],
                              command=lambda property=property, item=obj_list[i - 1]:
                              self.functionality_button_action(property, item), height=1,
                              width=18))
                func_obj[key]["buttons"][i].place(x=x_init, y=self.y)
                x_init += 136

            func_obj[key]["buttons"].append(tk.Button(self.win, text=">",
                                                      command=lambda property=property, addn_func=key:
                                                      self.right_button(property, addn_func)
                                                      , height=1, width=3))
            func_obj[key]["buttons"][5].place(x=x_init, y=self.y)
            x_init += 31

            func_obj[key]["buttons"].append(tk.Button(self.win, text="R",
                                                      command=lambda property=property, addn_func=key:
                                                      self.additional_functionality_reset(property, addn_func)
                                                      , height=1, width=3))
            func_obj[key]["buttons"][6].place(x=x_init, y=self.y)

            self.field_labels[key] = tk.Label(self.win, text=key.replace('_', ' ').title())
            self.field_labels[key].place(x=x_init + 45, y=self.y)

            self.y += 32

    def update_additional_functionality_lists(self):
        for i in self.properties:
            if len(self.fields[i]["additional_functionality"]) > 0:
                for addn_func in self.addn_func[i].keys():
                    if addn_func == "frequently_used":
                        if len(self.addn_func[i][addn_func]["data"]) > 12:
                            self.addn_func[i][addn_func]["items"] = sorted(self.addn_func[i][addn_func]["data"],
                                                                           key=lambda k:
                                                                           self.addn_func[i][addn_func]["data"][k],
                                                                           reverse=True)[:12]
                        else:
                            self.addn_func[i][addn_func]["items"] = sorted(self.addn_func[i][addn_func]["data"],
                                                                           key=lambda k:
                                                                           self.addn_func[i][addn_func]["data"][k],
                                                                           reverse=True)
                    if addn_func == "recently_used":
                        self.addn_func[i][addn_func]["items"] = list(self.addn_func[i][addn_func]["data"])[::-1]

    def update_additional_functionality(self):
        for i in self.properties:
            if len(self.fields[i]["additional_functionality"]) > 0:
                categories = self.property_field_variable[i].get().split(',')
                categories = [i.strip() for i in categories]
                categories = [i.strip('\n') for i in categories]
                for addn_func in self.addn_func[i].keys():
                    if addn_func == "frequently_used":
                        for x in categories:
                            if x in self.addn_func[i][addn_func]["data"]:
                                self.addn_func[i][addn_func]["data"][x] += 1
                            else:
                                self.addn_func[i][addn_func]["data"][x] = 1
                    if addn_func == "recently_used":
                        for x in categories:
                            if len(self.addn_func[i][addn_func]["data"]) >= 12:
                                self.addn_func[i][addn_func]["data"].popleft()
                                self.addn_func[i][addn_func]["data"].append(x)
                            else:
                                self.addn_func[i][addn_func]["data"].append(x)
        self.update_additional_functionality_lists()
        self.update_addtional_funtionality_button()

    def update_addtional_funtionality_button(self):
        for property in self.properties:
            if len(self.fields[property]["additional_functionality"]) > 0:
                for addn_func in self.addn_func[property].keys():
                    group = self.addn_func[property][addn_func]["current_group"]

                    if len(self.addn_func[property][addn_func]["items"]) == 0:
                        obj_list = ["", "", "", ""]
                    elif len(self.addn_func[property][addn_func]["items"]) < group * 4:
                        obj_list = self.addn_func[property][addn_func]["items"][(group - 1) * 4:]
                        while len(obj_list) < 4: obj_list.append("")
                    else:
                        obj_list = self.addn_func[property][addn_func]["items"][(group - 1) * 4:group * 4]

                    for i in range(1, 5):
                        self.addn_func[property][addn_func]["buttons"][i].config(text=obj_list[i - 1],
                                                                                 command=lambda property=property,
                                                                                                item=obj_list[i - 1]:
                                                                                 self.functionality_button_action(
                                                                                     property, item))

    def left_button(self, property, addn_func):
        group = self.addn_func[property][addn_func]["current_group"] - 1
        if group == 0:
            if len(self.addn_func[property][addn_func]["items"]) % 4 == 0:
                group = (len(self.addn_func[property][addn_func]["items"]) // 4)
            else:
                group = (len(self.addn_func[property][addn_func]["items"]) // 4) + 1

        self.addn_func[property][addn_func]["current_group"] = group

        self.update_addtional_funtionality_button()

    def right_button(self, property, addn_func):
        group = self.addn_func[property][addn_func]["current_group"] + 1

        if group > len(self.addn_func[property][addn_func]["items"]) // 4:
            if len(self.addn_func[property][addn_func]["items"]) % 4 == 0:
                group = 1
            if group - len(self.addn_func[property][addn_func]["items"]) // 4 > 1:
                group = 1

        self.addn_func[property][addn_func]["current_group"] = group

        self.update_addtional_funtionality_button()

    def additional_functionality_reset(self, property, addn_func):
        if addn_func == "custom_categories":
            if 'entry_box' not in self.addn_func[property][addn_func]:
                for button in self.addn_func[property][addn_func]["buttons"][0:-1]:
                    button.place_forget()
                string_variable = tk.StringVar()
                string_variable.set(','.join(self.addn_func[property][addn_func]['items']))
                self.addn_func[property][addn_func]["entry_box"] = tk.Text(self.win, height=1, width=47)
                self.addn_func[property][addn_func]["entry_box"].place(
                    x=self.addn_func[property][addn_func]["buttons"][0].winfo_x(),
                    y=self.addn_func[property][addn_func]["buttons"][0].winfo_y())
                self.addn_func[property][addn_func]["entry_box"].delete("1.0", tk.END)
                self.addn_func[property][addn_func]["entry_box"].insert(tk.END, string_variable.get())

            else:
                for button in self.addn_func[property][addn_func]["buttons"][0:-1]:
                    button.place(x=button.winfo_x(), y=button.winfo_y())
                string_variable = tk.StringVar()
                string_variable.set(self.addn_func[property][addn_func]["entry_box"].get("1.0", tk.END))
                self.addn_func[property][addn_func]["entry_box"].destroy()
                self.addn_func[property][addn_func].pop("entry_box")
                string_variable = string_variable.get().split(',')
                string_variable = [i for i in string_variable if i != ""]
                string_variable = [i.strip('\n') for i in string_variable if i != ""]
                if len(string_variable) > 12:
                    self.warning("More than 12 items entered. Selecting only first 12")
                    self.addn_func[property][addn_func]['items'] = string_variable[:12]
                else:
                    self.addn_func[property][addn_func]['items'] = string_variable

        if addn_func == "frequently_used":
            self.addn_func[property][addn_func]["items"] = []
            self.addn_func[property][addn_func]["current_group"] = 1
            self.addn_func[property][addn_func]["data"] = PriorityQueue()
            self.addn_func[property][addn_func]["data"] = {}

        if addn_func == "recently_used":
            self.addn_func[property][addn_func]["current_group"] = 1
            self.addn_func[property][addn_func]["data"] = deque()
            self.addn_func[property][addn_func]["items"] = list(self.addn_func[property][addn_func]["data"])

        self.update_addtional_funtionality_button()

    def functionality_button_action(self, id, item):
        text = self.property_field_variable[id].get()
        text = text.split(", ")

        if "" in text:
            text.remove("")

        if item in text:
            text.remove(item)
        else:
            text.append(item)
        self.property_field_variable[id].set(', '.join(text))

        self.update_property_fields(fields='property')

    def preview(self):
        preview_window = tk.Toplevel(self.win)
        preview_window.title("Preview")
        preview_window.geometry("800x800")

        variables = dict()
        labels = dict()
        texts = dict()

        x = 10
        y = 10
        for i in self.properties:
            height = int(self.fields[i]["height"]) * 4
            variables[i] = tk.StringVar()
            variables[i].set(self.property_field_variable[i].get())
            labels[i] = tk.Label(preview_window, text=i.title())
            labels[i].place(x=10, y=y)
            texts[i] = tk.Text(preview_window, width=85, height=height)
            texts[i].insert(tk.END, variables[i].get())
            texts[i].place(x=100, y=y)

            y += (height * 16) + 10

        def save_fields():
            for i in self.properties:
                self.property_field_variable[i].set(variables[i].get())
            self.update_property_fields()
            preview_window.destroy()

        def cancel_preview():
            preview_window.destroy()

        save_button = tk.Button(preview_window, text="Save Changes", command=save_fields)
        save_button.place(x=650, y=750)

        cancel_button = tk.Button(preview_window, text="Cancel", command=cancel_preview)
        cancel_button.place(x=750, y=750)

    def load_json(self, path):
        with open(path, 'rb') as file:
            data = json.load(file)
        file.close()
        return data

    def add_button(self, text_entry, id):
        for i in self.properties:
            if self.property_field_variable[i].get() != self.property_fields[i].get("1.0", END):
                self.undo_cache[i].append(self.property_field_variable[i].get())
                self.property_field_variable[i].set(self.property_fields[i].get("1.0", END))

        if self.property_field_variable[id].get() != self.property_fields[id].get("1.0", END):
            self.undo_cache[id].append(self.property_field_variable[id].get())
            self.undo_cache[id].append(self.property_fields[id].get("1.0", END))
        else:
            self.undo_cache[id].append(self.property_field_variable[id].get())
        self.property_field_variable[id].set(text_entry.get())
        self.update_property_fields()

        if self.settings_checkboxes_variable["periodic_cache"].get():
            temp = []
            for i in self.properties:
                temp.append(self.property_field_variable[i].get())

        if self.settings_checkboxes_variable["auto_next"].get():
            self.next()

    def append_button(self, text_entry, id):
        for i in self.properties:
            if self.property_field_variable[i].get() != self.property_fields[i].get("1.0", END):
                self.undo_cache[i].append(self.property_field_variable[i].get())
                self.property_field_variable[i].set(self.property_fields[i].get("1.0", END))

        if self.property_field_variable[id].get() != self.property_fields[id].get("1.0", END):
            self.undo_cache[id].append(self.property_field_variable[id].get())
            self.undo_cache[id].append(self.property_fields[id].get("1.0", END))
            self.property_field_variable[id].set(self.property_fields[id].get("1.0", END) + text_entry.get())
        else:
            self.undo_cache[id].append(self.property_field_variable[id].get())
            self.property_field_variable[id].set(self.property_field_variable[id].get() + text_entry.get())
        self.update_property_fields()

        if self.settings_checkboxes_variable["periodic_cache"].get():
            temp = []
            for i in self.properties:
                temp.append(self.property_field_variable[i].get())

        if self.settings_checkboxes_variable["auto_next"].get():
            self.next()

    def dump(self):
        with open("struc_data.json", "w") as json_file:
            json.dump(self.json_data_list, json_file)
        json_file.close()
        pass

    def cache(self):
        f_name = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        with open(f"Cache/{f_name}.json", "w") as json_file:
            json.dump(self.json_data_list, json_file)
        json_file.close()
        pass

    def save(self):
        if self.trav_current_idx != len(self.json_data_list):
            self.warning(
                "WARNING: Use update to save changes to this item. \nAPP DOES NOT SUPPORT SAVING EXISTING OBJECTS AS NEW OBJECTS")
            return

        for i in self.properties:
            self.property_field_variable[i].set(self.property_fields[i].get("1.0", tk.END))

        json_obj = self.get_obj()
        self.update_additional_functionality()

        for i in self.properties:
            json_obj[i] = self.property_field_variable[i].get()

            if i in self.auto_inc_checkboxes.keys():
                if self.auto_inc_checkboxes_variable[i].get():
                    self.property_field_variable[i].set(str(int(self.property_field_variable[i].get()) + 1))
                else:
                    self.property_field_variable[i].set("")

            if not self.keep_checkboxes_variable[i].get() and i not in self.auto_inc_checkboxes.keys():
                self.property_field_variable[i].set("")

            self.undo_cache[i] = []

        json_obj["last_line_idx"] = self.line_idx
        json_obj["file"] = self.current_file_path

        self.json_data_list.append(json_obj)

        if self.settings_checkboxes_variable["enable_undo"].get():
            if self.periodic_cache_current_value == self.periodic_cache_max_value:
                self.periodic_cache_current_value = 0
                self.cache()
            else:
                self.periodic_cache_current_value += 1

        self.update_property_fields()
        self.trav_current_idx += 1

    def get_obj(self):
        temp = {}
        for i in self.properties:
            temp[i] = ""

        temp["last_line_idx"] = 0
        temp["file"] = ""
        return temp

    def read_file(self, path="Files/file.txt", line_index=0):
        self.line_idx = line_index
        self.current_file_path = path

        with open(path, 'rb') as file:
            self.lines = file.readlines()
            self.lines = [i.decode("utf-8", errors="backslashreplace") for i in self.lines]

        self.unmodifiable_fields_variable[self.unmodifiable_fields_list[0]].set(str(self.lines[self.line_idx]))
        self.property_field_variable['link'].set(self.lines[0])
        driver.get(self.property_field_variable['link'].get())
        self.update_property_fields(fields='all')

    def next(self):
        if self.lines is None:
            self.read_file(self.file_paths[0])

        if self.line_idx + 1 == len(self.lines):
            self.read_file(self.file_paths[self.file_paths.index(self.current_file_path) + 1])
            self.line_idx = -1

        self.line_idx += 1
        self.unmodifiable_fields_variable[self.unmodifiable_fields_list[0]].set(self.lines[self.line_idx])
        self.update_property_fields(fields='content')

    def prev(self):
        if self.line_idx - 1 == -1:
            self.read_file(self.file_paths[self.file_paths.index(self.current_file_path) - 1])
            self.line_idx = len(self.lines)

        self.line_idx -= 1
        self.unmodifiable_fields_variable[self.unmodifiable_fields_list[0]].set(self.lines[self.line_idx])
        self.update_property_fields(fields='content')

    def reset(self):
        if len(self.json_data_list) < 1:
            for i in self.properties:
                if self.fields[i] == 'numeric':
                    self.property_field_variable[i].set("0")
                else:
                    self.property_field_variable[i].set("")
            return

        if self.current_file_path != self.json_data_list[-1]["file"]:
            self.read_file(path=self.json_data_list[-1]["file"])

        self.line_idx = self.json_data_list[-1]["last_line_idx"]
        self.unmodifiable_fields_variable[self.unmodifiable_fields_list[0]].set(self.lines[self.line_idx])

        for i in self.properties:
            if i in self.auto_inc_checkboxes.keys():
                if self.auto_inc_checkboxes_variable[i].get():
                    self.property_field_variable[i].set(str(int(self.json_data_list[-1][i]) + 1))
                else:
                    self.property_field_variable[i].set("")

            if not self.keep_checkboxes_variable[i].get() and i not in self.auto_inc_checkboxes.keys():
                self.property_field_variable[i].set("")

            self.keep_checkboxes_variable[i].set(False)

        self.update_property_fields(fields='all')

    def undo(self, id):
        if len(self.undo_cache[id]) <= 1:
            return

        text = self.undo_cache[id].pop(-1)
        self.property_field_variable[id].set(text)
        self.update_property_fields()

    def object_undo(self):
        if len(self.json_data_list) == 0:
            for i in self.properties:
                self.property_field_variable[i].set("")
            self.update_property_fields(fields='property')
            return

        item = self.json_data_list.pop(-1)
        for i in self.properties:
            self.property_field_variable[i].set(item[i])
        self.update_property_fields(fields='property')

    def t_prev(self):
        if self.trav_current_idx < 1:
            self.trav_current_idx = 0
            return

        if self.trav_current_idx == len(self.json_data_list):
            self.trav_buffer = {i: self.property_field_variable[i].get() for i in self.properties}

        self.trav_current_idx -= 1
        item = self.json_data_list[self.trav_current_idx]

        for i in self.properties:
            self.property_field_variable[i].set(item[i])

        self.update_property_fields(fields='property')

    def t_next(self):
        if self.trav_current_idx >= len(self.json_data_list):
            self.trav_current_idx = len(self.json_data_list)
            return

        self.trav_current_idx += 1
        if self.trav_current_idx == len(self.json_data_list):
            item = self.trav_buffer
        else:
            item = self.json_data_list[self.trav_current_idx]

        for i in self.properties:
            self.property_field_variable[i].set(item[i])

        self.update_property_fields(fields='property')

    def update_trav(self):
        if self.trav_current_idx == len(self.json_data_list):
            self.warning("OBJECT DOESN'T EXIST: Save Object before updating.")
            return

        for i in self.properties:
            self.property_field_variable[i].set(self.property_fields[i].get('1.0', tk.END))
            self.json_data_list[self.trav_current_idx][i] = self.property_field_variable[i].get()
        self.warning(f"Updated object at index {self.trav_current_idx}")

    def update_property_fields(self, fields='all'):
        if fields == 'all' or fields == 'property':
            for i in self.properties:
                self.property_fields[i].delete('1.0', tk.END)
                self.property_fields[i].insert(tk.END, self.property_field_variable[i].get())

        if fields == 'all' or fields == 'content':
            self.unmodifiable_fields_variable[
                self.unmodifiable_fields_list[0]].set(self.lines[self.line_idx])
            self.unmodifiable_fields[self.unmodifiable_fields_list[0]].config(state=tk.NORMAL)
            self.unmodifiable_fields[self.unmodifiable_fields_list[0]].delete("1.0", tk.END)
            self.unmodifiable_fields[self.unmodifiable_fields_list[0]].insert(tk.END, self.unmodifiable_fields_variable[
                self.unmodifiable_fields_list[0]].get())
            self.unmodifiable_fields[self.unmodifiable_fields_list[0]].config(state=tk.DISABLED)

        if fields == 'warning':
            self.unmodifiable_fields[self.unmodifiable_fields_list[-1]].config(state=tk.NORMAL)
            self.unmodifiable_fields[self.unmodifiable_fields_list[-1]].delete("1.0", tk.END)
            self.unmodifiable_fields[self.unmodifiable_fields_list[-1]].insert("1.0",
                                                                               self.unmodifiable_fields_variable[
                                                                                   self.unmodifiable_fields_list[
                                                                                       1]].get(), "red_font")
            self.unmodifiable_fields[self.unmodifiable_fields_list[-1]].config(state=tk.DISABLED)

    def init_config(self):
        preview_button1 = tk.Button(self.win, text="Dump", command=self.dump, height=1, width=10)
        preview_button1.place(x=810, y=100)

        preview_button2 = tk.Button(self.win, text="Save", command=self.save, height=1, width=10)
        preview_button2.place(x=810, y=210)

        preview_button3 = tk.Button(self.win, text="Cache", command=self.cache, height=1, width=10)
        preview_button3.place(x=810, y=240)

        preview_button4 = tk.Button(self.win, text="Next", command=self.next, height=1, width=10)
        preview_button4.place(x=810, y=300)

        preview_button5 = tk.Button(self.win, text="Prev", command=self.prev, height=1, width=10)
        preview_button5.place(x=810, y=330)

        preview_button6 = tk.Button(self.win, text="Reset", command=self.reset, height=1, width=10)
        preview_button6.place(x=810, y=390)

        preview_button = tk.Button(self.win, text="Object Undo", command=self.object_undo, height=1, width=10)
        preview_button.place(x=810, y=420)

        preview_button = tk.Button(self.win, text="Preview Fields", command=self.preview, height=1, width=10)
        preview_button.place(x=810, y=450)

        preview_button = tk.Button(self.win, text="T Prev", command=self.t_prev, height=1, width=10)
        preview_button.place(x=810, y=510)

        preview_button = tk.Button(self.win, text="T Next", command=self.t_next, height=1, width=10)
        preview_button.place(x=810, y=540)

        preview_button = tk.Button(self.win, text="Update", command=self.update_trav, height=1, width=10)
        preview_button.place(x=810, y=570)

        self.unmodifiable_fields[self.unmodifiable_fields_list[0]] = tk.Text(self.win, height=10, width=95)
        self.unmodifiable_fields[self.unmodifiable_fields_list[0]].insert(tk.END, self.unmodifiable_fields_variable[
            self.unmodifiable_fields_list[0]].get())
        self.unmodifiable_fields[self.unmodifiable_fields_list[0]].config(state=tk.DISABLED)
        self.unmodifiable_fields[self.unmodifiable_fields_list[0]].place(x=0, y=0)
        self.unmodifiable_fields[self.unmodifiable_fields_list[1]] = tk.Text(self.win, height=6, width=90)
        self.unmodifiable_fields[self.unmodifiable_fields_list[1]].tag_configure("red_font", foreground="red")
        self.unmodifiable_fields[self.unmodifiable_fields_list[1]].insert(tk.END, self.unmodifiable_fields_variable[
            self.unmodifiable_fields_list[1]].get(), "red_font")
        self.unmodifiable_fields[self.unmodifiable_fields_list[1]].config(state=tk.DISABLED)
        self.unmodifiable_fields[self.unmodifiable_fields_list[1]].place(x=0, y=800)

        self.field_labels["Field Name"] = tk.Label(self.win, text='Field Name')
        self.field_labels["Field Name"].place(x=0, y=170)
        self.field_labels["Input Field"] = tk.Label(self.win, text='Input Field')
        self.field_labels["Input Field"].place(x=300, y=170)
        self.field_labels["Keep"] = tk.Label(self.win, text='K')
        self.field_labels["Keep"].place(x=605, y=170)
        self.field_labels["AI"] = tk.Label(self.win, text='AI')
        self.field_labels["AI"].place(x=630, y=170)
        self.field_labels["ERRORS/WARNINGS"] = tk.Label(self.win, text='ERRORS/WARNINGS')
        self.field_labels["ERRORS/WARNINGS"].place(x=0, y=770)

        self.y = 200
        for item in self.properties:
            height = int(self.fields[item]["height"]) * 2

            self.field_labels[item] = tk.Label(self.win, text=self.fields[item]["name"].title())
            self.field_labels[item].place(x=0, y=self.y)

            self.property_fields[item] = tk.Text(self.win, width=67, height=height)
            self.property_fields[item].insert(tk.END, self.property_field_variable[item].get())
            self.property_fields[item].place(x=60, y=self.y)

            self.keep_checkboxes[item] = tk.Checkbutton(self.win, variable=self.keep_checkboxes_variable[item])
            self.keep_checkboxes[item].place(x=600, y=self.y)

            if self.fields[item]['type'] == 'numeric':
                self.auto_inc_checkboxes[item] = tk.Checkbutton(self.win,
                                                                variable=self.auto_inc_checkboxes_variable[item])
                self.auto_inc_checkboxes[item].place(x=625, y=self.y)

            self.undo_buttons[item] = tk.Button(self.win, text="Undo",
                                                command=lambda text_entry=self.property_field_variable[item],
                                                               id=item: self.undo(id), height=height,
                                                width=5)
            self.undo_buttons[item].place(x=650, y=self.y)

            self.add_buttons[item] = tk.Button(self.win, text="Add", command=lambda
                text_entry=self.unmodifiable_fields_variable[self.unmodifiable_fields_list[0]],
                id=item: self.add_button(text_entry,
                                         id),
                                               height=height,
                                               width=5)
            self.add_buttons[item].place(x=700, y=self.y)

            self.append_buttons[item] = tk.Button(self.win, text="Append",
                                                  command=lambda text_entry=self.unmodifiable_fields_variable[
                                                      self.unmodifiable_fields_list[0]],
                                                                 id=item: self.append_button(
                                                      text_entry,
                                                      id),
                                                  height=height, width=5)
            self.append_buttons[item].place(x=750, y=self.y)

            self.y += height * 16 + 10

            if item in self.addn_func:
                self.create_additional_functionality_buttons(property=item, func_obj=self.addn_func[item])

        del self.y

        y = 10
        for i in self.settings_checkboxes_list:
            self.settings_checkboxes[i] = tk.Checkbutton(self.win, variable=self.settings_checkboxes_variable[i])
            self.settings_checkboxes[i].place(x=790, y=y)
            self.settings_checkboxes_labels[i] = tk.Label(self.win, text=i.replace("_", ' ').title())
            self.settings_checkboxes_labels[i].place(x=810, y=y)

            y += 20

    def run(self):
        self.win.mainloop()


__name__ = "__main__"
with open("fields.json", 'rb') as f:
    fields = json.load(f)
f.close()

with open("file_paths.txt", 'rb') as f:
    file_paths = f.readlines()
f.close()

file_paths = [i.decode('utf-8') for i in file_paths]
file_paths = [i.strip('\n') for i in file_paths]
file_paths = [i.strip('\r') for i in file_paths]
file_paths = ['docs/' + i for i in file_paths]

print(file_paths)

GUI(fields, file_paths, checkpoint='struc_data.json').run()
