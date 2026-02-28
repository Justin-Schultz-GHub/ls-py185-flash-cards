import os
import random
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import DictCursor
import logging

LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

class DatabasePersistence:
    def __init__(self):
        pass

    @contextmanager
    def _database_connect(self):
        if os.environ.get('FLASK_ENV') == 'production':
            connection = psycopg2.connect(os.environ['DATABASE_URL'])
        else:
            connection = psycopg2.connect(dbname='flashcards')

        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def create_deck(self, name):
        query = '''
                INSERT INTO decks (name)
                values (%s)
                RETURNING id;
                '''
        with self._database_connect() as connection:
            with connection.cursor() as cursor:
                logger.info(
                        'Executing query: %s with name: %s',
                        query, name
                        )
                cursor.execute(query, (name,))
                deck_id = cursor.fetchone()[0]

        print(deck_id)
        return deck_id

    def get_all_decks(self):
        query = '''
                SELECT id, name FROM decks;
                '''
        logger.info('Executing query: %s', query)

        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query)
                results = cursor.fetchall()

        decks = [dict(result) for result in results]

        return(decks)

    def get_deck(self, deck_id):
        query = '''
                SELECT id, name FROM decks
                WHERE id = (%s);
                '''
        logger.info('Executing query: %s', query)

        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (deck_id,))
                results = cursor.fetchall()

        deck = [dict(result) for result in results]

        return(deck)

    def get_cards(self, deck_id):
        query = '''
                SELECT id, front, back FROM cards
                WHERE deck_id = (%s);
                '''
        logger.info('Executing query: %s', query)

        with self._database_connect() as connection:
            with connection.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(query, (deck_id,))
                results = cursor.fetchall()

        cards = [dict(result) for result in results]

        return(cards)

    def start_study(self, deck_folder, cards):
        pass

    def flip_card(self, deck_folder):
        pass

    def next_card(self, deck_folder):
        pass

    def previous_card(self, deck_folder):
        pass

    def end_study(self, deck_folder):
        pass