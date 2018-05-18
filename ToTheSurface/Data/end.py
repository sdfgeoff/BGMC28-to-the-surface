import menu
import game
import bge
import text_tools
import random

END_TEXT = """\
You made it to the surface! and found {} out of {} locations.
{}



Thanks for playing my game! I hope you enjoyed it.
                                - sdfgeoff
"""
NEXT_TIME_TEXT = """Next time try find: {}"""

def init(cont):
    if 'END' not in cont.owner:
        cont.owner['END'] = End(cont.owner.scene)
    else:
        cont.owner['END'].update()


class End:
    def __init__(self, scene):
        self.scene = scene
        self.mouse = menu.Mouse(self.scene)
        game.Soundtrack()


        found = bge.logic.globalDict['found']
        all_locs = bge.logic.globalDict['all']
        if len(found) == len(all_locs):
            additional = ""
        else:
            random.shuffle(all_locs)
            additional = NEXT_TIME_TEXT.format(
                next(p for p in all_locs if p not in found)
            )

        menu.TextBox(scene.objects["EndText"], END_TEXT.format(
            len(found),
            len(all_locs),
            additional
        ), 11)
        menu.Button(scene.objects["MenuButton"], "Menu").on_click.append(self._menu)
        menu.Button(scene.objects["QuitButton"], "Quit").on_click.append(self._quit)

    def _quit(self):
        bge.logic.endGame()

    def _menu(self):
        bge.logic.startGame('menu.blend')

    def update(self):
        self.mouse.update()


