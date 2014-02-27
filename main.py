import kivy
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import (StringProperty, ObjectProperty,
    NumericProperty, ListProperty, BooleanProperty, DictProperty)
from kivy.clock import Clock
import kivent_cython
from random import random
from kivent_cython import GameSystem, GameScreenManager, GameWorld
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.modalview import ModalView
from kivy.uix.stacklayout import StackLayout
from kivy.uix.behaviors import ToggleButtonBehavior, ButtonBehavior
from kivy.uix.label import Label
from kivy.animation import Animation
from kivy.uix.screenmanager import Screen

_group_colors = {}
_group_colors['Movies'] = (0.941176471, 0.68627451, 0.0, 1.0)
_group_colors['Clothes'] = (0.611764706, 1.0, 0.690196078, 1.0)
_group_colors['Food'] = (0.819607843, 0.278431373, 0.0, 1.0)
_group_colors['Home'] = (0.839215686, 0.988235294, 0.02745098, 1.0)
_group_colors['Beauty/Health'] = (0.537254902, 0.0, 0.639215686, 1.0)
_group_colors['Gifts'] = (0.298039216, 0.490196078, 1.0, 1.0)
_group_colors['Electronics'] = (0.0, 0.501960784, 0.5019607841, 1.0)
_group_colors['Bathrooms'] = (.9, .9, .9, 1.0)
_group_colors['Shoes'] = (1.0, 0.450980392, 0.0, 1.0)
_group_colors['Jewelry'] = (1.0, 0.066666667, 0.815686275, 1.0)
_group_colors['Accessories'] = (0.0, 0.780392157, 0.192156863, 1.0)
_group_colors['Vacant'] = (1.0, 1.0, 1.0, 1.0)


class ToggleStoreButton(ToggleButtonBehavior, StackLayout):
    color = ListProperty([1., 1., 1., 1.])
    group_name = StringProperty('')
    image_name = StringProperty('')
    reset_color = ListProperty([1., 1., 1., 1.])


class AdScreen(Screen):
    name = StringProperty(None)
    source = StringProperty(None)
    next_screen = StringProperty(None)


class StoreInformation(FloatLayout):
    store_name = StringProperty('Default')
    store_group = StringProperty('Vacant')
    logo_image = StringProperty('')
    collapsed = BooleanProperty(True)
    current_color = ListProperty([1., 1., 1., 1.])


class StoreLabel(ButtonBehavior, Label):
    color = ListProperty([1., 1., 1., 1.])
    entity_id = NumericProperty(None)


class StoreList(StackLayout):

    def __init__(self, **kwargs):
        super(StoreList, self).__init__(**kwargs)
        self.store_labels = {}

    def update_stores(self):
        store_system = self.gameworld.systems['store_data']
        data = store_system.get_list_of_store_names()
        store_names =  data[0]
        indices = data[2]
        ent_ids = data[3]
        store_colors = data[1]
        store_labels = self.store_labels
        self.clear_widgets()
        stores_to_add = {}
        s_aw = self.add_widget
        for i in range(len(store_names)):
            store_name = store_names[i]
            if store_name not in store_labels:
                store_labels[store_name] = store_wid = StoreLabel(
                text=str(indices[i]) + '. ' + store_names[i], 
                color=store_colors[i], entity_id=ent_ids[i])
                store_wid.bind(on_release=self.select_store_callback)
            else:
                store_wid = store_labels[store_name]
                store_wid.text = str(indices[i]) + '. ' + store_name
                store_wid.color = store_colors[i]
                store_wid.entity_id = ent_ids[i]
            stores_to_add[store_name] = store_wid
        
        ns = list(set(store_names))
        ns.sort()
        for i in range(len(ns)):
            s_aw(stores_to_add[ns[i]])

    def update_colors(self):
        gameworld = self.gameworld
        entities = gameworld.entities
        for child in self.children:
            if isinstance(child, StoreLabel):
                entity_id = child.entity_id
                entity = entities[entity_id]
                store_data = entity['store_data']
                child.color = store_data['color']


    def select_store_callback(self, instance):
        self.gameworld.systems['store_data'].focus_entity(instance.entity_id)


class Position(GameSystem):
    pass


class StoreData(GameSystem):
    focused_entity = NumericProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super(StoreData, self).__init__(**kwargs)
        self.groups_highlighted = set()

    def on_focused_entity(self, instance, value):
        gameworld = self.gameworld
        main_screen = gameworld.gamescreenmanager.main_screen
        store_information = main_screen.store_information
        if value != None:
            entities = gameworld.entities
            entity = entities[value]
            store_data = entity['store_data']
            store_information.store_name = store_data['store_name']
            store_information.store_group = store_data['store_group']
            if store_information.y < 0:
                anim = Animation(y=0, duration = .5)
                anim.start(store_information)
            else:
                anim1 = Animation(y=-200, duration = .25)
                anim2 = Animation(y=0, duration =.25)
                anim = anim1 + anim2
                anim.start(store_information)
        else:
            anim = Animation(y=-200, duration = .5)
            anim.start(store_information)

    def check_collide(self, touch):
        collided = []
        gameworld = self.gameworld
        game_view = gameworld.systems[gameworld.viewport]
        camera_pos = game_view.camera_pos
        x, y = touch.x - camera_pos[0], touch.y - camera_pos[1]
        entities = gameworld.entities
        for entity_id in self.entity_ids:
            entity = entities[entity_id]
            size = entity['shape_renderer']['size']
            position = entity['position']['position']
            pos_x, pos_y = position
            w, h = size[0]/2., size[1]/2.
            if pos_x - w < x < pos_x + w:
                if pos_y - h < y < pos_y + h:
                    collided.append(entity_id)
        return collided

    def label_map(self):
        entities = self.gameworld.entities
        layout = self.layout
        layout.clear_widgets()
        l_aw = layout.add_widget
        i = 1
        entity_ids = self.entity_ids
        for entity_id in entity_ids:
            entity = entities[entity_id]
            store_data = entity['store_data']
            group = store_data['store_group']
            if 'master' in store_data and not store_data['master']:
                continue
            if group != 'Vacant':
                number_label = Label(text=str(i), size_hint=(None, None), 
                center=entity['position']['position'], color=(0., 0., 0., 1.),
                font_size='12sp', font_name='assets/fonts/Exo_2/Exo2-SemiBold.ttf')
                l_aw(number_label)
                store_data['index'] = i
                i += 1

    def get_list_of_store_names(self):
        entities = self.gameworld.entities
        l = []
        colors = []
        indices = []
        ent_ids = []
        ea = ent_ids.append
        ia = indices.append
        la = l.append
        ca = colors.append
        entity_ids = self.entity_ids
        groups_highlighted = self.groups_highlighted
        do_group = False
        if list(groups_highlighted) != []:
            do_group = True
        for entity_id in entity_ids:
            entity = entities[entity_id]
            store_data = entity['store_data']
            group = store_data['store_group']
            if 'master' in store_data and not store_data['master']:
                continue 
            if group != 'Vacant' and not do_group:
                la(store_data['store_name'])
                ca(store_data['color'])
                ia(store_data['index'])
                ea(entity_id)
            elif do_group:
                if group in groups_highlighted:
                    la(store_data['store_name'])
                    ca(store_data['color']) 
                    ia(store_data['index'])
                    ea(entity_id)  
        return (l, colors, indices, ent_ids)

    def clear_entity_color(self, entity_id):
        entities = self.gameworld.entities
        entity = entities[entity_id]
        store_data = entity['store_data']
        group = store_data['store_group']

        if group == 'Vacant':
            store_data['color'] = (.75, .75, .75, 1.0)
        elif group == 'Bathrooms':
            store_data['color'] = (.9, .9, .9, 1.0)
        else:
            store_data['color'] = (1.0, 1.0, 1.0, 1.0)


    def clear_all_entities_color(self):
        entities = self.gameworld.entities
        for entity_id in self.entity_ids:
            entity = entities[entity_id]
            store_data = entity['store_data']
            group = store_data['store_group']
            if group == 'Vacant':
                store_data['color'] = (.75, .75, .75, 1.0)
            elif group == 'Bathrooms':
                store_data['color'] = (.9, .9, .9, 1.0)
            else:
                store_data['color'] = (1.0, 1.0, 1.0, 1.0)

    def add_group_to_highlight(self, group):
        self.groups_highlighted.add(group)
        self.update_highlight()
        self.update_store_list()

    def remove_group_from_highlight(self, group):
        self.groups_highlighted.remove(group)
        self.update_highlight()
        self.update_store_list()

    def update_store_list(self):
        gamescreenmanager = self.gameworld.gamescreenmanager
        main_screen = gamescreenmanager.main_screen
        main_screen.storelist.update_stores()

    def focus_entity(self, entity_id):
        entities = self.gameworld.entities
        root = self.app.root
        groups_highlighted = self.groups_highlighted
        entity = entities[entity_id]
        self.focused_entity = entity_id
        store_data = entity['store_data']
        group = store_data['store_group']
        if group != 'Vacant' and group != 'Bathrooms' and group not in groups_highlighted:
            self.add_group_to_highlight(group)
            root.toggle_button(group)
        self.update_highlight()
        
    def highlight_group(self, group):
        gameworld = self.gameworld
        entities = gameworld.entities
        root = self.app.root
        group_colors = root.group_colors
        for entity_id in self.entity_ids:
            entity = entities[entity_id]
            store_data = entity['store_data']
            if store_data['store_group'] == group:
                store_data['color'] = group_colors[group]

    def reset_colors(self):
        entity_ids = self.entity_ids
        entities = self.gameworld.entities
        group_colors = self.app.root.group_colors
        for entity_id in entity_ids:
            entity = entities[entity_id]
            store_data = entity['store_data']
            store_data['color'] = group_colors[store_data['store_group']]
            store_data['darkened'] = False

    def reset_color(self, entity_id):
        group_colors = self.app.root.group_colors
        entities = self.gameworld.entities
        entity = entities[entity_id]
        store_data = entity['store_data']
        store_data['color'] = group_colors[store_data['store_group']]
        store_data['darkened'] = False

    def darken_color(self, entity_id):
        group_colors = self.app.root.group_colors
        entities = self.gameworld.entities
        entity = entities[entity_id]
        store_data = entity['store_data']
        old_color = group_colors[store_data['store_group']]
        if store_data['store_group'] != 'Bathrooms':
            store_data['color'] = (old_color[0]*.5, old_color[1]*.5, old_color[2]*.5, 1.0)
            store_data['darkened'] = True

    def update_highlight(self):
        self.clear_all_entities_color()
        groups_highlighted = self.groups_highlighted
        highlight_group = self.highlight_group
        for group in groups_highlighted:
            highlight_group(group)
        if self.focused_entity != None:
            self.dim_everything_but_selected()
        main_screen = self.gameworld.gamescreenmanager.main_screen
        store_list = main_screen.storelist
        store_list.update_colors()
        

    def dim_everything_but_selected(self):
        groups_highlighted = self.groups_highlighted
        entity_ids = self.entity_ids
        focused_entity = self.focused_entity
        entities = self.gameworld.entities
        darken_color = self.darken_color
        reset_color = self.reset_color
        for entity_id in entity_ids:
            entity = entities[entity_id]
            store_data = entity['store_data']
            if store_data['store_group'] in groups_highlighted:
                if focused_entity != None:
                    if entity_id != focused_entity:
                        if 'linked' in store_data and focused_entity in store_data['linked']:
                            reset_color(entity_id)
                        else:
                            darken_color(entity_id)
                    else:
                        reset_color(entity_id)

    def on_touch_down(self, touch):
        collided = self.check_collide(touch)
        focused_entity = self.focused_entity
        if len(collided) > 0:
            entity_id = collided[0]
            if entity_id != focused_entity:
                self.focus_entity(entity_id)
            else:
                self.focused_entity = None
            return True
        else:
            self.focused_entity = None
            self.update_highlight()
            return False


class KioskView(Widget):
    info_popup = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(KioskView, self).__init__(**kwargs)
        Clock.schedule_once(self.init_game, 2.5)

    def on_touch_down(self, touch):
        gameworld = self.gameworld
        gamescreenmanager = gameworld.gamescreenmanager
        if not super(GameScreenManager, gamescreenmanager).on_touch_down(touch):
            super(GameWorld, gameworld).on_touch_down(touch)

    def toggle_button(self, group):
        gameworld = self.gameworld
        gamescreenmanager = gameworld.gamescreenmanager
        main_screen = gamescreenmanager.main_screen
        button_layout = main_screen.button_layout
        for wid in button_layout.children:
            if wid.group_name == group:
                wid._do_press()
                wid._do_release()

    def init_game(self, dt):
        self.setup_group_colors()
        self.setup_store_shapes()
        self.setup_stores()
        self.setup_states()
        #self.setup_carousel()
        Clock.schedule_interval(self.update, 1./10.)
        Clock.schedule_once(self.setup_2, 5.)

    def setup_2(self, dt):
        self.draw_stores()
        self.gameworld.systems['store_data'].label_map()
        self.gameworld.gamescreenmanager.main_screen.storelist.update_stores()
        self.set_state()


    def setup_carousel(self):
        main_screen = self.gameworld.gamescreenmanager.main_screen
        ad_manager = main_screen.ad_manager
        ad_manager.current = 'bextr'
        def update_carousel(dt):
            ad_manager.current = ad_manager.current_screen.next_screen
        Clock.schedule_interval(update_carousel, 5.0)

    def setup_group_colors(self):
        self.group_colors = _group_colors
        print self.group_colors

    def setup_store_shapes(self):
        self.store_shapes = store_shapes = {}
        store_shapes['0'] = {'size': (42, 600)}
        store_shapes['1'] = {'size': (300, 264)}
        store_shapes['2'] = {'size': (142, 544)}
        store_shapes['3'] = {'size': (64, 164)}
        store_shapes['4'] = {'size': (116, 228)}
        store_shapes['5'] = {'size': (80, 128)}
        store_shapes['6'] = {'size': (90, 116)}
        store_shapes['7A'] = {'size': (160, 94)}
        store_shapes['7B'] = {'size': (118, 92)}
        store_shapes['8'] = {'size': (26, 34)}
        store_shapes['9'] = {'size': (18, 86)}
        store_shapes['10'] = {'size': (24, 34)}
        store_shapes['11'] = {'size': (24, 30)}
        store_shapes['12'] = {'size': (22, 26)}
        store_shapes['13'] = {'size': (26, 42)}
        store_shapes['14'] = {'size': (22, 128)}
        store_shapes['15'] = {'size': (24, 30)}
        store_shapes['16'] = {'size': (20, 110)}
        store_shapes['17'] = {'size': (20, 50)}
        store_shapes['18'] = {'size': (20, 76)}
        store_shapes['19'] = {'size': (16, 128)}
        store_shapes['20'] = {'size': (18, 50)}
        store_shapes['21'] = {'size': (12, 76)}
        store_shapes['22'] = {'size': (20, 76)}
        store_shapes['23'] = {'size': (16, 76)}
        store_shapes['24'] = {'size': (36, 250)}
        store_shapes['25'] = {'size': (18, 250)}
        store_shapes['26'] = {'size': (18, 236)}
        store_shapes['27'] = {'size': (58, 100)}
        store_shapes['28'] = {'size': (58, 24)}
        store_shapes['29'] = {'size': (12, 58)}
        store_shapes['30'] = {'size': (132, 228)}
        store_shapes['31'] = {'size': (80, 24)}
        store_shapes['32'] = {'size': (22, 58)}
        store_shapes['33'] = {'size': (28, 36)}
        store_shapes['34'] = {'size': (28, 18)}
        store_shapes['35'] = {'size': (16, 68)}
        store_shapes['36'] = {'size': (18, 68)}
        store_shapes['37'] = {'size': (24, 70)}
        store_shapes['38'] = {'size': (12, 86)}
        store_shapes['39'] = {'size': (20, 16)}
        store_shapes['40'] = {'size': (22, 36)}
        store_shapes['41'] = {'size': (18, 28)}
        store_shapes['42'] = {'size': (18, 24)}

    def setup_stores(self):
        self.stores = stores = {}
        stores['Megaplex'] = {'shape': '1', 'pos': (464, 910), 
            'name': 'Larry H. Miller Megaplex', 'group': 'Movies'}
        stores['Macys'] = {'shape': '2', 'pos': (976, 674),
            'name': "Macy's", 'group': 'Clothes'}
        stores['JCPenny'] = {'shape': '2', 'pos': (49, 674), 
            'name': 'J.C. Penney', 'group': 'Clothes'}
        stores['RedRobin'] = {'shape': '6', 'pos': (827, 411), 
            'name': 'Red Robin', 'group': 'Food'}
        stores['ROSS'] = {'shape': '30', 'pos': (674, 399), 
            'name': 'ROSS', 'group': 'Clothes'}
        stores['Movies9A'] = {'shape': '7A', 'pos': (819, 887),
            'name': 'Movies 9', 'group': 'Movies'}
        stores['Movies9B'] = {'shape': '7B', 'pos': (840, 797),
            'name': 'Movies 9', 'group': 'Movies'}
        stores['BedBathBeyond'] = {'shape': '4', 'pos': (265, 394),
            'name': 'Bed Bath and Beyond', 'group': 'Home'}
        stores['Ulta'] = {'shape': '3', 'pos': (158, 426),
            'name': 'Ulta', 'group': 'Beauty/Health'}
        stores['Hammond'] = {'shape': '9', 'pos': (890, 705),
            'name': 'Hammond', 'group': 'Gifts'}
        stores['LACuts'] = {'shape': '9', 'pos': (870, 705),
            'name': 'L.A. Cuts', 'group': 'Beauty/Health'}
        stores['WestValleyMusic'] = {'shape': '9', 'pos': (850, 705),
            'name': 'West Valley Music', 'group': 'Gifts'}
        stores['ZAGG'] = {'shape': '9', 'pos': (830, 705),
            'name': 'ZAGG', 'group': 'Electronics'}
        stores['Vacant1'] = {'shape': '9', 'pos': (810, 705),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['UrbanExpress'] = {'shape': '9', 'pos': (790, 705),
            'name': 'Urban Express', 'group': 'Clothes'}
        stores['OrangeJulius'] = {'shape': '10', 'pos': (765, 682),
            'name': 'Orange Julius', 'group': 'Food'}
        stores['RiceVillage'] = {'shape': '11', 'pos': (765, 718),
            'name': 'Rice Village', 'group': 'Food'}
        stores['Vacant2'] = {'shape': '11', 'pos': (765, 752),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant3'] = {'shape': '11', 'pos': (765, 786),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['OsakaJapan'] = {'shape': '11', 'pos': (765, 820),
            'name': 'Osaka Japan', 'group': 'Food'}
        stores['Vacant4'] = {'shape': '8', 'pos': (635, 917),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['TropicalJuice'] = {'shape': '8', 'pos': (635, 878),
            'name': 'Tropical Juice', 'group': 'Food'}
        stores['Vacant5'] = {'shape': '8', 'pos': (635, 839),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Bathroom'] = {'shape': '13', 'pos': (635, 795),
            'name': 'Bathrooms', 'group': 'Bathrooms'}
        stores['ChineseGourmetExpress'] = {'shape': '12', 'pos': (663, 787),
            'name': 'Chinese Gourmet Express', 'group': 'Food'}
        stores['Vacant6'] = {'shape': '12', 'pos': (689, 787),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['ChurrosPizzaria'] = {'shape': '15', 'pos': (716, 770),
            'name': "Churro's Ole' Pizzeria", 'group': 'Food'}
        stores['GreekKabob'] = {'shape': '10', 'pos': (716, 734),
            'name': "Greek Kabob", 'group': 'Food'}
        stores['Subway'] = {'shape': '10', 'pos': (716, 696),
            'name': "Subway", 'group': 'Food'}
        stores['HotDogStick'] = {'shape': '10', 'pos': (716, 658),
            'name': "Hot Dog on a Stick", 'group': 'Food'}
        stores['Vacant20'] = {'shape': '14', 'pos': (688, 705),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant19'] = {'shape': '14', 'pos': (661, 705),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant18'] = {'shape': '14', 'pos': (634, 705),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant7'] = {'shape': '16', 'pos': (608, 714),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Maurices'] = {'shape': '16', 'pos': (583, 714),
            'name': "Maurice's", 'group': 'Clothes'}
        stores['Bath and Body Works'] = {'shape': '16', 'pos': (558, 714),
            'name': 'Bath and Body Works', 'group': 'Home'}
        stores['Vacant8'] = {'shape': '17', 'pos': (533, 684),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant9'] = {'shape': '18', 'pos': (458, 698),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Journeys'] = {'shape': '16', 'pos': (432, 715),
            'name': "Journey's", 'group': 'Clothes'}
        stores['FootActionUSA'] = {'shape': '16', 'pos': (406, 715),
            'name': 'FootAction USA', 'group': 'Shoes'}
        stores['ValentinesDayGifts'] = {'shape': '16', 'pos': (380, 715),
            'name': "Valentine's Day Gifts", 'group': 'Gifts'}
        stores['ModaBella'] = {'shape': '19', 'pos': (356, 706),
            'name': 'Moda Bella', 'group': 'Clothes'}
        stores['BoostMobile'] = {'shape': '19', 'pos': (336, 706),
            'name': 'Boost Mobile', 'group': 'Electronics'}
        stores['GNC'] = {'shape': '19', 'pos': (316, 706),
            'name': 'GNC', 'group': 'Beauty/Health'}
        stores['TheNerdStore'] = {'shape': '19', 'pos': (296, 706),
            'name': 'The Nerd Store', 'group': 'Gifts'}
        stores['RadioShack'] = {'shape': '19', 'pos': (276, 706),
            'name': 'RadioShack', 'group': 'Electronics'}
        stores['Vacant10'] = {'shape': '19', 'pos': (256, 706),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['XZone'] = {'shape': '19', 'pos': (236, 706),
            'name': 'X-Zone', 'group': 'Clothes'}
        stores['Wind&Waters'] = {'shape': '19', 'pos': (216, 706),
            'name': 'Wind & Waters', 'group': 'Gifts'}
        stores['Trinkets&Treasures'] = {'shape': '19', 'pos': (196, 706),
            'name': 'Trinkets and Treasures', 'group': 'Gifts'}
        stores['FadsNFashions'] = {'shape': '19', 'pos': (176, 706),
            'name': "Fads N' Fashions", 'group': 'Clothes'}
        stores['TheBazzar'] = {'shape': '19', 'pos': (156, 706),
            'name': 'The Bazzar', 'group': 'Gifts'}
        stores['RyansCustomJewelry'] = {'shape': '19', 'pos': (136, 706),
            'name': "Ryan's Custom Jewelry", 'group': 'Jewelry'}
        stores['Vacant11'] = {'shape': '20', 'pos': (135, 538),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant12'] = {'shape': '21', 'pos': (153, 551),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['MDPhotography'] = {'shape': '21', 'pos': (168, 551),
            'name': 'MD Photography', 'group': 'Gifts'}
        stores['Vacant13'] = {'shape': '21', 'pos': (183, 551),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['JolenesGirlsDresses'] = {'shape': '22', 'pos': (217, 551),
            'name': "Jolene's Girl's Dresses", 'group': 'Clothes'}
        stores['Zumeiz'] = {'shape': '22', 'pos': (242, 551),
            'name': 'Zumeiz', 'group': 'Clothes'}
        stores['Vacant14'] = {'shape': '22', 'pos': (267, 551),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['GameGridArcade'] = {'shape': '22', 'pos': (292, 551),
            'name': 'Game Grid Arcade', 'group': 'Electronics'}
        stores['PaylessShoeSource'] = {'shape': '23', 'pos': (315, 551),
            'name': 'Payless Shoe Source', 'group': 'Shoes'}
        stores['JBVariety'] = {'shape': '24', 'pos': (345, 464),
            'name': 'JB Variety', 'group': 'Clothes'}
        stores['20/20'] = {'shape': '25', 'pos': (376, 464),
            'name': '20/20', 'group': 'Clothes'}
        stores['Vacant16'] = {'shape': '26', 'pos': (398, 457),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant17'] = {'shape': '27', 'pos': (440, 350),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['PursePlus'] = {'shape': '28', 'pos': (440, 417),
            'name': 'Purse Plus', 'group': 'Accessories'}
        stores['TheGamePeddler'] = {'shape': '28', 'pos': (440, 445),
            'name': 'The Game Peddler', 'group': 'Electronics'}
        stores['AsianApp +'] = {'shape': '28', 'pos': (440, 473),
            'name': 'Asian Apps +', 'group': 'Food'}
        stores['PassionNails'] = {'shape': '28', 'pos': (440, 501),
            'name': 'Passion Nails', 'group': 'Beauty/Health'}
        stores['CharleySalon'] = {'shape': '29', 'pos': (417, 546),
            'name': 'Charley Salon', 'group': 'Beauty/Health'}
        stores['PretzelMaker1'] = {'shape': '29', 'pos': (432, 546),
            'name': 'Pretzel Maker', 'group': 'Food'}
        stores['PretzelMaker2'] = {'shape': '29', 'pos': (447, 546),
            'name': 'Pretzel Maker', 'group': 'Food'}
        stores['SchubachJewelers'] = {'shape': '29', 'pos': (462, 546),
            'name': 'Schubach Jewelers', 'group': 'Jewelry'}
        stores['FamousFootwear'] = {'shape': '5', 'pos': (562, 365),
            'name': 'Famous Footwear', 'group': 'Shoes'}
        stores['PopcornCottage'] = {'shape': '31', 'pos': (562, 445),
            'name': 'Popcorn Cottage', 'group': 'Food'}
        stores['X-BrandsCustom'] = {'shape': '31', 'pos': (562, 473),
            'name': 'X-Brands Custom T-Shirts', 'group': 'Food'}
        stores['BrowSpa24'] = {'shape': '31', 'pos': (562, 501),
            'name': 'Brow Spa 24', 'group': 'Beauty/Health'}
        stores['Rave'] = {'shape': '32', 'pos': (591, 546),
            'name': 'Rave', 'group': 'Clothes'}
        stores['Claires'] = {'shape': '32', 'pos': (565, 546),
            'name': "Claire's", 'group': 'Accessories'}
        stores['MorganJewelers'] = {'shape': '33', 'pos': (536, 557),
            'name': 'Morgan Jewelers', 'group': 'Jewelry'}
        stores['TieOneOn'] = {'shape': '34', 'pos': (536, 526),
            'name': 'Tie One On', 'group': 'Accessories'}
        stores['2Love'] = {'shape': '35', 'pos': (616, 551),
            'name': '2 Love', 'group': 'Clothes'}
        stores['Fragranza'] = {'shape': '35', 'pos': (635, 551),
            'name': 'Fragranza', 'group': 'Beauty/Health'}
        stores['CellAgain'] = {'shape': '35', 'pos': (654, 551),
            'name': 'Cell Again', 'group': 'Electronics'}
        stores['ShoeOutlet'] = {'shape': '35', 'pos': (673, 551),
            'name': 'Shoe Outlet', 'group': 'Shoes'}
        stores['Fanzz'] = {'shape': '35', 'pos': (692, 551),
            'name': 'Fanzz', 'group': 'Clothes'}
        stores['DiamondWireless'] = {'shape': '35', 'pos': (711, 551),
            'name': 'Diamond Wireless', 'group': 'Electronics'}
        stores['TMobile'] = {'shape': '36', 'pos': (731, 551),
            'name': 'T-Mobile', 'group': 'Electronics'}
        stores['Vacant21'] = {'shape': '37', 'pos': (888, 508),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['TheAccessoryShop'] = {'shape': '38', 'pos': (866, 515),
            'name': 'The Accessory Shop', 'group': 'Accessories'}
        stores['NikkisBridal'] = {'shape': '38', 'pos': (850, 515),
            'name': "Nikki's Bridal", 'group': 'Clothes'}
        stores['UniqueGifts'] = {'shape': '38', 'pos': (834, 515),
            'name': 'Unique Gifts', 'group': 'Gifts'}
        stores['KidsFashion'] = {'shape': '38', 'pos': (818, 515),
            'name': "Kid's Fashion", 'group': 'Clothes'}
        stores['JewelryDoctor'] = {'shape': '38', 'pos': (802, 515),
            'name': 'Jewelry Doctor', 'group': 'Jewelry'}
        stores['Vacant22'] = {'shape': '38', 'pos': (786, 515),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant23'] = {'shape': '39', 'pos': (865, 613),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant24'] = {'shape': '39', 'pos': (825, 613),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant25'] = {'shape': '39', 'pos': (785, 613),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant26'] = {'shape': '39', 'pos': (745, 613),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant27'] = {'shape': '39', 'pos': (705, 613),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant28'] = {'shape': '39', 'pos': (665, 613),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant29'] = {'shape': '39', 'pos': (625, 613),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant30'] = {'shape': '39', 'pos': (585, 613),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant31'] = {'shape': '39', 'pos': (545, 613),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant32'] = {'shape': '39', 'pos': (450, 613),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant33'] = {'shape': '39', 'pos': (410, 613),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant34'] = {'shape': '39', 'pos': (366, 613),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant35'] = {'shape': '39', 'pos': (326, 613),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant36'] = {'shape': '39', 'pos': (286, 613),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant37'] = {'shape': '39', 'pos': (250, 613),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant38'] = {'shape': '39', 'pos': (216, 613),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant39'] = {'shape': '39', 'pos': (184, 613),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant40'] = {'shape': '39', 'pos': (150, 613),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant41'] = {'shape': '40', 'pos': (495, 540),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant42'] = {'shape': '41', 'pos': (496, 380),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant43'] = {'shape': '42', 'pos': (760, 380),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant44'] = {'shape': '42', 'pos': (760, 420),
            'name': 'Vacant', 'group': 'Vacant'}

    def open_popup(self, store_name, logo, pos, entity_id):
        self.store_info_dismiss()
        info_popup = self.info_popup
        info_popup.store_name = store_name
        info_popup.logo_image = logo
        info_popup.pos = pos
        info_popup.current_entity_id = entity_id
        if info_popup not in self.children:
            #self.add_widget(info_popup)
            pass

    def store_info_dismiss(self):
        info_popup = self.info_popup
        if info_popup.current_entity_id:
            store_data = self.gameworld.systems['store_data']
            #store_data.reset_colors()
        if info_popup in self.children:
            self.remove_widget(info_popup)

    def highlight_group(self, group):
        store_data = self.gameworld.systems['store_data']
        groups_highlighted = store_data.groups_highlighted
        if group not in groups_highlighted:
            store_data.add_group_to_highlight(group)
        else:
            store_data.remove_group_from_highlight(group)

    def update(self, dt):
        self.gameworld.update(dt)

    def draw_stores(self):
        stores = self.stores
        store_shapes = self.store_shapes
        movies9a = None
        movies9b = None
        for key in stores:
            store = stores[key]
            pos = store['pos']
            size = store_shapes[store['shape']]['size']
            group = store['group']
            name = store['name']
            ent_id = self.draw_store(size, pos, name, group)
            if key == 'Movies9A':
                movies9a = ent_id
            elif key == 'Movies9B':
                movies9b = ent_id
        entities = self.gameworld.entities
        ent_9a = entities[movies9a]
        ent_9b = entities[movies9b]
        ent_9a['store_data']['linked'] = [movies9b]
        ent_9b['store_data']['linked'] = [movies9a]
        ent_9a['store_data']['master'] = True
        ent_9b['store_data']['master'] = False

    def draw_store(self, size, pos, name, group):
        store_size = size
        color = (1.0, 1.0, 1.0, 1.0)
        if group == 'Vacant':
            color = (.75, .75, .75, 1.0)
        if group == 'Bathrooms':
            color = (.9, .9, .9, 1.0)
        create_component_dict = {
            'position': {'position': pos},
            'shape_renderer':{'size': store_size, 
            'position_from': 'position',
            'color_from': 'store_data'},
            'store_data': {'color': color,
                'store_name': name, 
                'logo_image': 'roulaslogo.png',
                'store_group': group,
                'darkened': False}}
        component_order = ['position', 'store_data', 'shape_renderer']
        return self.gameworld.init_entity(
            create_component_dict, component_order)

    def setup_states(self):
        self.gameworld.add_state(state_name='main', 
            systems_added=['shape_renderer', 'store_data'],
            systems_removed=[], systems_paused=[],
            systems_unpaused=['default_gameview', 'shape_renderer'],
            screenmanager_screen='main')

    def set_state(self):
        self.gameworld.state = 'main'


class KioskDirectoryApp(App):
    store_colors = DictProperty({'Vacant': (1.0, 1.0, 1.0, 1.0)})

    def build(self):
        self.store_colors = _group_colors
        return KioskView()


if __name__ == '__main__':
    KioskDirectoryApp().run()
