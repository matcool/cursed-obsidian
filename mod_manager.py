#import bimpy
from dateutil.parser import parse as date_parse
from curseforge import *
import json
import os

if os.path.isfile('obsidian.json'):
    with open('obsidian.json', 'r') as file:
        data = json.load(file)
else:
    data = {'mods': []}

if False:
    query = input('Search for mod: ')

    results = Addon.search_addon(query)
    for i, addon in enumerate(results):
        print(f'{i} - {addon.name}\n'
            f'      {addon.summary}')
    choice = input('choose ')

    addon = results[int(choice)]

    # addon = Addon.from_id(315486)

    files = addon.get_files()
    files = sorted(files, key=lambda af: date_parse(af.date))
    files = tuple(reversed(files))
    for i, file in enumerate(files):
        print(f'{i} - {file.name}')

    choice = input('choose ')

    mod_file: AddonFile = files[int(choice)]
    mod_file.download('.')

    data['mods'].append({
        'name': addon.name,
        'id': addon.id,
        'url': addon.url,
        'filename': mod_file.filename,
        'file_id': mod_file.id
    })
else:
    for i, mod in enumerate(data['mods']):
        print(f'{i} - {mod["name"]} ({mod["filename"]})')
    choice = int(input('choose '))

    mod_data = data['mods'][choice]

    addon = Addon.from_id(mod_data['id'])

    files = addon.get_files()
    files = sorted(files, key=lambda af: date_parse(af.date))
    files = tuple(reversed(files))
    for i, file in enumerate(files):
        print(f'{i} - {file.name}')

    choice = input('choose ')

    mod_file: AddonFile = files[int(choice)]
    mod_file.download('.')

    os.remove(mod_data['filename'])

    mod_data['filename'] = mod_file.filename
    mod_data['file_id'] = mod_file.id

with open('obsidian.json', 'w') as file:
    json.dump(data, file)

# ctx = bimpy.Context()

# ctx.init(600, 600, 'Mod manager')

# search_window = False
# search_text = bimpy.String()

# while not ctx.should_close():
#     with ctx:
#         if bimpy.begin('Main'):
#             bimpy.text('Sup im the main window')
#             if bimpy.button('Search'):
#                 search_window = True
#         bimpy.end()
#         if search_window:
#             if bimpy.begin('Search for a mod'):
#                 bimpy.input_text('', search_text, 256)
#                 if bimpy.button('Search'):
#                     print(f'searching for: {search_text.value}')
#             bimpy.end()
