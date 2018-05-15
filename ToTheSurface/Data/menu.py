import bge
import text_tools
import common
import mathutils
import game
import os

ABOUT_TEXT = """\
The first adventure game I played was "advent.exe" otherwise known as "Colossal Cave Adventure". In it there were a few puzzles, and no combat to speak of. This game is my attempt to make a game in a similar vein: it's mostly about the exploration of the environment rather than actually achieving anything.
Due to the short timeframe of this game jam, the game world is smaller than I planned, but I hope you enjoy it anyway.
Music is "The Earth is Blue" by the artist Stellardrone.

                                        - sdfgeoff


"""

CONTROLS_TEXT = """\
                 Left Thruster: {}
                Right Thruster: {}
                Both Thrusters: {}
                   Extend Legs: {}

                  Open Logbook: {}
"""

GAME_NAME = "To The Surface"
def init(cont):
    if "MENU" not in cont.owner:
        cont.owner["MENU"] = Menu(cont.owner.scene)
    else:
        cont.owner["MENU"].update()

class Menu:
    def __init__(self, scene):
        game.Soundtrack()
        self.scene = scene
        for obj in scene.objects:
            if type(obj) == bge.types.KX_FontObject:
                text_tools.fix_text(obj)

        Button(self.scene.objects["StartButton"], "Start").on_click.append(self.start_game)
        Button(self.scene.objects["AboutButton"], "About").on_click.append(self._toggle_about)
        Button(self.scene.objects["ControlsButton"], "Controls").on_click.append(self._toggle_controls)
        Button(self.scene.objects["QuitButton"], "Quit").on_click.append(bge.logic.endGame)
        self.main_text = TextBox(self.scene.objects['AboutText'], "", 6.5)
        self.main_text.visible = False
        TextBox(self.scene.objects['Heading'], GAME_NAME, 6.5)

        self.mouse = Mouse(self.scene)


    def update(self):
        self.mouse.update()

    def _toggle_about(self):
        self.main_text.visible = True
        self.main_text.text = ABOUT_TEXT

    def _toggle_controls(self):
        self.main_text.visible = True
        self.main_text.text = CONTROLS_TEXT.format(
            bge.events.EventToString(game.LEFTKEY),
            bge.events.EventToString(game.RIGHTKEY),
            bge.events.EventToString(game.THRUSTKEY),
            bge.events.EventToString(game.LEGKEY),
            bge.events.EventToString(game.LOGBOOKKEY)
        )

    def start_game(self):
        bge.logic.startGame(os.path.join(common.BASE_PATH, 'game.blend'))


class Mouse:
    def __init__(self, scene):
        self.scene = scene
        bge.render.showMouse(True)

    def update(self):
        obj = self.get_mouse_over()
        if obj is not None and'BUTTON' in obj:
            if bge.logic.mouse.events[bge.events.LEFTMOUSE] == 1:
                obj['BUTTON'].on_click.fire()


    def get_mouse_over(self):
        pos = mathutils.Vector(bge.logic.mouse.position)

        pos -= mathutils.Vector([0.5, 0.5])
        pos.x *= self.scene.active_camera.ortho_scale
        height = bge.render.getWindowHeight()
        width = bge.render.getWindowWidth()
        pos.y *= -self.scene.active_camera.ortho_scale * height / width

        start_pos = mathutils.Vector([pos.x, 5, pos.y])
        end_pos = start_pos - mathutils.Vector([0, 1, 0])
        hit, _, __ = self.scene.active_camera.rayCast(end_pos, start_pos, 40)
        return hit



class Button:
    def __init__(self, obj, text):
        self.obj = obj
        self.text = text
        self.obj["BUTTON"] = self
        self.on_click = common.FunctionList()

    @property
    def text(self):
        return self.obj.children[0].text

    @text.setter
    def text(self, val):
        text_obj = self.obj.children[0]
        text_obj.text = val
        width = text_obj.dimensions.x
        text_obj.worldPosition.x = self.obj.worldPosition.x - width - 0.1


class TextBox:
    def __init__(self, obj, text, width):
        self.obj = obj
        self.width = width
        self.text = text

        self._orig_text = ""


    @property
    def text(self):
        return self._orig_text

    @text.setter
    def text(self, val):
        self._orig_text = val
        words = val.split(' ')
        self.obj.text = ''
        for word in words:
            old_text = self.obj.text
            self.obj.text += word + ' '
            if self.obj.dimensions.x > self.width:
                self.obj.text = old_text# + '\n' + word
                self.obj.text += '\n' + word + ' '

    @property
    def visible(self):
        return self.obj.visible

    @visible.setter
    def visible(self, val):
        self.obj.visible = val
