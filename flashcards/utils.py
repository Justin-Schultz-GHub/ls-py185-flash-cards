import os
import re
import yaml

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def deck_exists(path):
    return os.path.exists(path)

def get_data_dir(testing=False):
    subdir = 'tests/data' if testing else 'data'
    return os.path.join(BASE_DIR, subdir)

def get_yaml_path(deck_folder, testing=False):
    return os.path.join(get_deck_path(deck_folder, testing), 'cards.yml')

def get_deck_path(deck_folder, testing=False):
    return os.path.join(get_data_dir(testing), deck_folder)

def generate_next_folder_name(testing=False):
    existing = os.listdir(get_data_dir(testing=testing))
    pattern = re.compile(r'^deck(\d+)$')
    numbers = []

    for name in existing:
        match = pattern.match(name)
        if match:
            numbers.append(int(match.group(1)))

    next_number = max(numbers) + 1 if numbers else 1
    return f'deck{next_number}'

def generate_card_id(deck_folder):
    yaml_path = get_yaml_path(deck_folder)

    with open(yaml_path, 'r', encoding='utf-8') as f:
        deck_data = yaml.safe_load(f)

    existing_ids = set()

    for card in deck_data['cards']:
        existing_ids.add(int(card.get('id', 1)))

    return max(existing_ids) + 1 if existing_ids else 1