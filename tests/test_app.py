import unittest
from app import app
from flashcards.database_persistence import DatabasePersistence
from flashcards.session_persistence import SessionPersistence
import logging
from flask import g

LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

class AppTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['DATABASE'] = 'flashcards_test'
        self.client = app.test_client()
        self.db = DatabasePersistence(dbname=app.config['DATABASE'])

        self.deck_ids = [self.create_deck(f'Test Deck {i}') for i in range(1, 4)]

        self.card_ids = [self.db.create_card(f'Card Front {i}', f'Card Back {i}', self.deck_ids[1]) for i in range(1, 4)]

    def create_deck(self, deckname):
        return self.db.create_deck(deckname)

    def with_app_context(self, func, *args, **kwargs):
        with app.app_context():
            g.storage = self.db
            return func(*args, **kwargs)

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)
        self.assertIn('Test Deck 1', data)
        self.assertIn('Test Deck 2', data)
        self.assertIn('Test Deck 3', data)

    def test_display_new_deck_page(self):
        response = self.client.get('/new')
        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)
        self.assertIn('Create a New Deck', data)

    def test_create_deck(self):
        deckname = 'Test Deck 123'
        response = self.client.post('/new/create',
                                    data={
                                        'deckname': deckname,
                                    },
                                    follow_redirects=True
                                    )
        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)
        self.assertIn('Test Deck 123', data)
        self.assertIn('Test Deck 3', data)
        self.assertIn(f'Successfully created {deckname}', data)

    def test_create_nameless_deck(self):
        response = self.client.post('/new/create',
                                    data={
                                        'deckname': '',
                                    })
        self.assertEqual(response.status_code, 302)
        response = self.client.post('/new/create',
                                    data={
                                        'deckname': '',
                                    },
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)
        self.assertIn('Deck name cannot be empty.', data)
        deck = self.db.get_deck(4)
        self.assertEqual(deck, [])

    def test_display_rename_deck_page(self):
        with app.app_context():
            g.storage = self.db
            response = self.client.get(f'/decks/{self.deck_ids[0]}/rename')
            self.assertEqual(response.status_code, 200)
            data = response.get_data(as_text=True)
            self.assertIn(f'Renaming Test Deck 1', data)
            self.assertIn('Enter new deck name:', data)

    def test_rename_deck(self):
        deckname = 'Test Deck 45'
        deck_id = self.deck_ids[0]
        response = self.client.post(f'/decks/{deck_id}/rename',
                                    data={
                                        'deckname': deckname,
                                    },
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)
        self.assertIn('Deck successfully renamed.', data)
        self.assertIn('Test Deck 45', data)
        self.assertNotIn('Test Deck 1', data)

    def test_rename_deck_empty_name(self):
        deckname = ''
        deck_id = self.deck_ids[0]
        original_deck_data = self.db.get_deck(deck_id)[0]
        response = self.client.post(f'/decks/{deck_id}/rename',
                                    data={
                                        'deckname': deckname,
                                    },
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)
        self.assertIn(f"Renaming {original_deck_data['name']}:", data)
        self.assertIn('Deck name cannot be empty.', data)

        new_deck_data = self.db.get_deck(deck_id)[0]

        self.assertEqual(original_deck_data, new_deck_data)

    def test_delete_deck(self):
        deck_id = self.deck_ids[0]
        response = self.client.post(f'/decks/{deck_id}/delete',
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)
        self.assertIn('Deck successfully deleted.', data)
        self.assertNotIn('Test Deck 1', data)

    def test_delete_non_existent_deck(self):
        deck_id = 10
        response = self.client.post(f'/decks/{deck_id}/delete',
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)
        self.assertIn('Deck not found.', data)
        self.assertIn('Test Deck 1', data)
        self.assertIn('Test Deck 2', data)
        self.assertIn('Test Deck 3', data)

    def test_delete_deck_get_request(self):
        deck_id = self.deck_ids[0]
        response = self.client.get(f'/decks/{deck_id}/delete',
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 405)
        self.assertTrue(self.db.get_deck(deck_id))

    def test_display_new_card_page(self):
        deck_id = self.deck_ids[0]
        response = self.client.get(f'/decks/{deck_id}/new_card')
        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)
        self.assertIn('Create a New Flashcard', data)

    def test_create_card(self):
        deck_id = self.deck_ids[0]
        card_data = {
                'front': 'Test1',
                'back': 'Test2',
                }
        response = self.client.post(f'/decks/{deck_id}/new_card/create',
                                    data=card_data,
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)
        self.assertIn('Successfully created new card.', data)
        self.assertIn('Test1', data)
        self.assertIn('Test2', data)

        card = self.db.get_cards(deck_id)[0]

        self.assertEqual(card['front'], card_data['front'])
        self.assertEqual(card['back'], card_data['back'])

    def test_create_card_empty_inputs(self):
        deck_id = self.deck_ids[0]
        data_sets = [
                        {'front': 'Test1', 'back': ''},
                        {'front': '', 'back': 'Test2'},
                        {'front': '', 'back': ''}
                    ]
        original_deck_data = self.db.get_deck(deck_id)

        for data_set in data_sets:
            response = self.client.post(f'/decks/{deck_id}/new_card/create',
                                        data=data_set,
                                        follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            data = response.get_data(as_text=True)
            self.assertIn('Create a New Flashcard:', data)
            self.assertIn('Flashcards must have a front and back.', data)

        new_deck_data = self.db.get_deck(deck_id)

        self.assertEqual(original_deck_data, new_deck_data)

    def test_delete_card(self):
        deck_id = self.deck_ids[1]
        card_id = self.card_ids[1]
        old_cards = self.db.get_cards(deck_id)

        self.client.post(f'/decks/{deck_id}/{card_id}/delete')

        new_cards = self.db.get_cards(deck_id)

        self.assertNotEqual(old_cards, new_cards)

        for card in new_cards:
            self.assertNotEqual(card['id'], card_id)

    def tearDown(self):
        with self.db._database_connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute('DELETE FROM cards;')
                cursor.execute('DELETE FROM decks;')