from dateutil.parser import parse as date_parse
from curseforge import *
import json
import os
import easygui
from glfw_helper import Helper, imgui
import threading
from enum import Enum
from typing import Optional, Tuple

helper = Helper('Cursed Obsidian', 800, 600, bg=(0.2, 0.2, 0.2))

data = None
folder = None

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

# Windows

class EditModW:
    current_mod: Optional[dict] = None
    versions: Optional[Tuple[AddonFile]] = tuple()
    selected: int = 0
    download_state: DLState = DLState.IDLE

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

            if imgui.button('OK') and len(cls.versions):
                imgui.open_popup('Update mod?')
            
            if len(cls.versions) and imgui.begin_popup_modal('Update mod?', flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)[0]:
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
                    t = threading.Thread(target=cls.download_version)
                    t.start()
                imgui.set_item_default_focus()
                imgui.same_line()
                if imgui.button('Cancel', width=imgui.get_content_region_available_width()) and not disable:
                    imgui.close_current_popup()
                button_disable_color(disable)
                imgui.end_popup()
            imgui.same_line()
            
            if imgui.button('Cancel'):
                cls.disable()
        else:
            cls.disable()
        imgui.end()

    @classmethod
    def init(cls, mod_index: int):
        cls.current_mod = data['mods'][mod_index]

    @classmethod
    def disable(cls):
        cls.current_mod = None
        cls.versions = tuple()
        cls.selected = 0

search_str = None
search_state = 0 # 0 - nothing, 1 - downloading
search_results = []
search_selected = None
search_versions = []
search_version_selected = 0
def search_for_mod():
    global search_state, search_results, search_selected
    search_state = 1
    search_results = []
    search_results = Addon.search_addon(search_str)
    search_selected = None
    search_state = 0

search_versions_state = 0
def search_get_versions():
    global search_versions, search_versions_state
    search_versions_state = 1

    addon = search_results[search_selected]
    search_versions = tuple(reversed(sorted(addon.get_files(), key=lambda af: date_parse(af.date))))
    
    search_versions_state = 0

def download_search_mod_version():
    global download_state
    download_state = 1
    mod = search_results[search_selected]
    
    af: AddonFile = search_versions[search_version_selected]
    af.download(folder)
    
    data['mods'].append({
        'name': mod.name,
        'id': mod.id,
        'url': mod.url,
        'version_name': af.name,
        'file_name': af.file_name,
        'file_id': af.id,
        'icon': mod.picture,
        'summary': mod.summary
    })
    save_data()
    download_state = 2


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
            if imgui.begin('Main', flags=imgui.WINDOW_MENU_BAR | imgui.WINDOW_NO_TITLE_BAR):
                if imgui.begin_menu_bar():
                    if imgui.begin_menu('Add mod'):
                        if imgui.menu_item('Search')[0]:
                            search_str = ''
                        imgui.end_menu()
                    imgui.end_menu_bar()
                for i, mod in enumerate(data['mods']):
                    # oh god this is a hardcoded numbers mess
                    imgui.set_cursor_pos((8, i * 40 + 27))

                    imgui.begin_group()
                    
                    imgui.text(mod['name'])
                    imgui.text_colored(mod['summary'], 0.82, 0.82, 0.82)
                    
                    imgui.end_group()

                    version_name = mod['version_name']
                    imgui.set_cursor_pos((imgui.get_window_width() - len(version_name) * 7 - 8, i * 40 + 27))
                    imgui.text_colored(version_name, 0.5, 0.5, 0.5)
                    
                    imgui.set_cursor_pos((8, i * 40 + 24))
                    if imgui.selectable(f'##0n{i}', width=imgui.get_window_width() - 10, height=35)[0]:
                        imgui.set_next_window_focus()
                        EditModW.init(i)
            imgui.end()
            # Edit mod window
            EditModW.render()
        # Search mod window
        if search_str is not None:
            _, opened = imgui.begin('Search', closable=True)
            if opened:
                _, search_str = imgui.input_text('##0n', search_str, 256)
                imgui.same_line()
                disable = search_state == 1
                button_disable_color(disable)
                if imgui.button('Search') and not disable:
                    t = threading.Thread(target=search_for_mod)
                    t.start()
                button_disable_color(disable)
                if imgui.begin_child('search_results', border=True) and len(search_results):
                    for i, result in enumerate(search_results):
                        if imgui.selectable(f'{result.name}\n{result.summary}')[0]:
                            imgui.set_next_window_focus()
                            search_selected = i
                            search_versions = []
                            search_version_selected = 0
                imgui.end_child()
            else:
                search_str = None
                search_results = []
                search_selected = None
            imgui.end()
        # search mod specific window
        if search_selected is not None:
            _, opened = imgui.begin('Add mod', closable=True)
            if opened:
                mod = search_results[search_selected]
                imgui.text_colored(mod.name, 1, 1, 1)
                imgui.push_text_wrap_pos(imgui.get_window_width())
                imgui.text_colored(mod.summary, 0.82, 0.82, 0.82)
                imgui.pop_text_wrap_pos()
                imgui.separator()

                _, search_version_selected = imgui.combo('Select version', search_version_selected, [af.name for af in search_versions])
                disable = search_versions_state == 1
                button_disable_color(disable)
                if imgui.button('Get versions') and not disable:
                    t = threading.Thread(target=search_get_versions)
                    t.start()
                button_disable_color(disable)

                imgui.set_cursor_pos((0, imgui.get_window_height() - 32))
                imgui.separator()

                if imgui.button('Add'):
                    imgui.open_popup('Downloading mod')
                    t = threading.Thread(target=download_search_mod_version)
                    t.start()
                    
                if len(search_versions) and imgui.begin_popup_modal('Downloading mod', flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)[0]:
                    if download_state == 2:
                        imgui.close_current_popup()
                        download_state = 0
                    imgui.text('Downloading... (progress bar soon)')
                    imgui.end_popup()

                imgui.same_line()  
                if imgui.button('Cancel'):
                    search_selected = None
            else:
                search_selected = None
            imgui.end()

helper.stop()
