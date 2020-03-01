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

current_edit_mod = None
current_edit_versions = []
current_edit_version_selected = 0

def edit_mod_get_versions():
    global current_edit_versions
    global current_edit_version_selected
    
    project_id = data['mods'][current_edit_mod]['id']
    version_name = data['mods'][current_edit_mod]['version_name']
    addon = Addon.from_id(project_id)
    
    current_edit_versions = tuple(reversed(sorted(addon.get_files(), key=lambda af: date_parse(af.date))))
    current_edit_version_selected = None
    for i, af in enumerate(current_edit_versions):
        if af.name == version_name:
            current_edit_version_selected = i
            break

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
                        current_edit_mod = i
                        current_edit_versions = []
                        current_edit_version_selected = 0
            if current_edit_mod is not None:
                current = data['mods'][current_edit_mod]
                _, opened = imgui.begin('Edit mod', closable=True)
                if opened:
                    imgui.text_colored(current['name'], 1, 1, 0)
                    _, current_edit_version_selected = imgui.combo('Select version', current_edit_version_selected, [af.name for af in current_edit_versions])
                    if imgui.button('Get versions'):
                        t = threading.Thread(target=edit_mod_get_versions)
                        t.start()
                    imgui.separator()

                    if imgui.button('OK') and len(current_edit_versions):
                        imgui.open_popup('Update mod?')
                    
                    if len(current_edit_versions) and imgui.begin_popup_modal('Update mod?', flags=imgui.WINDOW_ALWAYS_AUTO_RESIZE)[0]:
                        imgui.text(f'This will delete your current jar file ({current["file_name"]}) ')
                        imgui.text(f'with the version you just selected ({current_edit_versions[current_edit_version_selected].name})')
                        imgui.separator()
                        #imgui.set_cursor_pos((40, imgui.get_cursor_pos()[1]))
                        if imgui.button('OK'):
                            imgui.close_current_popup()
                        imgui.set_item_default_focus()
                        imgui.same_line()
                        if imgui.button('Cancel'):
                            imgui.close_current_popup()
                        imgui.end_popup()
                    imgui.same_line()
                    
                    if imgui.button('Cancel'):
                        current_edit_mod = None
                        current_edit_versions = []
                        current_edit_version_selected = 0
                else:
                    current_edit_mod = None
                    current_edit_versions = []
                    current_edit_version_selected = 0
                imgui.end()
            imgui.end()
helper.stop()
