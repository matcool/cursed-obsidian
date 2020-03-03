import requests
import json
from typing import Tuple, List
import os
import shutil

TWITCH_HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'twitch-desktop-electron-platform/1.0.0 Chrome/66.0.3359.181 Twitch/3.0.16 Safari/537.36 '
                  'desklight/8.42.2',
    'authority': 'addons-ecs.forgesvc.net',
    'origin': 'https://www.twitch.tv'
}

class Author:
    def __init__(self, data: dict):
        self.data = data
        self.name = data['name']
        self.id = data['id']

class Category:
    def __init__(self, data: dict):
        self.data = data
        self.name = data['name']
        self.id = data['categoryId']
        self.url = data['url']
        self.avatar = data['avatarUrl']

class AddonFile:
    def __init__(self, data: dict):
        self.data = data
        self.id = data['id']
        self.name = data['displayName']
        self.file_name = data['fileName']
        self.date = data['fileDate']
        self.size = data['fileLength']
        self.url = data['downloadUrl']
        self.game_version = data['gameVersion']

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'AddonFile({self.name!r})'

    def download(self, path: str='', add_file_name: bool=True) -> str:
        if add_file_name:
            path = os.path.join(path, self.file_name)
        with requests.get(self.url, headers=TWITCH_HEADERS, stream=True) as r:
            r.raise_for_status()
            with open(path, 'wb') as file:
                shutil.copyfileobj(r.raw, file)
        return path

class Addon:
    def __init__(self, data: dict):
        self.data = data
        self.name = data['name']
        self.id = data['id']
        self.authors = tuple(Author(i) for i in data['authors'])
        self.url = data['websiteUrl']
        self.summary = data['summary']
        self.downloads = int(data['downloadCount'])
        self.icon = None
        for att in data['attachments']:
            if att['isDefault']: self.icon = att['url'] 

    @classmethod
    def from_id(cls, id: int):
        """
        Returns an Addon with given addon id
        """
        r = requests.get(f'https://addons-ecs.forgesvc.net/api/v2/addon/{id}', headers=TWITCH_HEADERS)
        return cls(json.loads(r.text))

    def get_files(self) -> Tuple[AddonFile]:
        """
        Returns a tuple with all the files in the `adddon/{id}/files` api
        """
        r = requests.get(f'https://addons-ecs.forgesvc.net/api/v2/addon/{self.id}/files', headers=TWITCH_HEADERS)
        data = json.loads(r.text)
        return tuple(AddonFile(i) for i in data)
    
    @staticmethod
    def search_addon(name: str, entries: int=10) -> Tuple['Addon']:
        """
        Searchs for an addon and returns a tuple of the addons found
        """
        r = requests.get('https://addons-ecs.forgesvc.net/api/v2/addon/search', headers=TWITCH_HEADERS, params={
            'gameId': '432',
            'pageSize': entries,
            'searchFilter': name
        })
        data = json.loads(r.text)
        return tuple(Addon(i) for i in data)

    @staticmethod
    def get_addons(addons: List[int]):
        """
        Returns a tuple of addons with the ids given
        """
        r = requests.post('https://addons-ecs.forgesvc.net/api/v2/addon', headers=TWITCH_HEADERS, params={
            'addonIds': addons
        })
        data = json.loads(r.text)
        return tuple(Addon(i) for i in data)

    def __str__(self):
        return f'{self.name} by {self.authors[0].name}'

    def __repr__(self):
        return f'Addon({self.name!r})'
