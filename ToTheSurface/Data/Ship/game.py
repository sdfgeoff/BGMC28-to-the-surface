import bge
import ship
import hud

def init(cont):
	if 'GAME' not in cont.owner:
		cont.owner['GAME'] = Game(cont.owner)
	else:
		cont.owner['GAME'].update()
	
	
class Game():
	def __init__(self, ship_obj):
		self.scene = ship_obj.scene
		self.ship = ship.Ship(ship_obj)
		self.hud = None
		
		self.loaded = False
		
	def update(self):
		if self.loaded == False:
			hud_scene = [s for s in bge.logic.getSceneList() if s.name == 'HUD']
			if hud_scene:
				self.hud = hud.HUD(hud_scene[0])
				self.loaded = True
				
				self.ship.on_ship_move.append(self._update_hud_radio_box)
				self.hud.major_text.text = "The Underground City"
				
				
		self._update_user_input()
		self.ship.update()
		self.hud.update()
		
		
		
	def _update_user_input(self):
		if bge.logic.keyboard.events[bge.events.EKEY] == 1:
			self.ship.legs_deployed = not self.ship.legs_deployed

		thrust = float(bge.events.UPARROWKEY in bge.logic.keyboard.active_events)
		steer = 0
		steer -= bge.events.LEFTARROWKEY in bge.logic.keyboard.active_events
		steer += bge.events.RIGHTARROWKEY in bge.logic.keyboard.active_events
		self.ship.fly(thrust, steer)
		
		if bge.logic.keyboard.events[bge.events.SPACEKEY] == 1:
			self.hud.step_text()
		
	def _update_hud_radio_box(self, ship_position):
		"""Moves the end of the radio box to the ships position"""
		screen_pos = self.scene.active_camera.getScreenPosition(
			self.ship.rootobj.childrenRecursive['AntennaTip']
		)
		self.hud.radio_box_right.set_pointer_position(screen_pos)
		
