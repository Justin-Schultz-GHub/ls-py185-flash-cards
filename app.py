import os
import re
from flask import (
                    flash,
                    Flask,
                    render_template,
                    redirect,
                    request,
                    send_from_directory,
                    session,
                    url_for,
                    )
import string
import shutil
import yaml
import random

app = Flask(__name__)
app.secret_key='secret1'

# Helper functions
def get_data_dir():
    subdir = 'tests/data' if app.config['TESTING'] else 'flashcards/data'
    return os.path.join(os.path.dirname(__file__), subdir)

def deck_exists(path):
    return os.path.exists(path)

def get_deck_path(deck_folder):
    return os.path.join(get_data_dir(), deck_folder)

def get_yaml_path(deck_folder):
    deck_path = get_deck_path(deck_folder)

    return os.path.join(deck_path, 'cards.yml')

def generate_next_folder_name():
    existing = os.listdir(get_data_dir())
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

# Route hooks
@app.route('/')
def index():
    data_dir = get_data_dir()
    folders = os.listdir(data_dir)
    decks = []

    for folder in folders:
        yaml_path = os.path.join(data_dir, folder, 'cards.yml')
        with open(yaml_path, 'r', encoding='utf-8') as file:
            deck_data = yaml.safe_load(file)

        deck_name = deck_data.get('name', folder)
        decks.append({'folder': folder, 'name': deck_name})

    return render_template('flashcards.html', decks=decks)

@app.route('/deck/<deck_folder>')
def display_deck(deck_folder):
    yaml_path = get_yaml_path(deck_folder)

    with open(yaml_path, 'r', encoding='utf-8') as f:
        deck_data = yaml.safe_load(f)

    cards = deck_data.get('cards', [])
    deck_title = deck_data.get('name', deck_folder)

    return render_template('deck.html', cards=cards, deck_title=deck_title, deck_folder=deck_folder)

@app.route('/new')
def new_deck():
    return render_template('new_deck.html')

@app.route('/new/create', methods=['POST'])
def create_deck():
    deckname = request.form['deckname']

    if not deckname:
        flash('Deck name cannot be empty.', 'error')
        return redirect(url_for('new_deck'))

    deck_folder = generate_next_folder_name()
    deck_path = get_deck_path(deck_folder)
    yaml_path = get_yaml_path(deck_folder)
    os.makedirs(deck_path, exist_ok=False)

    deck_data = {
            'name': deckname,
            'cards': []
        }

    with open(yaml_path, 'w', encoding='utf-8') as file:
        yaml.dump(deck_data, file, allow_unicode=True, default_flow_style=False, sort_keys=False)

    flash(f'Successfully created {deckname}.', 'success')
    return redirect(url_for('index'))

@app.route('/decks/<deck_folder>/rename')
def rename_deck(deck_folder):
    yaml_path = get_yaml_path(deck_folder)

    with open(yaml_path, 'r', encoding='utf-8') as file:
        deck_data = yaml.safe_load(file)

    return render_template('rename_deck.html', deck=deck_data, deck_folder=deck_folder)

@app.route('/decks/<deck_folder>', methods=['POST'])
def save_deck(deck_folder):
    yaml_path = get_yaml_path(deck_folder)

    with open(yaml_path, 'r', encoding='utf-8') as file:
        deck_data = yaml.safe_load(file)

    new_deck_name = request.form['deckname']

    if not new_deck_name:
        flash('Deck name cannot be empty.', 'error')
        return redirect(url_for('rename_deck', deck_folder=deck_folder))

    deck_data['name'] = new_deck_name

    with open(yaml_path, 'w', encoding='utf-8') as file:
        yaml.dump(deck_data, file, allow_unicode=True, default_flow_style=False, sort_keys=False)

    flash(f'Deck successfully renamed.', 'success')
    return redirect(url_for('index'))

@app.route('/decks/<deck_folder>/delete', methods=['POST'])
def delete_deck(deck_folder):
    folders = os.listdir(get_data_dir())

    if deck_folder in folders:
        deck_path = get_deck_path(deck_folder)
        shutil.rmtree(deck_path, ignore_errors=True)

        flash('Deck successfully deleted.', 'success')
        return redirect(url_for('index'))

    flash('Failed to delete deck.', 'error')
    return redirect(url_for('index'))

@app.route('/decks/<deck_folder>/new_card')
def new_card(deck_folder):
    return render_template('create_flashcard.html', deck_folder=deck_folder)

@app.route('/decks/<deck_folder>/new_card/create', methods=['POST'])
def create_card(deck_folder):
    yaml_path = get_yaml_path(deck_folder)

    with open(yaml_path, 'r', encoding='utf-8') as file:
        deck_data = yaml.safe_load(file)

    card_front = request.form['front'].strip()
    card_back = request.form['back'].strip()
    card_id = generate_card_id(deck_folder)

    if not card_front or not card_back:
        flash('Flashcards must have a front and back.', 'error')
        return redirect(url_for('new_card', deck_folder=deck_folder))

    deck_data['cards'].append({'front': card_front, 'back': card_back, 'id': card_id})
    with open(yaml_path, 'w', encoding='utf-8') as file:
        yaml.dump(deck_data, file, allow_unicode=True, default_flow_style=False, sort_keys=False)

    flash('Successfully created new card.', 'success')
    return redirect(url_for('display_deck', deck_folder=deck_folder))

@app.route('/decks/<deck_folder>/<card_id>/delete', methods=['POST'])
def delete_card(deck_folder, card_id):
    yaml_path = get_yaml_path(deck_folder)

    with open(yaml_path, 'r', encoding='utf-8') as file:
        deck_data = yaml.safe_load(file)

    for card in deck_data['cards']:
        if int(card_id) == int(card['id']):
            deck_data['cards'].remove(card)
            break

    with open(yaml_path, 'w', encoding='utf-8') as file:
        yaml.dump(deck_data, file, allow_unicode=True, default_flow_style=False, sort_keys=False)

    flash('Successfully deleted card.', 'success')
    return redirect(url_for('display_deck', deck_folder=deck_folder))

@app.route('/decks/<deck_folder>/study')
def study_cards(deck_folder):
    if 'study' not in session or session['study'].get('deck') != deck_folder or not session['study'].get('cards'):
        yaml_path = get_yaml_path(deck_folder)

        with open(yaml_path, 'r', encoding='utf-8') as file:
            deck_data = yaml.safe_load(file)

        if not deck_data.get('cards'):
            flash('This deck has no cards to study!', 'error')
            return redirect(url_for('display_deck', deck_folder=deck_folder))

        random.shuffle(deck_data['cards'])

        session['study'] = {
            'deck': deck_folder,
            'cards': deck_data['cards'],
            'index': 0,
            'side': 'front'
        }

    study = session['study']
    card = study['cards'][study['index']]
    side = study['side']

    return render_template(
                        'study.html',
                        card=card,
                        side=side,
                        deck_folder=deck_folder,
                        study_index = session['study']['index'],
                        cards = session['study']['cards']
                        )

@app.route('/decks/<deck_folder>/study/flip')
def flip_card(deck_folder):
    if 'study' in session and session['study'].get('deck') == deck_folder:
        session['study']['side'] = 'back' if session['study']['side'] == 'front' else 'front'
        session.modified = True

    return redirect(url_for('study_cards', deck_folder=deck_folder))

@app.route('/decks/<deck_folder>/study/previous')
def previous_card(deck_folder):
    if 'study' in session and session['study'].get('deck') == deck_folder:
        if session['study']['index'] > 0:
            session['study']['index'] -= 1

        session['study']['side'] = 'front'
        session.modified = True

    return redirect(url_for('study_cards', deck_folder=deck_folder))

@app.route('/decks/<deck_folder>/study/next')
def next_card(deck_folder):
    if 'study' in session and session['study'].get('deck') == deck_folder:
        if session['study']['index'] < len(session['study']['cards']):
            session['study']['index'] += 1

        session['study']['side'] = 'front'
        session.modified = True

    return redirect(url_for('study_cards', deck_folder=deck_folder))

@app.route('/decks/<deck_folder>/study/end')
def end_study(deck_folder):
    session.pop('study', None)

    return redirect(url_for('display_deck', deck_folder=deck_folder))

if __name__ == "__main__":
    app.run(debug=True, port=8080)