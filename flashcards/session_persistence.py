import random

class SessionPersistence:
    def __init__(self, session):
        self.session = session

    def start_study(self, cards, deck_id):
        if 'study' not in self.session or self.session['study'].get('deck') != deck_id:
            random.shuffle(cards)
            self.session['study'] = {
                'deck': deck_id,
                'cards': cards,
                'index': 0,
                'side': 'front'
            }
        return self.session['study']

    def flip_card(self, deck_id):
        if 'study' in self.session and self.session['study'].get('deck') == deck_id:
            self.session['study']['side'] = 'back' if self.session['study']['side'] == 'front' else 'front'
            self.session.modified = True

    def next_card(self, deck_id):
        if 'study' in self.session and self.session['study'].get('deck') == deck_id:
            if self.session['study']['index'] < len(self.session['study']['cards']) - 1:
                self.session['study']['index'] += 1

            self.session['study']['side'] = 'front'
            self.session.modified = True

    def previous_card(self, deck_id):
        if 'study' in self.session and self.session['study'].get('deck') == deck_id:
            if self.session['study']['index'] > 0:
                self.session['study']['index'] -= 1

            self.session['study']['side'] = 'front'
            self.session.modified = True

    def end_study(self, deck_id):
        self.session.pop('study', None)