import kivy
from kivy.core.window import Window
from kivy.modules import inspector

kivy.require("2.0.0")

from kivy.lang import Builder
from kivymd.app import MDApp

from Widgets.SwipeToDeleteItem import SwipeToDeleteItem


class YoutubeTextSearchApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.screen = Builder.load_file('YoutubeTextSearch.kv')
        inspector.create_inspector(Window, self.screen)

    def build(self):
        return self.screen

    def remove_item(self, instance):
        self.screen.ids.md_list.remove_widget(instance)

    def on_start(self):
        for i in range(20):
            self.screen.ids.md_list.add_widget(
                SwipeToDeleteItem(text=f"One-line item {i}")
            )


YoutubeTextSearchApp().run()
