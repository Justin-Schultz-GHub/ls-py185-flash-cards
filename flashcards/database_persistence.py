import os
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import DictCursor
import logging

LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

class DatabasePersistence:
    def __init__(self, dbname=None):
        self.dbname = dbname or os.environ.get('DATABASE') or 'flashcards'
        self._setup_schema()

    def _setup_schema(self):
        with self._database_connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute('''
                                CREATE TABLE IF NOT EXISTS decks (
                                id serial PRIMARY KEY,
                                name TEXT NOT NULL
                                );
                            ''')

                cursor.execute('''
                                CREATE TABLE IF NOT EXISTS cards (
                                id serial PRIMARY KEY,
                                front TEXT NOT NULL,
                                back TEXT NOT NULL,
                                deck_id INTEGER NOT NULL REFERENCES decks(id) ON DELETE CASCADE
                                );
                            ''')

                cursor.execute('''
                                CREATE INDEX IF NOT EXISTS idx_cards_deck_id
                                ON cards(deck_id);
                            ''')

    @contextmanager
    def _database_connect(self):
        if os.environ.get('FLASK_ENV') == 'production':
            connection = psycopg2.connect(os.environ['DATABASE_URL'])
        else:
            connection = psycopg2.connect(dbname=self.dbname)

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

        return deck_id

    def rename_deck(self, deck_id, new_deck_name):
        query = '''
                UPDATE decks
                SET name = (%s)
                WHERE id = (%s);
                '''

        with self._database_connect() as connection:
            with connection.cursor() as cursor:
                logger.info(
                        'Executing query: %s with deck_id: %s and deck_name: (%s)',
                        query, deck_id, new_deck_name
                        )
                cursor.execute(query, (new_deck_name, deck_id,))

                return cursor.rowcount

    def delete_deck(self, deck_id):
        query = '''
                DELETE FROM decks
                WHERE id = (%s);
                '''

        with self._database_connect() as connection:
            with connection.cursor() as cursor:
                logger.info(
                        'Executing query: %s with deck_id: %s',
                        query, deck_id
                        )
                cursor.execute(query, (deck_id,))

                return cursor.rowcount

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

    def create_card(self, front, back, deck_id):
        query = '''
                INSERT INTO cards (front, back, deck_id)
                values (%s, %s, %s)
                RETURNING id;
                '''

        with self._database_connect() as connection:
            with connection.cursor() as cursor:
                logger.info(
                        'Executing query: %s with deck_id: %s',
                        query, deck_id
                        )
                cursor.execute(query, (front, back, deck_id,))
                card_id = cursor.fetchone()[0]

        return card_id

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

    def delete_card(self, deck_id, card_id):
        query = '''
                DELETE FROM cards
                WHERE id = %s and deck_id = %s;
                '''

        with self._database_connect() as connection:
            with connection.cursor() as cursor:
                logger.info(
                        'Executing query: %s with deck_id: %s and card_id %s',
                        query, deck_id, card_id
                        )
                cursor.execute(query, (card_id, deck_id,))
