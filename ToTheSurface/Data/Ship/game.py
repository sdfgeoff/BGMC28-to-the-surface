import bge
import ship
import hud

LEGKEY = bge.events.EKEY
THRUSTKEY = bge.events.UPARROWKEY
LEFTKEY = bge.events.LEFTARROWKEY
RIGHTKEY = bge.events.RIGHTARROWKEY

SKIPTEXTKEY = bge.events.SPACEKEY

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
		
		self._fallen_message = False
		
		self.areas = {o['AREA']:o for o in self.scene.objects if 'AREA' in o}
		self.been_areas = []
		
	def update(self):
		if self.loaded == False:
			if self.load():
				self.loaded = True
			else:
				return
				
				
		self._update_user_input()
		if not self._fallen_message:
			self._check_ship_upsidedown()
		self.ship.update()
		self.hud.update()
		
		
	def load(self):
		hud_scene = [s for s in bge.logic.getSceneList() if s.name == 'HUD']
		if hud_scene:
			self.hud = hud.HUD(hud_scene[0])
			
			self.ship.on_ship_move.append(self._update_hud_radio_box)
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
		
	def _update_hud_radio_box(self, ship_position):
		"""Moves the end of the radio box to the ships position"""
		screen_pos = self.scene.active_camera.getScreenPosition(
			self.ship.rootobj.childrenRecursive['AntennaTip']
		)
		self.hud.radio_box_right.set_pointer_position(screen_pos)
		
		for area in self.areas:
			if area not in self.been_areas:
				area_obj = self.areas[area]
				dist = (ship_position - area_obj.worldPosition).xz.length
				if dist < area_obj.localScale.x: #assume round
					if self.hud.major_text.closing:
						self.hud.major_text.text = area
						self.been_areas.append(area)
		
