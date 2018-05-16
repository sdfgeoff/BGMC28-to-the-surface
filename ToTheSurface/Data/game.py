import bge
import ship
import hud
import os
import math
import aud
import common
import time

LEGKEY = bge.events.EKEY
THRUSTKEY = bge.events.UPARROWKEY
LEFTKEY = bge.events.LEFTARROWKEY
RIGHTKEY = bge.events.RIGHTARROWKEY

SKIPTEXTKEY = bge.events.SPACEKEY
LOGBOOKKEY = bge.events.LKEY


def init(cont):
    if 'GAME' not in cont.owner:
        cont.owner['GAME'] = Game(cont.owner)
    else:
        cont.owner['GAME'].update()


class Game():
    def __init__(self, ship_obj):
        self.track = Soundtrack()
        self.scene = ship_obj.scene
        self.ship = ship.Ship(ship_obj)
        self.hud = None


        if not os.path.exists(hud.SCREENSHOT_PATH):
            os.mkdir(hud.SCREENSHOT_PATH)

        for file_name in os.listdir(hud.SCREENSHOT_PATH):
            os.remove(os.path.join(hud.SCREENSHOT_PATH, file_name))

        self.loaded = False

        self._fallen_message = False
        self._logbook_message = False

        self.areas = {o['AREA']:o for o in self.scene.objects if 'AREA' in o}
        self.messages = {o['MESSAGE']:o for o in self.scene.objects if 'MESSAGE' in o}
        self.been_areas = []
        self.heard_messages = []

    def update(self):
        if self.loaded == False:
            if self.load():
                self.loaded = True
            else:
                return


        self._update_user_input()
        if not self._fallen_message:
            self._check_ship_upsidedown()

        if not self.hud.log_book.visible:
            self.ship.update()

        muffled = self.hud.log_book.visible or self.ship.is_underwater
        self.track.muffle(muffled)
        self.hud.radio_box_right.sound.set_muffle(muffled)
        self.hud.radio_box_left.sound.set_muffle(muffled)
        self.hud.update()


    def load(self):
        hud_scene = [s for s in bge.logic.getSceneList() if s.name == 'HUD']
        if hud_scene:
            self.hud = hud.HUD(hud_scene[0])
            self.hud.log_book.set_location_list(self.areas)
            self.hud.log_book.set_found_location_list(self.been_areas)

            self.hud.log_book.close_text.text = "Close the logbook with the {}".format(bge.events.EventToString(LOGBOOKKEY))

            self.ship.on_ship_move.append(self._update_hud_radio_box)
            self.ship.on_ship_move.append(self._check_areas)
            return True

        return False
            #self.hud.major_text.text = "The Underground City"

    def _check_ship_upsidedown(self):
        if abs(self.ship.orientation) > 1.5 and self.ship.speed < 0.2:
            # Fallen over - probably
            if self.hud.radio_box_right.closing:
                self.hud.radio_box_right.text = "Captain, it looks like we've fallen over. Try retracting and extending the landing legs by pressing the {}".format(bge.events.EventToString(LEGKEY))
                self._fallen_message = True


    def _update_user_input(self):
        if bge.logic.keyboard.events[LEGKEY] == 1:
            self.ship.legs_deployed = not self.ship.legs_deployed

        thrust = float(THRUSTKEY in bge.logic.keyboard.active_events)
        steer = 0
        steer -= LEFTKEY in bge.logic.keyboard.active_events
        steer += RIGHTKEY in bge.logic.keyboard.active_events
        self.ship.fly(thrust, steer)

        if bge.logic.keyboard.events[SKIPTEXTKEY] == 1:
            self.hud.step_text()

        if bge.logic.keyboard.events[LOGBOOKKEY] == 1:
            self.hud.log_book.page = math.ceil(len(self.been_areas) / 2) - 1
            self.hud.log_book.visible = not self.hud.log_book.visible

            if self.hud.log_book.visible:
                self.ship.pause()
                self.hud.log_icon_glow = False
                self.hud.radio_box_left.close()
            else:
                self.ship.resume()

        if self.hud.log_book.visible:
            if bge.logic.keyboard.events[LEFTKEY] == 1:
                self.hud.log_book.page -= 1
            elif bge.logic.keyboard.events[RIGHTKEY] == 1:
                self.hud.log_book.page += 1


    def _update_hud_radio_box(self, ship_position):
        """Moves the end of the radio box to the ships position"""
        screen_pos = self.scene.active_camera.getScreenPosition(
            self.ship.rootobj.childrenRecursive['AntennaTip']
        )
        self.hud.radio_box_right.set_pointer_position(screen_pos)


    def _check_areas(self, ship_position):
        for area in self.areas:
            if area not in self.been_areas:
                area_obj = self.areas[area]
                dist = (ship_position - area_obj.worldPosition).xz.length
                if dist < area_obj.localScale.x: #assume round
                    if self.hud.major_text.closing:
                        self.hud.major_text.text = area
                        self.been_areas.append(area)
                        bge.render.makeScreenshot(os.path.join(hud.SCREENSHOT_PATH, area + '.png'))

                        self.hud.log_icon_glow = True

                        if not self._logbook_message:
                            self.hud.radio_box_left.set_pointer_position(
                                (-0.015, -0.005)
                            )
                            self.hud.radio_box_left.text = "Open the logbook with the {}".format(bge.events.EventToString(LOGBOOKKEY))
                            self._logbook_message = True

        for message in self.messages:
            if message not in self.heard_messages:
                message_obj = self.messages[message]
                dist = (ship_position - message_obj.worldPosition).xz.length
                if dist < message_obj.localScale.x: #assume round
                    if self.hud.radio_box_right.closing:
                        self.hud.radio_box_right.text = message
                        self.heard_messages.append(message)



class Soundtrack:
    DEVICE = aud.device()
    def __init__(self):
        raw = aud.Factory(common.BASE_PATH + "/Stellardrone - The Earth Is Blue.ogg")
        normal = raw.loop(-1)
        muffled = raw.lowpass(440, 2).highpass(220, 1.5).loop(-1)
        # play the audio, this return a handle to control play/pause
        self.handle1 = self.DEVICE.play(normal)
        self.handle2 = self.DEVICE.play(muffled)

        if "start_time" not in bge.logic.globalDict:
            bge.logic.globalDict["start_time"] = time.time()
            elapsed = 0
        else:
            elapsed = time.time() - bge.logic.globalDict["start_time"]
        self.handle1.position = elapsed
        self.handle2.position = elapsed
        self.handle1.volume = 0.5
        self.handle2.volume = 0.0

    def muffle(self, val):
        if val:
            self.handle2.volume = 0.5
            self.handle1.volume = 0.0
        else:
            self.handle2.volume = 0.0
            self.handle1.volume = 0.5

