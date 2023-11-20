
def color_avg(c1, c2, wgt):
    return [wgt*a+(1-wgt)*b for a,b in zip(c1,c2)]

default_theme = {
    'background': (0.7, 0.7, 0.9, 1),
    'tile': (0.5, 0.5, 0.75, 1),
    'tile_selected': (0, 0, 0.5, 1),
    'tile_inactive': (0.7, 0.7, 0.7, 1),
    'tile_letter_text': (0.9, 0.9, 0.9, 1),
    'word_score_background': (0, 0, 0.5, 1), #(0, 0, 0.8, 1),
    'word_score_text': (0.9, 0.9, 0.9, 1), #(0.9, 0.9, 0.9, 1),
    'score_text': (0.9, 0.9, 0.9, 1),
    'checker': (0.8, 0.8, 0.9, 1),
    'move_candidates': (0.2, 0.3, 0.7, 1),
    'menu_button_background': (0.5, 0.8, 0.7, 1),
    'menu_button_foreground': (0.9, 0.9, 0.9, 1),
    'menu_button_foreground_disabled': (0.5, 0.5, 0.5, 1),
    }


beach_theme = {
    'background': (20,140,156,255),
    'tile': (255,241,156,255),
    'tile_selected': (232, 180, 120, 255),
    'tile_inactive': (200, 200, 200, 255),
    'tile_letter_text': (86, 148, 155, 255),
    'word_score_background' : (252, 200, 130, 255),
    'word_score_text': (86, 148, 155, 255),
    'score_text': (221, 238, 242, 255),
    'checker': (0, 202, 199, 255),
    'move_candidates': (252, 200, 130, 255),
    'menu_button_background': (252, 136, 61, 255),
    'menu_button_foreground': (255, 255, 255, 255),
    'menu_button_foreground_disabled': (128, 128, 128, 255),
    }

themes = {
    'default': default_theme,
    'beach' : beach_theme
    }

def load_theme(theme_name):
    global background, tile, tile_selected, tile_inactive, tile_letter_text, word_score_background, \
        word_score_text, score_text, checker, move_candidates, menu_button_background
    theme = themes[theme_name]
    if theme_name != 'default':
        c = lambda colors: tuple(1.0*col/255 for col in colors)
        theme = dict([(k, c(theme[k])) for k in theme])
    theme['bronze'] =  [205.0/255, 127.0/255, 50.0/255, 1.0]
    theme['silver'] = [192.0/255, 192.0/255, 192.0/255, 1.0]
    theme['gold'] = [1.0, 215.0/255, 0.0, 1.0]
    bg = theme['background']
    gry = [0.3,0.3,0.3,1.0]
    theme['bronze_off'] = color_avg(theme['silver'], bg,0.2)
    theme['silver_off'] = color_avg(theme['silver'], bg,0.2)
    theme['gold_off'] = color_avg(theme['silver'], bg,0.2)
    background = theme['background']
    tile = theme['tile']
    tile_selected = theme['tile_selected']
    tile_inactive = theme['tile_inactive']
    tile_letter_text = theme['tile_letter_text']
    word_score_background = theme['word_score_background']
    word_score_text = theme['word_score_text']
    score_text = theme['score_text']
    checker = theme['checker']
    move_candidates = theme['move_candidates']
    menu_button_background = theme['menu_button_background']
    return theme
