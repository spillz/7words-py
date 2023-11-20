from kivy.core.audio import SoundLoader

class SoundProxy:
    def __init__(self, sound_id, n):
        self.sounds = [SoundLoader.load('sounds/'+sound_id) for _ in range(n)]
        self.index = 0
    def play(self):
        try:
            self.sounds[self.index].play()
            self.index = (self.index + 1) % len(self.sounds)
        except:
            return

        
CANCEL_SELECTION = SoundProxy('cancel_selection.mp3', 1)
LEVEL_COMPLETED = SoundProxy('level_completed.mp3', 1)
LEVEL_FAILED = SoundProxy('level_failed.mp3', 1)
MENU = SoundProxy('menu.mp3', 5)
SELECT = SoundProxy('select.mp3', 5)
WORD_COMPLETED = SoundProxy('word_completed.mp3', 4)

if __name__ == '__main__':
    print('CANCEL_SELECTION')
    print('LEVEL_COMPLETED')
    print('LEVEL_FAILED')
    print('MENU')
    print('SELECT')
    print('WORD_COMPLETED')
