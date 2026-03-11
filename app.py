import secrets
import os
from flask import (
                    flash,
                    Flask,
                    render_template,
                    redirect,
                    request,
                    session,
                    url_for,
                    g,
                    )

from flashcards.database_persistence import (
                                            DatabasePersistence,
                                            )

from flashcards.session_persistence import (
                                            SessionPersistence,
                                            )

app = Flask(__name__)
app.config['DATABASE'] = 'flashcards'
app.secret_key=secrets.token_hex(32)

@app.before_request
def initialize_persistence():
    dbname = app.config.get('DATABASE', os.environ.get('DATABASE', 'flashcards'))
    g.storage = DatabasePersistence(dbname=dbname)
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
def rename_deck(deck_id):
    deck_name = g.storage.get_deck(deck_id)[0]['name']

    return render_template('rename_deck.html', deck_name=deck_name, deck_id=deck_id)

@app.route('/decks/<int:deck_id>/rename', methods=['POST'])
def save_deck(deck_id):
    new_deck_name = request.form['deckname']

    if not new_deck_name:
        flash('Deck name cannot be empty.', 'error')
        return redirect(url_for('rename_deck', deck_id=deck_id))

    if not g.storage.rename_deck(deck_id, new_deck_name):
        flash('Deck not found.', 'error')
        return redirect(url_for('rename_deck', deck_id=deck_id))

    flash(f'Deck successfully renamed.', 'success')
    return redirect(url_for('index'))

@app.route('/decks/<int:deck_id>/delete', methods=['POST'])
def delete_deck(deck_id):
    if g.storage.delete_deck(deck_id):
        flash('Deck successfully deleted.', 'success')
        return redirect(url_for('index'))

    flash('Deck not found.', 'error')
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
    if os.environ.get('FLASK_ENV') == 'production':
        app.run(debug=False)
    else:
        app.run(debug=True, port=8080)