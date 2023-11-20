import random
import functools
import itertools
import math
import pickle
import os
import datetime
import sounds

import kivy
#kivy.require('1.8.0')

__version__ = '0.1.5'

def get_user_path():
    """ Return the folder to where user data can be stored """
    root = os.getenv('EXTERNAL_STORAGE') or os.path.expanduser("~")
    path = os.path.join(root, ".7words")
    if not os.path.exists(path):
        os.makedirs(path)
    return path

import colors

#from kivy.uix.listview import ListView, ListItemLabel, ListItemButton
#from kivy.adapters.listadapter import ListAdapter
from kivy.uix.floatlayout import FloatLayout
#from kivy.uix.relativelayout import RelativeLayout
#from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.boxlayout import BoxLayout
#from kivy.uix.screenmanager import ScreenManager
#from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
#from kivy.uix.button import Button
#from kivy.uix.label import Label
from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty, ReferenceListProperty, NumericProperty, \
    BooleanProperty, ListProperty, ObjectProperty, DictProperty
#from kivy.uix.image import Image
from kivy.graphics.texture import Texture
from kivy.graphics import Rectangle, Color
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
#from kivy.vector import Vector
from kivy.animation import Animation
from kivy.logger import Logger
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform

platform = None #platform()
if platform == 'android':
    try:
        # Support for Google Play
        import googleplaysettings
        import googleplayservices
        leaderboard_highscore = 'high_score'
        leaderboard_daily_challenge_highscore = 'daily_challenge_high_score'
        googleplayclient = googleplayservices.GoogleClient()
    #    from kivy.uix.popup import Popup
        from kivy.uix.popup import Popup
        class GooglePlayPopup(Popup):
            pass
    except:
        platform = None

board_size = 7

#Letter, Value, Number of Tiles
tiles = [
('B', 2, 2),
('C', 2, 2),
('D', 1, 4),
('F', 2, 2),
('G', 2, 3),
('H', 3, 2),
('J', 4, 1),
('K', 3, 2),
('L', 0, 3),
('M', 2, 3),
('N', 1, 3),
('P', 2, 3),
('Q', 4, 1),
('R', 1, 4),
('S', 1, 4),
('T', 1, 4),
('V', 4, 1),
('W', 3, 2),
('X', 4, 1),
('Y', 3, 2),
('Z', 4, 1),]

vowels = [
('A', 0, 4),
('E', 0, 5),
('I', 0, 4),
('O', 0, 4),
('U', 1, 3),
]

tile_set = []
for t in tiles:
    tile_set += [(t[0],t[1]+1)]*t[2]

vowel_set = []
for t in vowels:
    vowel_set += [(t[0],t[1]+1)]*t[2]

words = set(open("TWL06.txt","r").read().splitlines())

class Tile(Widget):
    letter = StringProperty('A')
    value = NumericProperty()
    selected = BooleanProperty(False)
    active = BooleanProperty(False)
    gpos_x = NumericProperty()
    gpos_y = NumericProperty()
    gpos = ReferenceListProperty(gpos_x, gpos_y)
    opos_x = NumericProperty()
    opos_y = NumericProperty()
    opos = ReferenceListProperty(opos_x, opos_y)
    cpos_x = NumericProperty()
    cpos_y = NumericProperty()
    cpos = ReferenceListProperty(cpos_x, cpos_y)
    w_label = ObjectProperty()
    row = NumericProperty()
    def __init__(self, board, x, y, letter, value, row, active = False):
        super(Tile,self).__init__()
        self.letter = letter
        self.value = value
        self.gpos_x = x
        self.gpos_y = y
        self.opos = self.gpos
        self.cpos = self.gpos
        self.board = board
        self.row = row
        self.bind(gpos = self.gpos_changed)
        self.active = active

    def gpos_changed(self, *args):
        if tuple(self.cpos) == (-1, -1):
            self.opos = self.gpos
            self.cpos = self.gpos
#        if not self.board.block_gpos_updates:
#            del self.board[self.cpos]
#            if tuple(self.gpos) != (-1, -1):
#                self.board[self.gpos] = self
#        self.cpos = self.gpos
        a = Animation(pos = self.gpos, duration = 0.25)
        a.start(self)

    def on_touch_down(self, touch):
        if self.board.block_gpos_updates:
            return False
        if not self.active:
            return False
        if self.collide_point(*touch.pos):
            if self.selected:
                self.board.deselect(self)
            else:
                self.board.select(self)
                sounds.SELECT.play()
            return True
        return False
            
class Star(Widget):
    pass

class Board(FloatLayout):
    def __init__(self,**kwargs):
        super(Board,self).__init__(**kwargs)
        self.scorebar = ScoreBar()
        self.statusbar = StatusBar()
        self.messagebar = MessageBar()
        self.scorebar.bind(game_id = self.messagebar.game_changed)
        self.statusbar.w_word_label.bind(on_touch_down = self.confirm_word)
        self.bind(size = self.size_changed)
        self.menu = Menu()
        self.menu.bind(selection = self.menu_choice)
        self.scorebar.bind(game_id = self.menu.ui_update)
        self.scorebar.bind(score = self.menu.ui_update)
#        self.menu.ui_update(self.scorebar)
        self.add_widget(self.scorebar)
        self.add_widget(self.statusbar)
        self.add_widget(self.messagebar)
        self.block_gpos_updates = False
        self.instructions = Instructions()
        self.active_row = 0
        self.scorebar.get_status()

        self.pyramid = []
        self.selection = []
        self.free = []
        self.game_over = False

        cons = random.sample(tile_set, sum(range(board_size)))
        vow = random.sample(vowel_set, 3 + board_size)
        target = sum(l[1] for l in cons+vow)
        self.scorebar.target = [3*target, 4*target, 5*target]
        for y in range(board_size):
            letters = cons[:board_size-y-1] + vow[:1]
            random.shuffle(letters)
            self.pyramid.append([Tile(self, -1, -1, l, v, y, y==0) for
                                (l,v) in letters])
            cons = cons[board_size-y-1:]
            vow = vow[1:]
            for w in self.pyramid[y]:
                self.add_widget(w)
        for x in range(3):
            l,v = vow.pop()
            t = Tile(self, -1, -1, l, v, -1, True)
            self.free.append(t)
            self.add_widget(t)

        self.opyramid = [p[:] for p in self.pyramid]
        self.ofree = self.free[:]

        self.first_start = True

    def show_menu(self):
        self.menu.selection = -1
        self.add_widget(self.menu)

    def hide_menu(self):
        self.remove_widget(self.menu)

    def menu_choice(self, menu, selection):
        if selection == 1:
            self.hide_menu()
            self.restart_game()
        if selection == 2:
            self.hide_menu()
            self.next_game()
        if selection == 3:
            self.hide_menu()
            self.prev_game()
        if selection == 4:
            self.hide_menu()
            self.add_widget(self.instructions)
        if selection == 5:
            self.hide_menu()
            if platform == 'android':
                score_type = leaderboard_highscore if self.scorebar.game_id>0 else leaderboard_daily_challenge_highscore
                App.get_running_app().gs_show_leaderboard(score_type)
        if selection == 6:
            self.hide_menu()
            if platform == 'android':
                App.get_running_app().gs_show_achievements()
        if selection == 7:
            App.get_running_app().set_next_theme()
            self.hide_menu()
            self.show_menu()
        if selection == 8:
            App.get_running_app().stop()

    def pos2gpos(self, pos):
        return int((pos[0] - self.off_x)//self.tile_space_size), int((pos[1] - self.off_y)//self.tile_space_size)

    def next_game(self):
        if self.scorebar.score>0:
            self.scorebar.played += 1
        self.scorebar.game_id += 1
        self.reset(True)

    def prev_game(self):
        if self.scorebar.game_id>1:
            if self.scorebar.score>0:
                self.scorebar.played += 1
            self.scorebar.game_id -= 1
        self.reset(True)

    def restart_game(self):
        if self.scorebar.score>0:
            self.scorebar.played += 1
        self.reset()

    def reset(self, redraw = False):
        Clock.schedule_once(lambda *args: self.reset_tick(-1), 0.01)
        self.scorebar.score = 0
        self.statusbar.word = ''
        self.statusbar.word_score = 0
        self.active_row = 0
        self.selection = []
        self.pyramid = [p[:] for p in self.opyramid]
        self.free = self.ofree[:]

        if redraw:
            cons = random.sample(tile_set, sum(range(board_size)))
            vow = random.sample(vowel_set, 3 + board_size)
            target = sum(l[1] for l in cons+vow)
            self.scorebar.target = [3*target, 4*target, 5*target]

        for t in self.free:
            if redraw:
                l,v = vow.pop()
                t.letter = l
                t.value = v
            t.cpos = t.gpos = (-1, -1)
        for row in self.pyramid:
            if redraw:
                letters = cons[:len(row)-1] + vow[:1]
                random.shuffle(letters)
            for t in row:
                if redraw:
                    l,v = letters.pop()
                    t.letter = l
                    t.value = v
                t.cpos = t.gpos = (-1, -1)
            if redraw:
                cons = cons[len(row)-1:]
                vow = vow[1:]
        self.game_over = False
        self.size_changed()

    def reset_tick(self, i):
        if i==-1:
            self.block_gpos_updates = True
            arr = self.free
        else:
            arr = self.pyramid[i]
        arr = self.free if i==-1 else self.pyramid[i]
        for t in arr:
            t.gpos = t.cpos
            t.opos = t.cpos
            t.selected = False
            t.active = t.row == self.active_row or i == -1
        i += 1
        if i < board_size:
            Clock.schedule_once(lambda *args: self.reset_tick(i), 0.1)
        else:
            self.block_gpos_updates = False

    def ppos2pos(self, ppos):
        if tuple(ppos) == (-1, -1):
            return self.size[0]/2, self.size[1]
        else:
            return self.center_x + self.tile_space_size*(ppos[0] - 0.5*(len(self.pyramid[ppos[1]]))), 0.1*self.size[1] + self.tile_space_size*(board_size - 1 - ppos[1])

    def spos2pos(self, spos):
        if spos == -1:
            return self.size[0]/2, self.size[1]
        else:
            return self.center_x + self.tile_space_size*(spos - 0.5*(len(self.selection))), 0.65*self.size[1]

    def fpos2pos(self, fpos):
        if fpos == -1:
            return self.size[0]/2, self.size[1]
        else:
            sz = board_size + 1
            if fpos//sz < len(self.free)//sz:
                row_len = sz
            else:
                row_len = len(self.free)%sz
            return  self.center_x + self.tile_space_size*(fpos%sz - 0.5*(row_len)), \
                    self.off_y + 0.82*self.size[1] - self.tile_space_size*(fpos//sz)

    def update_selection(self):
        for t, i in zip(self.selection,range(len(self.selection))):
            t.gpos = self.spos2pos(i)

    def update_free_tiles(self):
        for t, i in zip(self.free,range(len(self.free))):
            t.cpos = t.opos = t.gpos = self.fpos2pos(i)

    def update_pyramid_row_tiles(self, row = None):
        if row == None:
            row = self.active_row
        r = self.pyramid[self.active_row]
        for t, i in zip(r,range(len(r))):
            t.cpos = t.opos = t.gpos = self.ppos2pos((i,self.active_row))

    def _conv_pos(self, gpos):
        return int(gpos[0]), int(gpos[1])

    def size_changed(self,*args):
        self.tile_space_size = min(self.size[0], 0.5*self.size[1])//board_size
        self.tile_size = self.tile_space_size-4
        self.pyramid_size = board_size*self.tile_space_size
        self.off_x = 0# (self.size[0] - self.board_size)/2
        self.off_y = 0# 0.9*self.size[1] - self.board_size
        self.statusbar.size = (self.size[0]*3/4, 0.06*self.size[1])
        self.statusbar.pos = (self.size[0]/8, 0.04*self.size[1] + (self.off_y - 0.04*self.size[1] - 0.06*self.size[1])/2)
        self.messagebar.size = (self.size[0], 0.04*self.size[1])
        self.messagebar.pos = (0, 0)
        self.scorebar.size = (self.size[0],0.1*self.size[1])
        self.scorebar.pos = (0, 0.9*self.size[1])
        for row, y in zip(self.pyramid,range(len(self.pyramid))):
            for t, x in zip(row,range(len(row))):
                t.opos = t.gpos = self.ppos2pos((x, y))
                t.size = (self.tile_size, self.tile_size)
        for t, x in zip(self.free,range(len(self.free))):
            t.opos = t.gpos = self.fpos2pos(x)
            t.size = (self.tile_size, self.tile_size)
        for t, x in zip(self.selection,range(len(self.selection))):
            t.gpos = self.spos2pos(x)
            t.size = (self.tile_size, self.tile_size)
        self.menu.size = self.size
        self.menu.pos = self.pos
        self.instructions.size = self.size
        self.instructions.pos = self.pos
        self.draw_background()
        if self.first_start:
            self.first_start = False
#            if not self.load_state():
#                self.next_game()

    def draw_background(self, candidates = None):
        pass
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*colors.background)
            Rectangle(pos = self.pos, size = self.size)
#            Color(*colors.checker)
#            for x in range(board_size):
#                for y in range(board_size):
#                    if (x+y)%2 == 0:
#                        Rectangle(pos = (self.off_x + x*self.tile_space_size, self.off_y + y*self.tile_space_size), size = (self.tile_size, self.tile_size))
#            if candidates is not None:
#                Color(*colors.move_candidates)
#                for c in candidates:
#                    x, y = c
#                    Rectangle(pos = (self.off_x + x*self.tile_space_size + self.tile_space_size/4, self.off_y + y*self.tile_space_size + self.tile_space_size/4), size = (self.tile_size/2, self.tile_size/2))

    def update_word_bar(self):
        self.statusbar.word, self.statusbar.word_score = self.is_selection_a_word()

    def deselect(self, tile):
        self.block_gpos_updates = True
        for t in self.selection:
            t.gpos = t.opos
            t.selected = False
        self.selection = []
        self.block_gpos_updates = False
        self.update_word_bar()
        sounds.CANCEL_SELECTION.play()

    def select(self, tile):
        self.block_gpos_updates = True
        self.selection.append(tile)
        tile.selected = True
        self.update_selection()
        self.block_gpos_updates = False
        self.update_word_bar()

    def is_selection_a_word(self):
        has_move = False
        sum_value = 0
        sel = self.selection
        candidate = ''.join([s.letter for s in sel])
        sum_value = sum([s.value for s in sel])
        if candidate in words:
            return candidate, sum_value*len(candidate)
#        if candidate[::-1] in words:
#            return candidate[::-1], sum_value*len(candidate)
        return '', 0

    def confirm_word(self, widget, touch):
        if not widget.collide_point(*touch.pos):
            return
        if self.game_over:
            if self.statusbar.word_score == -1:
                sounds.MENU.play()
                self.next_game()
            if self.statusbar.word_score == -2:
                sounds.MENU.play()
                self.restart_game()
            return
        if self.statusbar.word == '':
            return
        if platform == 'android':
            ws = self.statusbar.word_score
            word = self.statusbar.word
            if len(word) >= 3:
                if len(word) >= 9:
                    App.get_running_app().gs_achieve('achievement_%i_letter_word'%(len(word),))
                else:
                    App.get_running_app().gs_inc_achieve('achievement_%i_letter_word'%(len(word),))
        word_score = self.statusbar.word_score
        hi_score = self.scorebar.hi_score
        self.scorebar.score += self.statusbar.word_score
        self.statusbar.word = ''
        self.statusbar.word_score = 0
        #reset the selected tiles
        for t in self.selection:
            t.active = False
            t.selected = False
            if t in self.free:
                self.free.remove(t)
        #remove unused tiles from the pyramid row to the free space
        for t in self.pyramid[self.active_row]:
            if t not in self.selection:
                self.free.append(t)
        self.update_free_tiles()
        #move the selection back to the pyramid
        self.pyramid[self.active_row] = self.selection
        self.update_pyramid_row_tiles()
        #empty the selection
        self.selection = []
        #update the position of the free tiles
        self.update_free_tiles()
        #now activate the next row
        self.active_row += 1
        if self.active_row < board_size:
            for t in self.pyramid[self.active_row]:
                t.active = True
        sounds.WORD_COMPLETED.play()
        if self.scorebar.score > hi_score:
            if self.scorebar.score >= self.scorebar.target[2] > self.scorebar.score - word_score:
                Clock.schedule_once(lambda *args: sounds.WORD_COMPLETED.play(), 0.25)
                Clock.schedule_once(lambda *args: sounds.WORD_COMPLETED.play(), 0.5)
                Clock.schedule_once(lambda *args: sounds.WORD_COMPLETED.play(), 0.75)
            elif self.scorebar.score >= self.scorebar.target[1] > self.scorebar.score - word_score:
                Clock.schedule_once(lambda *args: sounds.WORD_COMPLETED.play(), 0.25)
                Clock.schedule_once(lambda *args: sounds.WORD_COMPLETED.play(), 0.5)
            elif self.scorebar.score >= self.scorebar.target[0] > self.scorebar.score - word_score:
                Clock.schedule_once(lambda *args: sounds.WORD_COMPLETED.play(), 0.25)
        self.check_game_over()

    def check_game_over(self):
        if self.active_row < board_size:
            tiles = ''.join([t.letter for t in self.pyramid[self.active_row] + self.free])
            if len(tiles)<=6:
                #if there are 6 or few tiles available, lets check all permutations
                for i in range(2,7):
                    for w in itertools.permutations(tiles, i):
                        if ''.join(w) in words:
                            return
            else:
                #too computationally intensive to check more than 6 letters, so lets use a crude heuristic
                vlike = 'AEIOUY'
                for v in vlike:
                    if v in tiles:
                        return
        if self.active_row < board_size:
            for t in self.pyramid[self.active_row]:
                t.active = False
        for t in self.free:
            t.active = False
        self.game_over = True
        if self.scorebar.hi_score >= self.scorebar.target[0]:
            self.statusbar.word = 'NEXT GAME'
            self.statusbar.word_score = -1
            Clock.schedule_once(lambda *args: sounds.LEVEL_COMPLETED.play(), 1)
        else:
            self.statusbar.word = 'REPLAY GAME'
            self.statusbar.word_score = -2
            Clock.schedule_once(lambda *args: sounds.LEVEL_FAILED.play(), 1)

    def path_state(self):
        return os.path.join(get_user_path(),'gamestate.pickle')

    def load_state(self):
        path = self.path_state()
        if not os.path.exists (path):
            return False
        Logger.info ('loading game data')
#        store = file(path,'rb')
#        game = pickle.loads (store.read ())
#        grid_data = game['grid_data']
#        self.original_gps = game['original_gps']
#        self.selection = game['selection']
#        self.statusbar.word_score = game['word_score']
#        self.statusbar.word = game['word']
#        self.scorebar.set_game_id(game['high_score_id'])
#        self.scorebar.score = game['score']
#
#        self.block_gpos_updates = True
#        self.tiles = {}
#
#        for t,gd in zip(self.tile_widgets,grid_data):
#            letter, value, selected, gpos, cpos, opos = gd
#            t.letter = letter
#            t.value = value
#            t.cpos = cpos
#            t.opos = opos
#            t.gpos = gpos
#            t.selected = selected
#            self[t.gpos] = t
#
#        store.close ()
#        os.remove(path)

        self.block_gpos_updates = False
        return True

    def save_state(self):
#         grid_data = []
#         for t in self.tile_widgets:
#             grid_data.append((str(t.letter), int(t.value), bool(t.selected), tuple(t.gpos), tuple(t.cpos), tuple(t.opos)))
#
#         store = file(self.path_state(),'wb')
#         data = dict(
#            version = __version__,
#            grid_data = grid_data,
#            original_gps = self.original_gps,
#            selection = self.selection,
#            word = self.statusbar.word,
#            word_score = self.statusbar.word_score,
#            high_score_id = self.scorebar.game_id,
#            score = self.scorebar.score)
#         store.write(pickle.dumps(data))
#         store.close()
         Logger.info ('saved game data')

class Instructions(BoxLayout):
    m_scrollview = ObjectProperty()
    def __init__(self):
        super(Instructions,self).__init__()

#    def on_touch_down(self, touch):
#        if not self.m_scrollview.collide_point(*touch.pos):
#            if not self.m_scrollview.child.collide_point(*touch.pos):
#                return True
#
#    def on_touch_up(self, touch):
#        if not self.m_scrollview.collide_point(*touch.pos):
#            if not self.m_scrollview.child.collide_point(*touch.pos):
#                return True


class Menu(BoxLayout):
    selection = NumericProperty(-1)
    prev_game = BooleanProperty()
    next_game = BooleanProperty()
    def __init__(self):
        super(Menu,self).__init__()

    def ui_update(self, scorebar, *args):
        self.prev_game = scorebar.game_id>1
        self.next_game = scorebar.hi_score > scorebar.target[0] or scorebar.played>10

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            return True
        return False

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            for c in self.children:
                if c.collide_point(*touch.pos) and c.active:
                    self.selection = c.value
                    sounds.MENU.play()
                    return True
            return True
        return False
                
class ScoreBar(BoxLayout):
    score = NumericProperty()
    hi_score = NumericProperty()
    game_id = NumericProperty(-1)
    played = NumericProperty()

    def __init__(self,**kwargs):
        super(ScoreBar,self).__init__(**kwargs)
        try:
            self.store = JsonStore(os.path.join(get_user_path(),'scores.json'))
        except:
            self.store = None
        self.bind(game_id = self.set_game_id)
        self.bind(score = self.score_changed)
        self.bind(played = self.set_played)

    def get_status(self):
        try:
            if self.store.exists('status'):
                data = self.store.get('status')
                self.game_id = data['game_id']
            else:
                self.game_id = 1
        except:
            self.game_id = 1

    def set_played(self, *args):
        try:
            self.store.put(str(self.game_id), high_score=int(self.hi_score), played = int(self.played))
        except:
            pass
        Logger.info("played game %i %i times"%(self.game_id, self.played))

    def set_game_id(self, *args):
        Logger.info("setting game %i"%self.game_id)
        if self.game_id > 0:
            try:
                data = self.store.put('status', game_id = self.game_id)
            except:
                pass
        try:
            if self.store.exists(str(self.game_id)):
                data = self.store.get(str(self.game_id))
                self.hi_score = data['high_score']
                self.played = data['played']
            else:
                raise IOError
        except:
            self.hi_score = 0
            self.played = 0
        Logger.info("high score %i"%self.hi_score)
        self.score = 0
        random.seed(self.game_id)

    def score_changed(self, *args):
        Logger.info("setting game score %i for game %i"%(self.score,self.game_id))
        if self.score > self.hi_score:
            self.hi_score = self.score
            try:
                self.store.put(str(self.game_id), high_score=int(self.hi_score), played = int(self.played))
            except:
                pass
        if platform == 'android':
            #TODO: FIXME
            if self.game_id>0:
                App.get_running_app().gs_score(leaderboard_daily_challenge_highscore, int(self.score))
            App.get_running_app().gs_score(leaderboard_highscore, int(self.score))
            if self.score > 600:
                App.get_running_app().gs_achieve('achievement_score_of_600')
            if self.score > 800:
                App.get_running_app().gs_achieve('achievement_score_of_800')
            if self.score > 1000:
                App.get_running_app().gs_achieve('achievement_score_of_1000')
            if self.score > 1200:
                App.get_running_app().gs_achieve('achievement_score_of_1200')

class StatusBar(BoxLayout):
    w_word_label = ObjectProperty()
    word = StringProperty()
    word_score = NumericProperty()
    def __init__(self,**kwargs):
        super(StatusBar,self).__init__(**kwargs)

class MessageBar(BoxLayout):
    message = StringProperty()
    def __init__(self,**kwargs):
        super(MessageBar,self).__init__(**kwargs)

    def game_changed(self, scorebar, game_id):
        self.game_id = game_id


class SevenWordsApp(App):
    colors = DictProperty()
    def build(self):
        try:
#            self.colors = colors.load_theme('default')
            self.colors = colors.load_theme(self.config.get('theme','theme'))
        except KeyError:
            self.colors = colors.load_theme('default')

        Builder.load_file('words.kv')
        self.gb = Board()
        Window.bind(on_keyboard = self.on_keyboard)

        if platform == 'android':
            self.use_google_play = self.config.getint('play', 'use_google_play')
            if self.use_google_play:
                googleplayclient.connect(self.activate_google_play_success, self.activate_google_play_failed)
            else:
                Clock.schedule_once(self.ask_google_play, .5)

        return self.gb

    def set_next_theme(self):
        themes = list(colors.themes)
        ind = themes.index(self.config.get('theme','theme'))
        new_theme = themes[ind-1]
        self.config.set('theme', 'theme', new_theme)
        self.config.write()
        self.colors = colors.load_theme(themes[ind-1])
        self.gb.draw_background()

    def build_config(self, config):
        config.setdefaults('theme', {'theme': 'beach'})
        if platform == 'android':
            config.setdefaults('play', {'use_google_play': '0'})

    def open_settings(self, *args):
        pass

    def gs_score(self, score_type, score):
        if platform == 'android' and self.use_google_play>0 and score>0:
            googleplayclient.submit_score(score_type, int(score))

    def gs_show_leaderboard(self, score_type):
        if platform == 'android':
            if self.use_google_play>0:
                googleplayclient.show_leaderboard(score_type)
            else:
                self.ask_google_play()

    def gs_achieve(self, achievement_id):
        if platform == 'android' and self.use_google_play>0:
            googleplayclient.unlock_achievement(achievement_id)

    def gs_inc_achieve(self, achievement_id):
        if platform == 'android' and self.use_google_play>0:
            googleplayclient.increment_achievement(achievement_id)

    def gs_show_achievements(self):
        if platform == 'android':
            if self.use_google_play>0:
                googleplayclient.show_achievements()
            else:
                self.ask_google_play()

    def ask_google_play(self, *args):
        popup = GooglePlayPopup()
        popup.open()

    def activate_google_play(self):
        self.config.set('play', 'use_google_play', '1')
        self.config.write()
        googleplayclient.connect(self.activate_google_play_success, self.activate_google_play_failed)

    def activate_google_play_success(self, *args):
        self.use_google_play = 1

    def activate_google_play_failed(self, *args):
        self.use_google_play = 0

    def on_keyboard(self, window, key, scancode=None, codepoint=None, modifier=None):
        '''
        used to manage the effect of the escape key
        '''
        if key == 27:
            sounds.MENU.play()
            if self.gb.instructions in self.gb.children:
                self.gb.remove_widget(self.gb.instructions)
            elif self.gb.menu not in self.gb.children:
                self.gb.show_menu()
            else:
                self.gb.hide_menu()
            return True
        return False

    def on_pause(self):
        '''
        trap on_pause to keep the app alive on android
        '''
        self.gb.save_state()
#        if platform == 'android':
#            googleplayclient.logout()
        return True

    def on_resume(self):
        pass
#        if platform == 'android':
#            googleplayclient.connect(self.activate_google_play_success, self.activate_google_play_failed)

    def on_stop(self):
        self.gb.save_state()

if __name__ == '__main__':
    gameapp = SevenWordsApp()
    gameapp.run()

