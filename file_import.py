import json
import pygame


def save_data(data, path):
    json.dump(data, open(path, 'w', encoding='utf-8'))


def load_data(path) -> dict:
    data = json.load(open(path, 'r', encoding='utf-8'))
    if not isinstance(data, dict):
        raise json.decoder.JSONDecodeError
    return data


FILE_PATH_SETTINGS = "settings.json"

default_settings = {
    "keys": {
        "up": pygame.K_UP,
        "down": pygame.K_DOWN,
        "left": pygame.K_LEFT,
        "right": pygame.K_RIGHT,
        "jump": pygame.K_LSHIFT,
        "hook": pygame.K_z,
    }
}

# save_data(default_settings, FILE_PATH_SETTING)
error = False
try:
    settings = load_data(FILE_PATH_SETTINGS)
    st_keys = settings["keys"]

    KEY_UP = st_keys["up"]
    KEY_DOWN = st_keys["down"]
    KEY_LEFT = st_keys["left"]
    KEY_RIGHT = st_keys["right"]
    KEY_JUMP = st_keys["jump"]
    KEY_HOOK = st_keys["hook"]
except FileNotFoundError as e:
    error = True
except json.decoder.JSONDecodeError as e:
    error = True
except KeyError as e:
    error = True

if error:
    save_data(default_settings, FILE_PATH_SETTINGS)
    raise RuntimeError("Restart Game. Settings was damaged. They set to default")
