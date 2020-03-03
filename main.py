from dateutil.parser import parse as date_parse
from curseforge import *
import json
import os
import easygui
from glfw_helper import Helper, imgui
import threading
from enum import Enum
from typing import Optional, Tuple
import textwrap

helper = Helper('Cursed Obsidian', 800, 600, bg=(0.2, 0.2, 0.2))

data = None
folder = None

# Utils

def save_data():
    with open(os.path.join(folder, 'obsidian.json'), 'w') as file:
        json.dump(data, file)

_button_disabled = False
def button_disable_color(condition: bool=True):
    global _button_disabled
    if condition:
        if _button_disabled:
            imgui.pop_style_color(3)
        else:
            imgui.push_style_color(imgui.COLOR_BUTTON, 0.3, 0.3, 0.3)
            imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.3, 0.3, 0.3)
            imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 0.3, 0.3, 0.3)
        _button_disabled = not _button_disabled

def get_versions(addon: Addon, sort: bool=True) -> Tuple[AddonFile]:
    files = addon.get_files()
    if sort:
        files = tuple(reversed(sorted(files, key=lambda af: date_parse(af.date))))
    return files

def download_func(use_done: bool=False, var_name: str='download_state'):
    def decorator(func):
        def wrapper(cls, *args, **kwargs):
            setattr(cls, var_name, DLState.DOWNLOADING)
            func(cls, *args, **kwargs)
            setattr(cls, var_name, DLState.DONE if use_done else DLState.IDLE)
        return wrapper
    return decorator

class DLState(Enum):
    IDLE = 0
    DOWNLOADING = 1
    DONE = 2 # not used sometimes

class MultiButton:
    """
    Wraps an Selectable across multiple widgets

    Usage:
    ```py
    button = MultiButton()
    with button:
        imgui.text('Hello')
        imgui.text('World')
    if button:
        print('Pressed')
    ```
    """
    def __init__(self, id=''):
        self.start_pos = None
        self.value = None
        self.id = id

    def __enter__(self):
        self.start_pos = imgui.get_cursor_pos()
    
    def __exit__(self, *args):
        end_pos = imgui.get_cursor_pos()
        imgui.set_cursor_pos((8, self.start_pos[1]))
        self.value = imgui.selectable(f'##0n{self.id}', width=imgui.get_window_width() - 10, height=end_pos[1] - self.start_pos[1] - 4)
        imgui.set_cursor_pos(end_pos)

    def __bool__(self):
        return self.value[0]

class EasyContext:
    def __init__(self, enter, exit):
        self.enter = enter
        self.exit = exit
    def __enter__(self):
        return self.enter()
    def __exit__(self, *_):
        return self.exit()

def revert_cursor():
    start = None
    def enter():
        nonlocal start
        start = imgui.get_cursor_pos()
        return start
    def _exit():
        imgui.set_cursor_pos(start)
    return EasyContext(enter, _exit)

# Windows

class MainW:
    @classmethod
    def render(cls):
        imgui.begin('Main', flags=imgui.WINDOW_MENU_BAR | imgui.WINDOW_NO_TITLE_BAR)

        if imgui.begin_menu_bar():
            if imgui.begin_menu('Add mod'):
                if imgui.menu_item('Search')[0]:
                    SearchModW.init()
                imgui.end_menu()
            imgui.end_menu_bar()

        for i, mod in enumerate(data['mods']):
            button = MultiButton(i)
            with button:
                imgui.begin_group()
                
                top_y = imgui.get_cursor_pos()[1]
                imgui.text(mod['name'])
                imgui.text_colored(textwrap.shorten(mod['summary'], width=70), 0.82, 0.82, 0.82)
                
                imgui.end_group()

                with revert_cursor():
                    version_name = mod['version_name']
                    imgui.set_cursor_pos((imgui.get_window_width() - len(version_name) * 7 - 8, top_y))
                    imgui.text_colored(version_name, 0.5, 0.5, 0.5)

            if button:
                imgui.set_next_window_focus()
                EditModW.init(i)
        
        imgui.end()

class EditModW:
    current_mod: Optional[dict] = None
    versions: Tuple[AddonFile] = tuple()
    selected: int = 0
    download_state: DLState = DLState.IDLE

    @classmethod
    def init(cls, mod_index: int):
        cls.current_mod = data['mods'][mod_index]

    @classmethod
    def disable(cls):
        cls.current_mod = None
        cls.versions = tuple()
        cls.selected = 0

    @classmethod
    @download_func()
    def get_versions(cls):
        cls.versions = get_versions(Addon.from_id(cls.current_mod['id']))

        cls.selected = 0
        for i, af in enumerate(cls.versions):
            if af.id == cls.current_mod['file_id']:
                cls.selected = i
                break

    @classmethod
    @download_func(use_done=True)
    def download_version(cls):
        af: AddonFile = cls.versions[cls.selected]
        af.download(folder)
        
        old_path = os.path.join(folder, cls.current_mod['file_name'])
        if os.path.isfile(old_path): # just in case
            os.remove(old_path)
        
        cls.current_mod.update({
            'version_name': af.name,
            'file_id': af.id,
            'file_name': af.file_name
        })
        save_data()
    
    @classmethod
    def render(cls):
        if cls.current_mod is None: return

        if imgui.begin('Edit mod', closable=True)[1]:
            imgui.text_colored(cls.current_mod['name'], 1, 1, 1)
            
            imgui.push_text_wrap_pos(imgui.get_window_width())
            imgui.text_colored(cls.current_mod['summary'], 0.82, 0.82, 0.82)
            imgui.pop_text_wrap_pos()

            imgui.separator()

            _, cls.selected = imgui.combo('Select version', cls.selected, [af.name for af in cls.versions])
            
            disabled = cls.download_state == DLState.DOWNLOADING
            
            button_disable_color(disabled)
            if imgui.button('Get versions') and not disabled:
                t = threading.Thread(target=cls.get_versions)
                t.start()
            button_disable_color(disabled)

            imgui.set_cursor_pos((0, imgui.get_window_height() - 32))
            imgui.separator()

            if imgui.button('OK') and cls.versions:
                imgui.open_popup('Update mod?')
            
            if cls.versions and imgui.begin_popup_modal('Update mod?', flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)[0]:
                if cls.download_state == DLState.DONE:
                    imgui.close_current_popup()
                    cls.download_state = DLState.IDLE
                imgui.begin_group()
                imgui.text('This will replace: ')
                imgui.text('with the version: ')
                imgui.end_group()

                imgui.same_line()

                imgui.begin_group()
                imgui.text_colored(cls.current_mod['version_name'], 1.0, 0.4, 0.4)
                imgui.text_colored(cls.versions[cls.selected].name, 0.4, 1.0, 0.4)
                imgui.end_group()
                
                imgui.separator()
                disable = cls.download_state != DLState.IDLE
                button_disable_color(disable)
                if imgui.button('OK', width=imgui.get_content_region_available_width() / 2 - imgui.STYLE_FRAME_PADDING) and not disable:
                    threading.Thread(target=cls.download_version).start()
                imgui.set_item_default_focus()
                imgui.same_line()
                if imgui.button('Cancel', width=imgui.get_content_region_available_width()) and not disable:
                    imgui.close_current_popup()
                button_disable_color(disable)
                imgui.end_popup()
            imgui.same_line()
            
            if imgui.button('Cancel'):
                cls.disable()

            with revert_cursor() as current_pos:
                imgui.set_cursor_pos((imgui.get_window_width() - 72, current_pos[1] - 23))
                imgui.push_style_color(imgui.COLOR_BUTTON, 0.9, 0.3, 0.3)
                imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.9, 0.4, 0.4)
                imgui.push_style_color(imgui.COLOR_BUTTON_ACTIVE, 1.0, 0.3, 0.4)
                if imgui.button('Remove', width=50):
                    imgui.open_popup('Remove mod')
                imgui.pop_style_color(3)

            if imgui.begin_popup_modal('Remove mod', flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)[0]:
                imgui.text('Are you sure (this will also delete the .jar)')
                imgui.separator()
                if imgui.button('OK', width=imgui.get_content_region_available_width() / 2 - 20):
                    path = os.path.join(folder, cls.current_mod['file_name'])
                    if os.path.isfile(path): # just in case
                        os.remove(path)
                    data['mods'].remove(cls.current_mod)
                    cls.current_mod = None

                imgui.set_item_default_focus()
                imgui.same_line()

                if imgui.button('Cancel', width=imgui.get_content_region_available_width()):
                    imgui.close_current_popup()
                imgui.end_popup()
        else:
            cls.disable()
        imgui.end()

class SearchModW:
    download_state: DLState = DLState.IDLE
    
    query: Optional[str] = None
    results: Tuple[Addon] = tuple()

    @classmethod
    def init(cls):
        cls.query = ''

    @classmethod
    def disable(cls):
        cls.query = None
        cls.results = tuple()

    @classmethod
    @download_func()
    def search_mods(cls):
        cls.results = Addon.search_addon(cls.query)

    @classmethod
    def render(cls):
        if cls.query is None: return

        if imgui.begin('Search', closable=True)[1]:
            _, cls.query = imgui.input_text('##0n', cls.query, 256)
            imgui.same_line()

            disabled = cls.download_state == DLState.DOWNLOADING
            button_disable_color(disabled)
            if imgui.button('Search') and not disabled:
                threading.Thread(target=cls.search_mods).start()
            button_disable_color(disabled)
            
            if imgui.begin_child('search_results', border=True) and cls.results:
                for i, result in enumerate(cls.results):
                    button = MultiButton(i)
                    with button:
                        imgui.begin_group()

                        imgui.text(result.name)
                        imgui.text_colored(textwrap.shorten(result.summary, width=70), 0.82, 0.82, 0.82)

                        imgui.end_group()
                    if button:
                        imgui.set_next_window_focus()
                        AddModW.init(result)
            imgui.end_child()
        else:
            cls.disable()
        imgui.end()

class AddModW:
    download_state: DLState = DLState.IDLE

    mod: Optional[Addon] = None
    versions: Tuple[AddonFile] = tuple()
    selected: int = 0

    @classmethod
    def init(cls, mod: Addon):
        cls.mod = mod
    
    @classmethod
    def disable(cls):
        cls.mod = None
        cls.versions = tuple()
        cls.selected = 0

    @classmethod
    @download_func()
    def get_versions(cls):
        cls.versions = get_versions(cls.mod)

    @classmethod
    @download_func(use_done=True)
    def download_version(cls):
        af: AddonFile = cls.versions[cls.selected]
        af.download(folder)
        
        data['mods'].append({
            'name': cls.mod.name,
            'id': cls.mod.id,
            'url': cls.mod.url,
            'version_name': af.name,
            'file_name': af.file_name,
            'file_id': af.id,
            'icon': cls.mod.icon,
            'summary': cls.mod.summary
        })
        save_data()

    @classmethod
    def render(cls):
        if cls.mod is None: return

        if imgui.begin('Add mod', closable=True)[1]:
            imgui.text_colored(cls.mod.name, 1, 1, 1)
            imgui.push_text_wrap_pos(imgui.get_window_width())
            imgui.text_colored(cls.mod.summary, 0.82, 0.82, 0.82)
            imgui.pop_text_wrap_pos()
            imgui.separator()

            _, cls.selected = imgui.combo('Select version', cls.selected, [af.name for af in cls.versions])
            disabled = cls.download_state == DLState.DOWNLOADING
            button_disable_color(disabled)
            if imgui.button('Get versions') and not disabled:
                threading.Thread(target=cls.get_versions).start()
            button_disable_color(disabled)

            imgui.set_cursor_pos((0, imgui.get_window_height() - 32))
            imgui.separator()

            if imgui.button('Add'):
                imgui.open_popup('Downloading mod')
                threading.Thread(target=cls.download_version).start()
                
            if cls.versions and imgui.begin_popup_modal('Downloading mod', flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)[0]:
                if cls.download_state == DLState.DONE:
                    imgui.close_current_popup()
                    cls.download_state = DLState.IDLE
                imgui.text('Downloading... (progress bar soon)')
                imgui.end_popup()

            imgui.same_line()  
            if imgui.button('Cancel'):
                cls.disable()
        else:
            cls.disable()
        imgui.end()


while helper.loop():
    with helper:
        if imgui.begin_main_menu_bar():
            if imgui.menu_item('New')[0]:
                data_path = easygui.filesavebox(msg='Create obsidian.json', default='obsidian.json', filetypes=['*.json'])
                if data_path:
                    data = {'mods':[]}
                    with open(data_path, 'w') as file:
                        json.dump(data, file)
                    folder = os.path.dirname(data_path)
            if imgui.menu_item('Open')[0]:
                data_path = easygui.fileopenbox(msg='Open obsidian.json', default='*.json', filetypes=['*.json'])
                if data_path:
                    with open(data_path, 'r') as file:
                        data = json.load(file)
                    folder = os.path.dirname(data_path)
            imgui.end_main_menu_bar()

        if data is not None:
            MainW.render()
            EditModW.render()
            SearchModW.render()
            AddModW.render()

helper.stop()
