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

selected_mod = None
selected_mod_files = []
selected_mod_file = 0

def edit_mod_get_versions():
    global selected_mod_files
    global selected_mod_file
    
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

while helper.loop():
    with helper:
        if imgui.begin_main_menu_bar():
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
                    if imgui.begin_menu('Actions'):
                        if imgui.menu_item('Search for mods')[0]:
                            'yea'
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
            if selected_mod is not None:
                current = data['mods'][selected_mod]
                _, opened = imgui.begin('Edit mod', closable=True)
                if opened:
                    imgui.text_colored(current['name'], 1, 1, 0)
                    _, selected_mod_file = imgui.combo('Select version', selected_mod_file, [af.name for af in selected_mod_files])
                    if imgui.button('Get versions'):
                        t = threading.Thread(target=edit_mod_get_versions)
                        t.start()


                    imgui.set_cursor_pos((0, imgui.get_window_height() - 30))
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
                        if disable:
                            imgui.push_style_color(imgui.COLOR_BUTTON, 0.3, 0.3, 0.3)
                            imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.3, 0.3, 0.3)
                        if imgui.button('OK', width=imgui.get_content_region_available_width() / 2 - imgui.STYLE_FRAME_PADDING) and not disable:
                            t = threading.Thread(target=download_selected_mod_version)
                            t.start()
                        imgui.set_item_default_focus()
                        imgui.same_line()
                        if imgui.button('Cancel', width=imgui.get_content_region_available_width()) and not disable:
                            imgui.close_current_popup()
                        if disable: imgui.pop_style_color(2)
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
helper.stop()
