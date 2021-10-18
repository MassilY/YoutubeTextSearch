from kivy.lang import Builder
from kivy.properties import StringProperty
from kivymd.uix.behaviors import FakeRectangularElevationBehavior
from kivymd.uix.card import MDCardSwipe, MDCard

Builder.load_file("Widgets/swipeToDeleteItem.kv")


class SwipeToDeleteItem(MDCard, FakeRectangularElevationBehavior):
    text = StringProperty()

    def __init__(self, **kw):
        super(SwipeToDeleteItem, self).__init__(**kw)


