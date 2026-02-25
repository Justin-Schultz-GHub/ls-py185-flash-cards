import random

class SessionPersistence:
    def __init__(self, session):
        self.session = session

    def start_study(self, deck_folder, cards):
        if 'study' not in self.session or self.session['study'].get('deck') != deck_folder or not self.session['study'].get('cards'):
            self.session['study'] = {
                'deck': deck_folder,
                'cards': random.sample(cards, len(cards)),
                'index': 0,
                'side': 'front'
            }
        return self.session['study']

    def flip_card(self, deck_folder):
        if 'study' in self.session and self.session['study'].get('deck') == deck_folder:
            self.session['study']['side'] = 'back' if self.session['study']['side'] == 'front' else 'front'
            self.session.modified = True

    def next_card(self, deck_folder):
        if 'study' in self.session and self.session['study'].get('deck') == deck_folder:
            if self.session['study']['index'] < len(self.session['study']['cards']):
                self.session['study']['index'] += 1

            self.session['study']['side'] = 'front'
            self.session.modified = True

    def previous_card(self, deck_folder):
        if 'study' in self.session and self.session['study'].get('deck') == deck_folder:
            if self.session['study']['index'] > 0:
                self.session['study']['index'] -= 1

            self.session['study']['side'] = 'front'
            self.session.modified = True

    def end_study(self, deck_folder):
        self.session.pop('study', None)