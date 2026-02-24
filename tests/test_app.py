import unittest
import os
import shutil
import yaml
from app import app, get_data_dir, get_deck_path, get_yaml_path, generate_next_folder_name, deck_exists

class AppTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.data_path = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(self.data_path, exist_ok=True)

        for i in range(1, 4):
            self.create_deck(f'Test Deck {i}', self.data_path)

    def create_deck(self, deckname, data_path):
        deck_folder = generate_next_folder_name()
        os.makedirs(get_deck_path(deck_folder), exist_ok=True)
        yaml_path = get_yaml_path(deck_folder)

        deck_data = {
            'name': deckname,
            'cards': [
                        {'front': 'Card 1 Front', 'back': 'Card 1 Back', 'id': '1'},
                        {'front': 'Card 2 Front', 'back': 'Card 2 Back', 'id': '2'},
                        {'front': 'Card 3 Front', 'back': 'Card 3 Back', 'id': '3'},
                    ]
        }

        with open(yaml_path, 'w', encoding='utf-8') as file:
            yaml.dump(deck_data, file, allow_unicode=True, default_flow_style=False, sort_keys=False)

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
        self.assertFalse(deck_exists(f'{self.data_path}/deck4'))

    def test_display_rename_deck_page(self):
        response = self.client.get('/decks/deck1/rename')
        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)
        self.assertIn('Renaming Test Deck 1', data)
        self.assertIn('Enter new deck name:', data)

    def test_rename_deck(self):
        deckname = 'Test Deck 45'
        response = self.client.post('/decks/deck1',
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
        deck_folder = 'deck3'
        yaml_path = get_yaml_path(deck_folder)

        with open(yaml_path, 'r', encoding='utf-8') as file:
            original_deck_data = yaml.safe_load(file)

        response = self.client.post(f'/decks/{deck_folder}',
                                    data={
                                        'deckname': deckname,
                                    },
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)
        self.assertIn(f"Renaming {original_deck_data['name']}:", data)
        self.assertIn('Deck name cannot be empty.', data)

        with open(yaml_path, 'r', encoding='utf-8') as file:
            new_deck_data = yaml.safe_load(file)

        self.assertEqual(original_deck_data, new_deck_data)

    def test_delete_deck(self):
        deck = 'deck3'
        response = self.client.post(f'/decks/{deck}/delete',
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)
        self.assertIn('Deck successfully deleted.', data)
        self.assertNotIn('Test Deck 3', data)

    def test_delete_non_existent_deck(self):
        deck_folder = 'deck4'
        response = self.client.post(f'/decks/{deck_folder}/delete',
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)
        self.assertIn('Failed to delete deck.', data)
        self.assertIn('Test Deck 1', data)
        self.assertIn('Test Deck 2', data)
        self.assertIn('Test Deck 3', data)

    def test_delete_deck_get_request(self):
        deck_folder = 'deck3'
        response = self.client.get(f'/decks/{deck_folder}/delete',
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 405)
        folders = os.listdir(get_data_dir())
        self.assertIn(deck_folder, folders)

    def test_display_new_card_page(self):
        deck_folder = 'deck3'
        response = self.client.get(f'/decks/{deck_folder}/new_card')
        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)
        self.assertIn('Create a New Flashcard', data)

    def test_create_card(self):
        deck_folder = 'deck3'
        response = self.client.post(f'/decks/{deck_folder}/new_card/create',
                                    data={
                                        'front': 'Test1',
                                        'back': 'Test2'
                                    },
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        data = response.get_data(as_text=True)
        self.assertIn('Successfully created new card.', data)
        self.assertIn('Test1', data)
        self.assertIn('Test2', data)

        yaml_path = get_yaml_path(deck_folder)

        with open(yaml_path, 'r', encoding='utf-8') as file:
            deck_data = yaml.safe_load(file)

        self.assertIn('id', deck_data['cards'][-1])

    def test_create_card_empty_inputs(self):
        deck_folder = 'deck3'
        yaml_path = get_yaml_path(deck_folder)

        with open(yaml_path, 'r', encoding='utf-8') as file:
            original_deck_data = yaml.safe_load(file)

        data_sets = [
                        {'front': 'Test1', 'back': ''},
                        {'front': '', 'back': 'Test2'},
                        {'front': '', 'back': ''}
                    ]

        for data_set in data_sets:
            response = self.client.post(f'/decks/{deck_folder}/new_card/create',
                                        data=data_set,
                                        follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            data = response.get_data(as_text=True)
            self.assertIn('Create a New Flashcard:', data)
            self.assertIn('Flashcards must have a front and back.', data)

        with open(yaml_path, 'r', encoding='utf-8') as file:
            new_deck_data = yaml.safe_load(file)

        self.assertEqual(original_deck_data, new_deck_data)

    def test_delete_card(self):
        deck_folder = 'deck2'
        card_id = '2'
        self.client.post(f'/decks/{deck_folder}/{card_id}/delete')
        yaml_path = get_yaml_path(deck_folder)

        with open(yaml_path, 'r', encoding='utf-8') as file:
            deck_data = yaml.safe_load(file)

        for card in deck_data['cards']:
            self.assertNotEqual(card_id, card['id'])

    def tearDown(self):
        shutil.rmtree(self.data_path, ignore_errors=True)