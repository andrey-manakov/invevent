from . import start_menu, events_menu, settings_menu, friends_menu


def register_menu(bot):
    start_menu.register(bot)
    events_menu.register(bot)
    friends_menu.register(bot)
    settings_menu.register(bot)
