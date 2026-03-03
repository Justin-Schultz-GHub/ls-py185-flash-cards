import os
import re
import secrets
import random
from flask import (
                    flash,
                    Flask,
                    render_template,
                    redirect,
                    request,
                    send_from_directory,
                    session,
                    url_for,
                    g,
                    )

from flashcards.utils import (
                            deck_exists,
                            get_yaml_path,
                            get_deck_path,
                            get_data_dir,
                            generate_next_folder_name,
                            generate_card_id,
                            )

import string
import shutil
import yaml

from flashcards.database_persistence import (
                                            DatabasePersistence,
                                            )

from flashcards.session_persistence import (
                                            SessionPersistence,
                                            )

app = Flask(__name__)
app.secret_key=secrets.token_hex(32)

@app.before_request
def initialize_persistence():
    g.storage = DatabasePersistence()
    g.study = SessionPersistence(session)

# Route hooks
@app.route('/')
def index():
    decks = g.storage.get_all_decks()

    return render_template('flashcards.html', decks=decks)

@app.route('/deck/<int:deck_id>')
def display_deck(deck_id):
    deck = g.storage.get_deck(deck_id)
    deck_name = deck[0]['name']
    cards = g.storage.get_cards(deck_id)

    return render_template('deck.html', cards=cards, deck_name=deck_name, deck_id=deck_id)

@app.route('/new')
def new_deck():
    return render_template('new_deck.html')

@app.route('/new/create', methods=['POST'])
def create_deck():
    deckname = request.form['deckname']

    if not deckname:
        flash('Deck name cannot be empty.', 'error')
        return redirect(url_for('new_deck'))

    g.storage.create_deck(deckname)

    flash(f'Successfully created {deckname}.', 'success')
    return redirect(url_for('index'))

@app.route('/decks/<int:deck_id>/rename')
def rename_deck(deck_folder):
    yaml_path = get_yaml_path(deck_folder)

    with open(yaml_path, 'r', encoding='utf-8') as file:
        deck_data = yaml.safe_load(file)

    return render_template('rename_deck.html', deck=deck_data, deck_folder=deck_folder)

@app.route('/decks/<int:deck_id>', methods=['POST'])
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

@app.route('/decks/<int:deck_id>/delete', methods=['POST'])
def delete_deck(deck_folder):
    folders = os.listdir(get_data_dir())

    if deck_folder in folders:
        deck_path = get_deck_path(deck_folder)
        shutil.rmtree(deck_path, ignore_errors=True)

        flash('Deck successfully deleted.', 'success')
        return redirect(url_for('index'))

    flash('Failed to delete deck.', 'error')
    return redirect(url_for('index'))

@app.route('/decks/<int:deck_id>/new_card')
def new_card(deck_id):
    return render_template('create_flashcard.html', deck_id=deck_id)

@app.route('/decks/<int:deck_id>/new_card/create', methods=['POST'])
def create_card(deck_id):
    card_front = request.form['front'].strip()
    card_back = request.form['back'].strip()

    if not card_front or not card_back:
        flash('Flashcards must have a front and back.', 'error')
        return redirect(url_for('new_card', deck_id=deck_id))

    g.storage.create_card(card_front, card_back, deck_id)

    flash('Successfully created new card.', 'success')
    return redirect(url_for('display_deck', deck_id=deck_id))

@app.route('/decks/<int:deck_id>/<int:card_id>/delete', methods=['POST'])
def delete_card(deck_id, card_id):
    g.storage.delete_card(deck_id, card_id)

    flash('Successfully deleted card.', 'success')
    return redirect(url_for('display_deck', deck_id=deck_id))

@app.route('/decks/<int:deck_id>/study')
def study_cards(deck_id):
    study = g.study.start_study(g.storage.get_cards(deck_id), deck_id)

    if not study or not study['cards']:
        flash('This deck has no cards to study!', 'error')
        return redirect(url_for('display_deck', deck_id=deck_id))

    card = study['cards'][study['index']]
    side = study['side']

    return render_template(
                        'study.html',
                        card=card,
                        side=side,
                        deck_id=deck_id,
                        study_index = study['index'],
                        cards = study['cards']
                        )

@app.route('/decks/<int:deck_id>/study/flip')
def flip_card(deck_id):
    g.study.flip_card(deck_id)

    return redirect(url_for('study_cards', deck_id=deck_id))

@app.route('/decks/<int:deck_id>/study/next')
def next_card(deck_id):
    g.study.next_card(deck_id)

    return redirect(url_for('study_cards', deck_id=deck_id))

@app.route('/decks/<int:deck_id>/study/previous')
def previous_card(deck_id):
    g.study.previous_card(deck_id)

    return redirect(url_for('study_cards', deck_id=deck_id))

@app.route('/decks/<int:deck_id>/study/end')
def end_study(deck_id):
    g.study.end_study(deck_id)

    return redirect(url_for('display_deck', deck_id=deck_id))

if __name__ == "__main__":
    app.run(debug=True, port=8080)