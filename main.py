from dateutil.parser import parse as date_parse
from curseforge import *
import json
import os
import easygui
from glfw_helper import Helper, imgui
import threading

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

selected_mod = None
selected_mod_files = []
selected_mod_file = 0

def edit_mod_get_versions():
    global selected_mod_files, selected_mod_file
    
    project_id = data['mods'][selected_mod]['id']
    file_id = data['mods'][selected_mod]['file_id']
    addon = Addon.from_id(project_id)
    
    selected_mod_files = tuple(reversed(sorted(addon.get_files(), key=lambda af: date_parse(af.date))))
    selected_mod_file = None
    for i, af in enumerate(selected_mod_files):
        if af.id == file_id:
            selected_mod_file = i
            break

download_state = 0 # 0 - nothing, 1 - downloading, 2 - done
def download_selected_mod_version():
    global download_state
    download_state = 1
    current_mod = data['mods'][selected_mod]
    
    af: AddonFile = selected_mod_files[selected_mod_file]
    af.download(folder)
    
    old_path = os.path.join(folder, current_mod['file_name'])
    if os.path.isfile(old_path): # just in case
        os.remove(old_path)
    
    current_mod.update({
        'version_name': af.name,
        'file_id': af.id,
        'file_name': af.file_name
    })
    save_data()
    download_state = 2

search_str = None
search_state = 0 # same as download_state
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
                    # would be nice to do this some other way (to include an image in the future)
                    # instead of putting it in a selectable
                    if imgui.selectable(f'{mod["name"]}\n{mod["summary"]}')[0]:
                        imgui.set_next_window_focus()
                        selected_mod = i
                        selected_mod_files = []
                        selected_mod_file = 0
            # Edit mod window
            if selected_mod is not None:
                current = data['mods'][selected_mod]
                _, opened = imgui.begin('Edit mod', closable=True)
                if opened:
                    imgui.text_colored(current['name'], 1, 1, 0)
                    _, selected_mod_file = imgui.combo('Select version', selected_mod_file, [af.name for af in selected_mod_files])
                    if imgui.button('Get versions'):
                        t = threading.Thread(target=edit_mod_get_versions)
                        t.start()


                    imgui.set_cursor_pos((0, imgui.get_window_height() - 32))
                    imgui.separator()

                    if imgui.button('OK') and len(selected_mod_files):
                        imgui.open_popup('Update mod?')
                    
                    if len(selected_mod_files) and imgui.begin_popup_modal('Update mod?', flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)[0]:
                        if download_state == 2:
                            imgui.close_current_popup()
                            download_state = 0
                        imgui.text(f'This will delete your current jar file ({current["file_name"]}) ')
                        imgui.text(f'and replace it with the version you just selected ({selected_mod_files[selected_mod_file].name})')
                        imgui.separator()
                        disable = download_state != 0
                        button_disable_color(disable)
                        if imgui.button('OK', width=imgui.get_content_region_available_width() / 2 - imgui.STYLE_FRAME_PADDING) and not disable:
                            t = threading.Thread(target=download_selected_mod_version)
                            t.start()
                        imgui.set_item_default_focus()
                        imgui.same_line()
                        if imgui.button('Cancel', width=imgui.get_content_region_available_width()) and not disable:
                            imgui.close_current_popup()
                        button_disable_color(disable)
                        imgui.end_popup()
                    imgui.same_line()
                    
                    if imgui.button('Cancel'):
                        selected_mod = None
                        selected_mod_files = []
                        selected_mod_file = 0
                else:
                    selected_mod = None
                    selected_mod_files = []
                    selected_mod_file = 0
                imgui.end()
            imgui.end()
        # Search mod window
        if search_str is not None:
            _, opened = imgui.begin('Search', closable=True)
            if opened:
                _, search_str = imgui.input_text('', search_str, 256)
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
