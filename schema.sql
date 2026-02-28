CREATE TABLE decks (
id serial PRIMARY KEY,
name TEXT NOT NULL
);

CREATE TABLE cards (
id serial PRIMARY KEY,
front TEXT NOT NULL,
back TEXT NOT NULL,
deck_id INTEGER NOT NULL REFERENCES decks(id) ON DELETE CASCADE
);

CREATE INDEX idx_cards_deck_id
ON cards(deck_id);