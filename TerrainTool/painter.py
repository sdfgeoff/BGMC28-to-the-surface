import bge
import mathutils
import math
import cProfile
import os
import config
import time


levelname = 'level'


NAME_TO_PARAM = {
	"GrowthDial": "growth",
	"RockDial": "rock",
	"WaterDial": "water",
	"RadiusDial": "radius",
	"SoftnessDial": "softness",
	"AlphaDial": "alpha",
}

def selector(cont):
	if "SELECTOR" not in cont.owner:
		cont.owner["SELECTOR"] = Selector(cont.owner.scene)
		cont.owner['prof'] = cProfile.Profile()
		return
	
	cont.owner["prof"].runcall(cont.owner["SELECTOR"].update)
	if bge.logic.keyboard.events[bge.events.F1KEY] == 1:
		cont.owner["prof"].print_stats(sort='tottime')


LEVEL_DIR = os.path.normpath(os.path.join(
	os.path.dirname(os.path.abspath(__file__)), 
	'../ToTheSurface/Data'
))
ROOT_DIR = os.path.normpath(os.path.join(
	os.path.dirname(os.path.abspath(__file__)), 
	'../'
))

class Selector:
	def __init__(self, scene):
		self.scene = scene
		self.mouse = MouseCasterOrtho(scene)
		self.brush = Brush()
		self._preview = BrushPreview(scene.objects["BrushPreview"], self.brush)

		for obj_name in NAME_TO_PARAM:
			self.mouse.add_obj_function(scene.objects[obj_name], self._set_brush_param_raw)
		self.mouse.add_obj_function(scene.objects["World"], self._update_brush_pos)
		self.mouse.add_obj_function(scene.objects["World"], self.draw)
		self.mouse.add_obj_function(scene.objects["World"], self.zoom)
		self.mouse.add_obj_function(scene.objects["BrushPreview"], self._toggle_preview)
		self.brush.on_change.append(self.update_previews)
		self.brush.on_change.append(self._update_brush_scale)

		self.brush.radius = 0.5
		self.brush.growth = 0.0
		self.brush.rock = 0.0
		self.brush.water = 0.0
		self.brush.softness = 0.5
		self.brush.alpha = 1.0
		self.brush.regenerate_brush()

		self.panel = Panel(scene.objects["Panel"])
		self.map = WorldMap(scene.objects['World'], [1024, 1024])

		self.count = 0
		self._start_pos = None  # Mouse world panning
		
		self.map.load(
			os.path.join(LEVEL_DIR, levelname)
		)
		
		
		self.enable_color = True
		self.enable_alpha = True
		
	def update(self):
		if self.count < 2:
			self.count += 1
			self._preview.refresh()
		self.mouse.update()
		
		self.map.update()

		self.panel.update()
		if bge.logic.keyboard.events[bge.events.F2KEY] == 1:
			self.map.save(os.path.join(LEVEL_DIR, levelname))
			
		if bge.logic.keyboard.events[bge.events.LEFTSHIFTKEY] == 1:
			self._toggle_alpha()
		if bge.logic.keyboard.events[bge.events.LEFTALTKEY] == 1:
			self._toggle_color()

	def _toggle_alpha(self, *args):
		self.enable_alpha = not self.enable_alpha
		self.scene.objects["EnableAlpha"].color = [self.enable_alpha, 0, 0, 1]
			
	def _toggle_color(self, *args):
		self.enable_color = not self.enable_color
		self.scene.objects["EnableColor"].color = [self.enable_color, 0, 0, 1]

	def _set_brush_param_raw(self, obj, _pos, _nor, _poly, uv, button):
		"""Interaction with one of the side-panel dials"""
		if button == 'left':
			name = NAME_TO_PARAM[obj.name]
			val = uv.y
			self.brush.set_param(name, val)
		elif button == 'scrollup':
			name = NAME_TO_PARAM[obj.name]
			val = self.brush.get_param(name) + 0.03
			while val > 1.0:
				val -= 1
			self.brush.set_param(name, val)
		elif button == 'scrolldown':
			name = NAME_TO_PARAM[obj.name]
			val = self.brush.get_param(name) - 0.03
			while val < 0.0:
				val += 1
			self.brush.set_param(name, val)


	def update_previews(self, _):
		"""Updates the position of the dials"""
		self._preview.refresh()
		for obj_name in NAME_TO_PARAM:
			obj = self.scene.objects[obj_name]
			val = self.brush.__dict__[NAME_TO_PARAM[obj.name]]
			obj.children[0].worldOrientation = [0, 0, val*2*math.pi]
			
	def _toggle_preview(self, obj, pos, _nor, _poly, _uv, button, static=[True]):
		if button == 'left':
			if static[0] == True:
				self._preview.invert = not self._preview.invert
				static[0] = False
		else:
			static[0] = True


	def _update_brush_pos(self, obj, pos, _nor, _poly, _uv, _button):
		"""Moves the red brush position indicator"""
		self.scene.objects["BrushIndicator"].worldPosition = pos + mathutils.Vector([0, 0, 1])
	
	def _update_brush_scale(self, _):
		"""changes the red brush position indicator"""
		scale = self.brush.radius * self.brush.MAX_SIZE / config.PIXELS_PER_BU
		indicator = self.scene.objects["BrushIndicator"]
		indicator.localScale = [scale] * 3
		indicator.children[0].localScale = [1.0 - self.brush.softness] * 3

	def draw(self, obj, pos, _nor, _poly, _uv, button):
		"""Paints onto the canvas"""
		fill = None
		if button == 'left':
			self._preview.invert = False
			fill = False
		elif button == 'right':
			self._preview.invert = True
			fill = True
		else:
			return
		
		if not self.enable_alpha:
			fill = None
		
		if self.enable_color:
			color = True
		else:
			color = False
			
		self.map.draw(self.brush, pos, fill=fill, color=color)
		
	def zoom(self, obj, pos, _nor, _poly, _uv, button):
		"""Handles mouse pan/zoom"""
		if button == 'scrollup':
			self.scene.active_camera.ortho_scale *= 0.8
		elif button == 'scrolldown':
			self.scene.active_camera.ortho_scale *= 1.25
			
		elif button == 'middle':
			if self._start_pos != None:
				delta = mathutils.Vector(bge.logic.mouse.position) - self._start_pos
				delta.x *= self.scene.active_camera.ortho_scale
				delta.y *= self.scene.active_camera.ortho_scale / bge.render.getWindowWidth() * bge.render.getWindowHeight()
				self.scene.active_camera.worldPosition.x -= delta.x
				self.scene.active_camera.worldPosition.y += delta.y
			
			self._start_pos = mathutils.Vector(bge.logic.mouse.position)
		else:
			self._start_pos = None
		

class Panel:
	def __init__(self, obj):
		self.obj = obj

	def update(self):
		"""Stay in the top left"""
		cam = self.obj.scene.active_camera
		scale = cam.ortho_scale
		height = scale / bge.render.getWindowWidth() * bge.render.getWindowHeight()
		self.obj.localScale.x = height
		self.obj.localScale.y = height

		self.obj.localPosition.x = -scale/2
		self.obj.localPosition.y = height/2


class WorldMap():
	def __init__(self, obj, resolution):
		self.update = self.skip
		self.obj = obj
		self.resolution = mathutils.Vector(resolution)
		
		self.physics_objects = list()

		self.obj.color = [
			config.PIXELS_PER_BU*2/resolution[0],
			config.PIXELS_PER_BU*2/resolution[1],
			1,
			1
		]

		self.tex = bge.texture.Texture(obj, 0, 0)
		self.tex.source = bge.texture.ImageBuff(resolution[0], resolution[1], 0)
		self.tex.source.load(b'\xFF\x00\xFF' * (resolution[0] * resolution[1]), resolution[0], resolution[1])
		self.tex.refresh(False)
		self.obj.scene.objects["EdgeIndicator"].localScale.xy = self.resolution / config.PIXELS_PER_BU
		
		

	def draw(self, brush, world_pos, fill=False, color=True):
		"""Draws with the brush at the specified world coordiantes"""
		pos = world_pos.xy * config.PIXELS_PER_BU
		pos += self.resolution/2
		pos -= mathutils.Vector([brush.MAX_SIZE, brush.MAX_SIZE])/2
		
		if color:
			self.tex.source.plot(
				brush.raw_array, 
				brush.MAX_SIZE, brush.MAX_SIZE,
				int(pos.x), int(pos.y),
				bge.texture.IMB_BLEND_COLOR
			)
			self.tex.source.plot(
				brush.raw_array, 
				brush.MAX_SIZE, brush.MAX_SIZE,
				int(pos.x), int(pos.y),
				bge.texture.IMB_BLEND_LUMINOSITY
			)
		
		if fill is True:
			self.tex.source.plot(
				brush.alpha_array, 
				brush.MAX_SIZE, brush.MAX_SIZE,
				int(pos.x), int(pos.y),
				bge.texture.IMB_BLEND_ERASE_ALPHA
			)
		elif fill is False:
			self.tex.source.plot(
				brush.alpha_array, 
				brush.MAX_SIZE, brush.MAX_SIZE,
				int(pos.x), int(pos.y),
				bge.texture.IMB_BLEND_ADD_ALPHA
			)
		self.tex.refresh(False)

	def save(self, filename):
		from PIL import Image
		print("Saving terrain-type map to {}.png".format(filename))
		img = Image.frombytes("RGBA", (int(self.resolution[0]), int(self.resolution[1])), bytes(self.tex.source.image))
		img.save(filename + '.png')
		time.sleep(0.1)
		blend = filename + '.blend'
		os.system("cd {}; make {}".format(
			ROOT_DIR,
			blend
		))
		self.load_physics(filename)
		
	def load_physics(self, filename):
		full_path = filename + '-physics.blend'
		self.physics_objects = []
		
		if full_path in bge.logic.LibList():
			print("Freeing previous physics")
			bge.logic.LibFree(full_path)
		if os.path.exists(full_path):
			print("Loading physics from", full_path)
			existing_objs = list(self.obj.scene.objects)
			bge.logic.LibLoad(full_path, 'Scene')
			
			for obj in self.obj.scene.objects:
				if obj not in existing_objs:
					self.physics_objects.append(obj)
					
			for obj in self.physics_objects:
				obj.color = [0, 1, 0, 1]
				obj.meshes[0].replaceMaterial(
					0,
					self.obj.scene.objects["EdgeIndicator"].meshes[0].materials[0]
				)
				# TODO: Temporary hack because don't know the pixels size
				# in the generate mesh stage
				obj.worldPosition.xy += self.resolution / config.PIXELS_PER_BU / 2
			
		else:
			print("Physics does not exist")

	def redraw(self):
		self.tex.refresh(True)
		self.update = self.skip
		
	def skip(self):
		pass
		

	def load(self, filename):
		from PIL import Image
		image = Image.open(filename + '.png')
		self.resolution = mathutils.Vector(image.size)
		self.tex.source.load(b'\xFF\x00\xFF' * (image.size[0] * image.size[1]), image.size[0], image.size[1])
		self.tex.source.plot(
			image.tobytes(), 
			image.size[0], image.size[0],
			0, 0,
			bge.texture.IMB_BLEND_COPY
		)
		
		self.tex.refresh(False)
		self.load_physics(filename)
		self.update = self.redraw


class Brush():
	MAX_SIZE = 64
	BPP = 4  # Bytes per pixel
	def __init__(self):
		self.growth = 0
		self.rock = 0
		self.water = 0
		self.radius = 0
		self.softness = 0
		self.alpha = 0
		self.on_change = list()

		self.raw_array = bytearray(self.MAX_SIZE * self.MAX_SIZE * self.BPP)
		self.alpha_array = bytearray(self.MAX_SIZE * self.MAX_SIZE * self.BPP)
		self.regenerate_brush()

	def get_param(self, name):
		return self.__dict__[name]

	def set_param(self, name, val):
		self.__dict__[name] = val
		self.regenerate_brush()

	def regenerate_brush(self):
		size = self.MAX_SIZE

		for x in range(size):
			x_dist = x - size/2 + 0.5
			for y in range(size):
				y_dist = y - size/2 + 0.5
				dist = math.sqrt(x_dist **2 + y_dist ** 2)
				pixel_num = y*size*self.BPP + x*self.BPP
				tmp_rad = self.radius * size/2
				if tmp_rad == 0:
					radius = 0
				else:
					radius = max(0, (tmp_rad - dist)/tmp_rad)
				soft = radius ** (self.softness * 5.0) * self.alpha
				col = [
					int(self.growth*255),
					int(self.rock*255),
					int(self.water*255),
					int(soft*255)
				]
				self.alpha_array[pixel_num:pixel_num+4] = col
				col[3] = int((soft ** 0.8) * 255)
				self.raw_array[pixel_num:pixel_num+4] = col
		call_list(self.on_change, [self])


class BrushPreview:
	def __init__(self, obj, brush):
		self.obj = obj
		self.brush = brush
		self.tex = bge.texture.Texture(obj, 0, 0)
		self.tex.source = bge.texture.ImageBuff(brush.MAX_SIZE, brush.MAX_SIZE, 0)
		self.tex.refresh(False)
		self.obj["tex"] = self.tex
		
	@property
	def invert(self):
		return self.obj.color[0] < 0.5
	
	@invert.setter
	def invert(self, val):
		if val:
			self.obj.color = [0, 0, 0, 1]
		else:
			self.obj.color = [1, 0, 0, 1]

	def refresh(self):
		size = self.brush.MAX_SIZE
		self.tex.source.load(b'\xFF\xFF\xFF' * (size ** 2), size, size)
		self.tex.source.plot(self.brush.raw_array, size, size, 0, 0)
		self.tex.refresh(False)



class MouseCasterOrtho:
	def __init__(self, scene):
		self.scene = scene
		self.known_objects = {}
		bge.render.showMouse(True)

	def add_obj_function(self, obj, function):
		if obj not in self.known_objects:
			self.known_objects[obj] = [function]
		else:
			self.known_objects[obj].append(function)

	def update(self):
		cam = self.scene.active_camera
		pos1 = mathutils.Vector(list(bge.logic.mouse.position) + [0]) - mathutils.Vector([0.5, 0.5, 0])
		pos1.x *= cam.ortho_scale
		pos1.y *= -cam.ortho_scale / bge.render.getWindowWidth() * bge.render.getWindowHeight()
		
		pos2 = pos1.copy()
		pos2.z = -5
		pos1 = cam.worldTransform * pos1
		pos2 = cam.worldTransform * pos2
		hit_obj, pos, nor, poly, uv = cam.rayCast(pos2, pos1, 50, "", 1, 0, 2)
		
		if hit_obj in self.known_objects:
			button = None
			if bge.events.LEFTMOUSE in bge.logic.mouse.active_events:
				button = 'left'
			elif bge.events.RIGHTMOUSE in bge.logic.mouse.active_events:
				button = 'right'
			elif bge.events.MIDDLEMOUSE in bge.logic.mouse.active_events:
				button = 'middle'
			elif bge.events.WHEELUPMOUSE in bge.logic.mouse.active_events:
				button = 'scrollup'
			elif bge.events.WHEELDOWNMOUSE in bge.logic.mouse.active_events:
				button = 'scrolldown'

			call_list(
				self.known_objects[hit_obj], 
				[hit_obj, pos, nor, poly, uv, button]
			)


def call_list(func_list, args=(), kwargs={}):
	for func in func_list:
		func(*args, **kwargs)
