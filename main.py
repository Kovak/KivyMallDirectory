import kivy
import cymunk
from kivent import GameSystem, GameWorld
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import (StringProperty, ListProperty, NumericProperty, 
    ObjectProperty, BooleanProperty)
from kivy.uix.stacklayout import StackLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.base import EventLoop
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from kivy.uix.widget import Widget
from stores import stores, categories
from kivy.uix.togglebutton import ToggleButton
from kivy.animation import Animation
from kivy.storage.jsonstore import JsonStore
from datetime import datetime, timedelta
store_sentences = JsonStore('store_data.json')

_group_colors = {}
_group_colors['Movies'] = (1.0, 1.0, 1.0, 1.0)
_group_colors['Clothes'] = (1.0, 1.0, 1.0, 1.0)
_group_colors['Food'] = (1.0, 1.0, 1.0, 1.0)
_group_colors['Home'] = (1.0, 1.0, 1.0, 1.0)
_group_colors['Beauty/Health'] = (1.0, 1.0, 1.0, 1.0)
_group_colors['Gifts'] = (1.0, 1.0, 1.0, 1.0)
_group_colors['Electronics'] = (1.0, 1.0, 1.0, 1.0)
_group_colors['Bathrooms'] = (0.0, 0.0, 1.0, 1.0)
_group_colors['Shoes'] = (1.0, 1.0, 1.0, 1.0)
_group_colors['Jewelry'] = (1.0, 1.0, 1.0, 1.0)
_group_colors['Accessories'] = (1.0, 1.0, 1.0, 1.0)
_group_colors['Vacant'] = (1.0, 1.0, 1.0, 1.0)

# _group_colors['Movies'] = (0.941176471, 0.68627451, 0.0, 1.0)
# _group_colors['Clothes'] = (0.611764706, 1.0, 0.690196078, 1.0)
# _group_colors['Food'] = (0.71372549, 0.168627451, 0.0, 1.0)
# _group_colors['Home'] = (0.839215686, 0.988235294, 0.02745098, 1.0)
# _group_colors['Beauty/Health'] = (0.670588235, 0.243137255, 1.0, 1.0)
# _group_colors['Gifts'] = (0.298039216, 0.490196078, 1.0, 1.0)
# _group_colors['Electronics'] = (0.0, 0.823529412, 0.698039216, 1.0)
# _group_colors['Bathrooms'] = (0.0, 0.0, 1.0, 1.0)
# _group_colors['Shoes'] = (1.0, 0.450980392, 0.0, 1.0)
# _group_colors['Jewelry'] = (1.0, 0.066666667, 0.815686275, 1.0)
# _group_colors['Accessories'] = (0.0, 0.780392157, 0.192156863, 1.0)
# _group_colors['Vacant'] = (0., 0., 0., 1.0)


class StoreData(GameSystem):
    focused_entity = NumericProperty(None, allownone=True)
    previous_value = NumericProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super(StoreData, self).__init__(**kwargs)
        self.groups_highlighted = set()

    def on_focused_entity(self, instance, value):
        previous_value = self.previous_value
        if previous_value is not None:
            self.clear_entity_color(previous_value)
        if value is not None:
            self.highlight_entity(value)
        self.previous_value = value

    def clear_entity_color(self, entity_id):
        entities = self.gameworld.entities
        entity = entities[entity_id]
        color_data = entity.color
        store_data = entity.store_data
        group = store_data.store_group

        if group == 'Bathrooms':
            r, g, b, a = _group_colors['Bathrooms']
            color_data.r = r
            color_data.g = g
            color_data.b = b
            color_data.a = a
        else:
            color_data.r = 0.
            color_data.g = 0.
            color_data.b = .1
            color_data.a = 1.

        if hasattr(store_data, 'linked'):
            for each in store_data.linked:
                other_ent = entities[each]
                color_data = other_ent.color
                color_data.r = 0.
                color_data.g = 0.
                color_data.b = .1
                color_data.a = 1.

    def highlight_entity(self, entity_id):
        entities = self.gameworld.entities
        entity = entities[entity_id]
        color_data = entity.color
        store_data = entity.store_data
        group = store_data.store_group
        r, g, b, a = _group_colors[group]
        color_data.r = r
        color_data.g = g
        color_data.b = b
        color_data.a = a
        if hasattr(store_data, 'linked'):
            for each in store_data.linked:
                other_ent = entities[each]
                color_data = other_ent.color
                color_data.r = r
                color_data.g = g
                color_data.b = b
                color_data.a = a

    def clear_all_entities_color(self):
        entities = self.gameworld.entities
        for entity_id in self.entity_ids:
            entity = entities[entity_id]
            store_data = entity.store_data
            group = store_data.store_group
            color_data = entity.color
            if group == 'Bathrooms':
                r, g, b, a = _group_colors['Bathrooms']
                color_data.r = r
                color_data.g = g
                color_data.b = b
                color_data.a = a
            else:
                color_data.r = 0.
                color_data.g = 0.
                color_data.b = .1
                color_data.a = 1.
        
class KioskView(Widget):
    info_popup = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(KioskView, self).__init__(**kwargs)
        self.time_since_last_interact = 0.0
        Clock.schedule_once(self.init_game, 30.0)

    def update(self, dt):
        self.gameworld.update(dt)

    def init_game(self, dt):
        self.setup_group_colors()
        self.setup_store_shapes()
        self.setup_stores()
        self.setup_states()
        #self.setup_carousel()
        gameworld = self.gameworld
        gameworld.currentmap = gameworld.systems['map']
        Clock.schedule_once(self.setup_2)
        Clock.schedule_interval(self.update, 1./60.)

    def setup_2(self, dt):
        self.draw_stores()
        self.set_state()

        #self.gameworld.systems['store_data'].focused_entity = 25


    def setup_group_colors(self):
        self.group_colors = _group_colors

    def setup_store_shapes(self):
        self.store_shapes = store_shapes = {}
        store_shapes['0'] = {'size': (42, 600)}
        store_shapes['1'] = {'size': (300, 264)}
        store_shapes['2'] = {'size': (112, 544)}
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
            'name': 'Larry H. Miller Megaplex', 'group': 'Movies',
            'picture_name': 'larryhmillermegaplex'}
        stores['Macys'] = {'shape': '2', 'pos': (961, 674),
            'name': "Macy's", 'group': 'Clothes', 'picture_name': 'macys'}
        stores['JCPenney'] = {'shape': '2', 'pos': (64, 674), 
            'name': 'J.C. Penney', 'group': 'Clothes', 'picture_name': 'jcpenney'}
        stores['RedRobin'] = {'shape': '6', 'pos': (827, 411), 
            'name': 'Red Robin', 'group': 'Food', 'picture_name': 'redrobin'}
        stores['ROSS'] = {'shape': '30', 'pos': (674, 399), 
            'name': 'ROSS', 'group': 'Clothes', 'picture_name': 'ross'}
        stores['Movies9A'] = {'shape': '7A', 'pos': (819, 887),
            'name': 'Movies 9', 'group': 'Movies', 'picture_name': 'movies9'}
        stores['Movies9B'] = {'shape': '7B', 'pos': (840, 797),
            'name': 'Movies 9', 'group': 'Movies', 'picture_name': 'movies9'}
        stores['BedBathBeyond'] = {'shape': '4', 'pos': (265, 394),
            'name': 'Bed Bath and Beyond', 'group': 'Home', 
            'picture_name': 'bedbathbeyond'}
        stores['Ulta'] = {'shape': '3', 'pos': (158, 426),
            'name': 'Ulta', 'group': 'Beauty/Health', 'picture_name': 'ulta'}
        stores['Hammond'] = {'shape': '9', 'pos': (890, 705),
            'name': 'Hammond', 'group': 'Gifts', 'picture_name': 'hammond'}
        stores['LACuts'] = {'shape': '9', 'pos': (870, 705),
            'name': 'L.A. Cuts', 'group': 'Beauty/Health'}
        stores['WestValleyMusic'] = {'shape': '9', 'pos': (850, 705),
            'name': 'West Valley Music', 'group': 'Gifts'}
        stores['ZAGG'] = {'shape': '9', 'pos': (830, 705),
            'name': 'ZAGG', 'group': 'Electronics', 'picture_name': 'zagg'}
        stores['Vacant1'] = {'shape': '9', 'pos': (810, 705),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['UrbanExpress'] = {'shape': '9', 'pos': (790, 705),
            'name': 'Urban Express', 'group': 'Clothes'}
        stores['OrangeJulius'] = {'shape': '10', 'pos': (765, 682),
            'name': 'Orange Julius', 'group': 'Food', 
            'picture_name': 'orange-julius'}
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
            'name': "Subway", 'group': 'Food',
            'picture_name': 'subway'}
        stores['HotDogStick'] = {'shape': '10', 'pos': (716, 658),
            'name': "Hot Dog on a Stick", 'group': 'Food', 
            'picture_name': 'hotdogstick'}
        stores['Vacant20'] = {'shape': '14', 'pos': (688, 705),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant19'] = {'shape': '14', 'pos': (661, 705),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant18'] = {'shape': '14', 'pos': (634, 705),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant7'] = {'shape': '16', 'pos': (608, 714),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Maurices'] = {'shape': '16', 'pos': (583, 714),
            'name': "Maurice's", 'group': 'Clothes',
            'picture_name': 'maurices'}
        stores['Bath and Body Works'] = {'shape': '16', 'pos': (558, 714),
            'name': 'Bath and Body Works', 'group': 'Home',
            'picture_name': 'bathbodyworks'}
        stores['Vacant8'] = {'shape': '17', 'pos': (533, 684),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant9'] = {'shape': '18', 'pos': (458, 698),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Journeys'] = {'shape': '16', 'pos': (432, 715),
            'name': "Journey's", 'group': 'Clothes',
            'picture_name': 'journeys'}
        stores['FootActionUSA'] = {'shape': '16', 'pos': (406, 715),
            'name': 'FootAction USA', 'group': 'Shoes',
            'picture_name': 'footactionusa'}
        stores['ValentinesDayGifts'] = {'shape': '16', 'pos': (380, 715),
            'name': "Valentine's Day Gifts", 'group': 'Gifts'}
        stores['ModaBella'] = {'shape': '19', 'pos': (356, 706),
            'name': 'Moda Bella', 'group': 'Clothes',
            'picture_name': 'modabella'}
        stores['BoostMobile'] = {'shape': '19', 'pos': (336, 706),
            'name': 'Boost Mobile', 'group': 'Electronics',
            'picture_name': 'boostmobile'}
        stores['GNC'] = {'shape': '19', 'pos': (316, 706),
            'name': 'GNC', 'group': 'Beauty/Health',
            'picture_name': 'gnc'}
        stores['TheNerdStore'] = {'shape': '19', 'pos': (296, 706),
            'name': 'The Nerd Store', 'group': 'Gifts',
            'picture_name': 'nerdstore'}
        stores['RadioShack'] = {'shape': '19', 'pos': (276, 706),
            'name': 'RadioShack', 'group': 'Electronics',
            'picture_name': 'radioshack'}
        stores['Vacant10'] = {'shape': '19', 'pos': (256, 706),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['XZone'] = {'shape': '19', 'pos': (236, 706),
            'name': 'X-Zone', 'group': 'Clothes'}
        stores['Wind&Waters'] = {'shape': '19', 'pos': (216, 706),
            'name': 'Wind & Waters', 'group': 'Gifts'}
        stores['Trinkets&Treasures'] = {'shape': '19', 'pos': (196, 706),
            'name': 'Trinkets and Treasures', 'group': 'Gifts'}
        stores['FadsNFashions'] = {'shape': '19', 'pos': (176, 706),
            'name': "Fads N' Fashions", 'group': 'Clothes',
            'picture_name': 'fadsnfashions'}
        stores['TheBazzar'] = {'shape': '19', 'pos': (156, 706),
            'name': 'The Bazzar', 'group': 'Gifts'}
        stores['RyansCustomJewelry'] = {'shape': '19', 'pos': (136, 706),
            'name': "Ryan's Custom Jewelry", 'group': 'Jewelry'}
        stores['Vacant11'] = {'shape': '20', 'pos': (135, 538),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['Vacant12'] = {'shape': '21', 'pos': (153, 551),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['MDPhotography'] = {'shape': '21', 'pos': (168, 551),
            'name': 'MD Photography', 'group': 'Gifts',
            'picture_name': 'md-photography'}
        stores['Vacant13'] = {'shape': '21', 'pos': (183, 551),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['JolenesGirlsDresses'] = {'shape': '22', 'pos': (217, 551),
            'name': "Jolene's Girl's Dresses", 'group': 'Clothes',
            'picture_name': 'jolenes'}
        stores['Zumeiz'] = {'shape': '22', 'pos': (242, 551),
            'name': 'Zumeiz', 'group': 'Clothes',
            'picture_name': 'zumeiz'}
        stores['Vacant14'] = {'shape': '22', 'pos': (267, 551),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['GameGridArcade'] = {'shape': '22', 'pos': (292, 551),
            'name': 'Game Grid Arcade', 'group': 'Electronics',
            'picture_name': 'gamegrid'}
        stores['PaylessShoeSource'] = {'shape': '23', 'pos': (315, 551),
            'name': 'Payless Shoe Source', 'group': 'Shoes',
            'picture_name': 'payless'}
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
            'name': 'Pretzel Maker', 'group': 'Food',
            'picture_name': 'pretzel'}
        stores['PretzelMaker2'] = {'shape': '29', 'pos': (447, 546),
            'name': 'Pretzel Maker', 'group': 'Food',
            'picture_name': 'pretzelmaker'}
        stores['SchubachJewelers'] = {'shape': '29', 'pos': (462, 546),
            'name': 'Schubach Jewelers', 'group': 'Jewelry',
            'picture_name': 'schubach'}
        stores['FamousFootwear'] = {'shape': '5', 'pos': (562, 365),
            'name': 'Famous Footwear', 'group': 'Shoes',
            'picture_name': 'famousfootwear'}
        stores['PopcornCottage'] = {'shape': '31', 'pos': (562, 445),
            'name': 'Popcorn Cottage', 'group': 'Food',
            'picture_name': 'popcorncottage'}
        stores['X-BrandsCustom'] = {'shape': '31', 'pos': (562, 473),
            'name': 'X-Brands Custom T-Shirts', 'group': 'Food',
            'picture_name': 'xbrand'}
        stores['BrowSpa24'] = {'shape': '31', 'pos': (562, 501),
            'name': 'Brow Spa 24', 'group': 'Beauty/Health',
            'picture_name': 'browspa'}
        stores['Rave'] = {'shape': '32', 'pos': (591, 546),
            'name': 'Rave', 'group': 'Clothes',
            'picture_name': 'rave'}
        stores['Claires'] = {'shape': '32', 'pos': (565, 546),
            'name': "Claire's", 'group': 'Accessories',
            'picture_name': 'claires'}
        stores['MorganJewelers'] = {'shape': '33', 'pos': (536, 557),
            'name': 'Morgan Jewelers', 'group': 'Jewelry',
            'picture_name': 'morganjewelers'}
        stores['TieOneOn'] = {'shape': '34', 'pos': (536, 526),
            'name': 'Tie One On', 'group': 'Accessories',
            'picture_name': 'tieoneon'}
        stores['2Love'] = {'shape': '35', 'pos': (616, 551),
            'name': '2 Love', 'group': 'Clothes'}
        stores['Fragranza'] = {'shape': '35', 'pos': (635, 551),
            'name': 'Fragranza', 'group': 'Beauty/Health',
            'picture_name': 'fragranza'}
        stores['CellAgain'] = {'shape': '35', 'pos': (654, 551),
            'name': 'Cell Again', 'group': 'Electronics',
            'picture_name': 'cellagain'}
        stores['ShoeOutlet'] = {'shape': '35', 'pos': (673, 551),
            'name': 'Shoe Outlet', 'group': 'Shoes'}
        stores['Fanzz'] = {'shape': '35', 'pos': (692, 551),
            'name': 'Fanzz', 'group': 'Clothes',
            'picture_name': 'fanzz'}
        stores['DiamondWireless'] = {'shape': '35', 'pos': (711, 551),
            'name': 'Diamond Wireless', 'group': 'Electronics',
            'picture_name': 'diamondwireless'}
        stores['TMobile'] = {'shape': '36', 'pos': (731, 551),
            'name': 'T-Mobile', 'group': 'Electronics',
            'picture_name': 'tmobile'}
        stores['Vacant21'] = {'shape': '37', 'pos': (888, 508),
            'name': 'Vacant', 'group': 'Vacant'}
        stores['TheAccessoryShop'] = {'shape': '38', 'pos': (866, 515),
            'name': 'The Accessory Shop', 'group': 'Accessories'}
        stores['NikkisBridal'] = {'shape': '38', 'pos': (850, 515),
            'name': "Nikki's Bridal", 'group': 'Clothes',
            'picture_name': 'nikkisbridal'}
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
            if 'picture_name' in store:
                picture_info = store['picture_name']
            else:
                picture_info = None
            ent_id = self.draw_store(size, pos, name, group,
                picture_info)
            store['ent_id'] = ent_id
            if key == 'Movies9A':
                movies9a = ent_id
            elif key == 'Movies9B':
                movies9b = ent_id
        entities = self.gameworld.entities
        ent_9a = entities[movies9a]
        ent_9b = entities[movies9b]
        ent_9a.store_data.linked = [movies9b]
        ent_9b.store_data.linked = [movies9a]
        ent_9a.store_data.master = True
        ent_9b.store_data.master = False

    def draw_store(self, size, pos, name, group, picture_info):
        store_size = size
        color = (0.00, 0.00, .1, 1.0)
        if group == 'Bathrooms':
            color = _group_colors['Bathrooms']
        create_component_dict = {
            'position': pos,
            'shape_renderer':{'size': store_size},
            'color': color,
            'store_data': {'color': color,
                'store_name': name, 
                'logo_image': 'roulaslogo.png',
                'store_group': group,
                'picture_info': picture_info,
                'darkened': False}}
        component_order = ['position', 'color', 'store_data', 'shape_renderer']
        return self.gameworld.init_entity(
            create_component_dict, component_order)

    def setup_states(self):
        self.gameworld.add_state(state_name='stores', 
            systems_added=['shape_renderer', 'store_data'],
            systems_removed=[], systems_paused=[],
            systems_unpaused=['default_gameview', 'shape_renderer'],
            screenmanager_screen=None)
        self.gameworld.add_state(state_name='main',
            systems_added=[],
            systems_removed=['shape_renderer'],
            systems_paused=[],
            systems_unpaused=['default_gameview', 'shape_renderer'],
            screenmanager_screen=None,
            )

    def set_state(self):
        self.gameworld.state = 'main'

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        Clock.schedule_interval(self.advance_carousel, 15.0)

    def advance_carousel(self, dt):
        self.carousel.load_next(mode='next')

class CategoryButton(ButtonBehavior, StackLayout):
    image_name = StringProperty('')
    category_name = StringProperty('')

class StoreLogoButton(ButtonBehavior, BoxLayout):
    store_name = StringProperty('')
    logo = StringProperty('')
    store_key = StringProperty('')

class SubCategoryButton(ToggleButton):
    category = StringProperty('')
    subcategory = StringProperty('')


class StoreScreen(Screen):
    current_key = StringProperty('')


class MapPopup(Widget):
    pass

class CategoryScreen(Screen):
    category = StringProperty('')
    subcategories = ListProperty([])
    current_selected = ListProperty([])

    def on_category(self, instance, value):
        app = self.app
        subcategories = app.subcategories
        self.subcategories = subcategories[value]
        #fix me, find better way to retrigger
        self.current_selected = [1, 2, 3]
        self.current_selected = []

    def get_title(self, category):
        if category == 'healthandbeauty':
            return 'Health and Beauty'
        else:
            return category.title()

    def calculate_sizing(self, instance, children):
        h = instance.height
        num_children = len(children)
        spacing = instance.spacing
        total_size_required = num_children * (100+spacing[0])
        if total_size_required > h:
            desired_size = h - (num_children * spacing[0])
            new_default = desired_size/num_children
            instance.row_default_height = new_default
        else:
            instance.row_default_height = 100

    def on_subcategories(self, instance, value):
        layout = self.ids.button_layout
        layout.clear_widgets()
        category = self.category
        for each in value:
            layout.add_widget(SubCategoryButton(
                text=categories[each], category=category,
                subcategory=each,
                on_release=self.toggle_subcategory))

    def toggle_subcategory(self, button):
        if button.state == 'down':
            subcategory = button.subcategory
            self.current_selected = [subcategory]
        else:
            self.current_selected = []

    def on_current_selected(self, instance, value):
        app = self.app
        layout = self.ids.logo_layout
        layout.clear_widgets()
        category = self.category
        stores = app.stores
        if value == []:
            get_stores = app.get_stores_in_category(category)
        elif value is not None:
            get_stores = app.get_stores_subcategories(value)
        else:
            get_stores = []
        for store in get_stores:
            store_dict = stores[store]
            layout.add_widget(StoreLogoButton(
                store_name=store_dict['store_name'],
                store_key=store))


class VFMallKiosk(FloatLayout):
    camera_x = NumericProperty(0)
    do_message = BooleanProperty(False)
    message_popup = ObjectProperty(None)
    last_touch_time = ObjectProperty(None)
    time_to_reset = NumericProperty(1)

    def __init__(self, **kwargs):
        super(VFMallKiosk, self).__init__(**kwargs)
        self.message_popup = MapPopup(pos=(1100, 400), size=(500, 200), 
            size_hint=(None, None))
        Clock.schedule_interval(self.reset, 30.0)


    def on_do_message(self, instance, value):
        message_popup = self.message_popup
        children = self.children
        if value:
            if message_popup not in children:
                self.add_widget(message_popup)
        else:
            if message_popup in children:
                self.remove_widget(message_popup)
    
    def open_category(self, category):
        self.screen_manager.current = 'category'
        self.category_screen.category = category
        self.do_message = False

    def on_touch_down(self, touch):
        super(VFMallKiosk, self).on_touch_down(touch)
        self.last_touch_time = self.get_time()

    def get_time(self):
        return datetime.utcnow()

    def reset(self, dt):
        last_touch_time = self.last_touch_time
        current_time = self.get_time()
        time_to_reset = timedelta(minutes=self.time_to_reset)
        if last_touch_time is not None:
            if last_touch_time + time_to_reset < current_time:
                self.screen_manager.current = 'main'

    def go_back(self):
        current = self.screen_manager.current_screen
        self.do_message = False
        if self.screen_manager.current == 'store':
            anim = Animation(camera_x=-1080, duration = .5)
            anim.start(self)
        if current.previous is not None:
            self.screen_manager.current = current.previous

    def open_store(self, selected_store):
        store_screen = self.store_screen
        text_label = store_screen.ids.text_label
        text_label.text = store_sentences['store_data'][selected_store]
        kioskmap = store_screen.kioskmap
        store_screen.current_key = selected_store
        x_distance = 1080
        self.camera_x = 845+x_distance
        anim = Animation(camera_x=845, duration = .5)
        anim.start(self)
        self.screen_manager.current = 'store'
        gameworld = kioskmap.gameworld
        gameworld.state = 'stores'
        store_system = gameworld.systems['store_data']
        try:
            correct_entity_id = kioskmap.stores[
                stores[selected_store]['mapkey']]['ent_id']
            self.do_message = False
        except:
            correct_entity_id = None
            self.do_message = True
        store_system.focused_entity = correct_entity_id

    def on_camera_x(self, instance, value):
        kioskmap = self.store_screen.kioskmap
        camera_system = kioskmap.ids.camera
        camera_system.camera_pos = (value, -100)


class VFMallKioskApp(App):


    def build(self):
        EventLoop.window.bind(on_keyboard=self.hook_keyboard)
        self.stores = stores
        self.calculate_stores()

    def hook_keyboard(self, window, key, *largs):
        if key == 27:
            self.root.go_back()
            return True

    def get_stores_in_category(self, category):
        stores = self.stores
        stores_to_return = []
        store_append = stores_to_return.append
        for store in stores:
            store_dict = stores[store]
            s_category = store_dict['store_category']
            if s_category == category:
                store_append(store)
        return stores_to_return

    def get_stores_subcategories(self, subcategories_list):
        stores = self.stores
        stores_to_return = []
        store_append = stores_to_return.append
        subset_isect = set(subcategories_list).intersection
        for store in stores:
            store_dict = stores[store]
            subcategories = store_dict['sub_categories']
            intersect = subset_isect(set(subcategories))
            if len(intersect) > 0:
                store_append(store)
        return stores_to_return

    def calculate_stores(self):
        stores = self.stores
        self.categories = categories = []
        self.subcategories = subcategories = {}
        for store in stores:
            store_dict = stores[store]
            cat = store_dict['store_category']
            sub_cats = store_dict['sub_categories']
            if cat not in categories:
                categories.append(cat)
                subcategories[cat] = []
            for sub in sub_cats:
                if sub not in subcategories[cat]:
                    subcategories[cat].append(sub)



if __name__ == '__main__':
    VFMallKioskApp().run()