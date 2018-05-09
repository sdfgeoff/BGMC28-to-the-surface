import math
import bge
import mathutils
import time

class HUD:
	def __init__(self, scene):
		self.scene = scene
		self.radio_box_left = RadioBox(scene.objects['RadioBoxLeft'])
		self.radio_box_right = RadioBox(scene.objects['RadioBoxRight'])
		self.major_text = MajorText(scene.objects['MajorText'])
		
	def update(self):
		self.radio_box_left.update()
		self.radio_box_right.update()
		self.major_text.update()
		
	def step_text(self):
		if not self.major_text.all_visible:
			self.major_text.show_all()
		else:
			self.major_text.close()

		if not self.radio_box_left.all_visible:
			self.radio_box_left.show_all()
		else:
			self.radio_box_left.close()

		if not self.radio_box_right.all_visible:
			self.radio_box_right.show_all()
		else:
			self.radio_box_right.close()


class MajorText:
	MAX_TIME = 8.0
	def __init__(self, root_obj):
		self.obj = root_obj
		fix_text(self.obj)
		self.start_time = time.time()
		self.scale = 0
		self.closing = True
		
		#self.text = ''
		
		
	@property
	def visible(self):
		return self.obj.visible
		
	@visible.setter
	def visible(self, val):
		self.obj.visible = val
		for obj in self.obj.childrenRecursive:
			obj.visible = val

	@property
	def text(self):
		return self.obj.text
		
	@text.setter
	def text(self, val):
		# Compute final text with newlines
		self.obj.color = [1, 1, 1, 0]
		self.scale = 0
		self.obj.text = val
		self.closing = False
		self.visible = True
		self.start_time = time.time()
		
		length = self.obj.dimensions.x
		self.obj.worldPosition.x = -length/2
		for child in self.obj.childrenRecursive:
			child.localPosition.x = length/2
		
	def update(self):
		if self.closing:
			self.scale = self.scale * 0.9
		else:
			if time.time() - self.start_time > self.MAX_TIME:
				self.close()
			self.scale = self.scale * 0.9 + 0.1
		self.obj.color[3] = self.scale ** 5
		for child in self.obj.childrenRecursive:
			child.localScale.y = self.scale
			child.color = [1, 1, 1, self.scale]
		

			
	def close(self):
		self.closing = True
		
	def show_all(self):
		"""Show the text instantly"""
		if not self.closing:
			self.scale = 1.0
			
	@property
	def all_visible(self):
		return self.scale > 0.99
		
		
		


class RadioBox:
	"""Where messages via the radio appear"""
	PADDING = 0.2
	MAX_WIDTH = 5.0
	MAX_TIME = 10.0
	def __init__(self, root_obj):
		self.obj = root_obj.groupMembers['RadioMessage']
		fix_text(self.obj)
		self._final_text = ''
		self.closing = True
		self.start_time = time.time()
		
		self.pointer_target = mathutils.Vector([0, 0])
		
		# Set objects to "off"
		left = self.obj.childrenRecursive['LeftPane']
		right = self.obj.childrenRecursive['RightPane']
		pointer = self.obj.childrenRecursive['Pointer']
		
		left.localScale.y = 0
		left.color[3] = 0
		right.localScale.y = 0
		right.color[3] = 0
		self.obj.color[3] = 0
		
		pointer.color[3] = 0
		
		for obj in left.childrenRecursive:
			obj.localScale.y = 0
			obj.color[3] = 0
		for obj in right.childrenRecursive:
			obj.localScale.y = 0
			obj.color[3] = 0
		
		
		#self.text = "This is some text"
		
		
		
	@property
	def visible(self):
		return self.obj.visible
		
	@visible.setter
	def visible(self, val):
		self.obj.visible = val
		for obj in self.obj.childrenRecursive:
			obj.visible = val


	@property
	def text(self):
		return self.obj.text
		
	@text.setter
	def text(self, val):
		# Compute final text with newlines
		words = val.split(' ')
		self.obj.text = ''
		self.visible = True
		self.start_time = time.time()
		self.closing = False
		for word in words:
			old_text = self.obj.text
			self.obj.text += word + ' '
			if self.obj.dimensions.x > self.MAX_WIDTH:
				self.obj.text = old_text# + '\n' + word
				self.obj.text += '\n' + word + ' '
		self._final_text = self.obj.text
		
		# Position borders correctly
		height = self.obj.dimensions.y
		width = self.obj.dimensions.x
		
		left = self.obj.childrenRecursive['LeftPane']
		right = self.obj.childrenRecursive['RightPane']
			
		right.localPosition.x = width + self.PADDING
		
		# Blank the text so it can be 'typed' in
		self.obj.text = ''
		
	def update(self):
		if not self.closing:
			# Type the text
			if len(self.obj.text) < len(self._final_text):
				self.obj.text = self._final_text[0:len(self.obj.text) + 1]
			
			# Check the timeout
			if time.time() - self.start_time > self.MAX_TIME:
				self.close()
				
			border_target = self.obj.dimensions.y
			color_target = 1
		else:
			border_target = 0
			color_target = 0
			
		left = self.obj.childrenRecursive['LeftPane']
		right = self.obj.childrenRecursive['RightPane']
		pointer = self.obj.childrenRecursive['Pointer']
		
		current_height = left.localScale.y - self.PADDING*2
		height = border_target * 0.1 + current_height * 0.9
		
		current_color = left.color[3]
		color = color_target * 0.1 + current_color * 0.9
		
		if color > 0.001:
			left.localScale.y = height + self.PADDING*2
			left.color[3] = color
			right.localScale.y = height + self.PADDING*2
			right.color[3] = color
			
			self.obj.color[3] = color
			pointer.color[3] = color
			
			for obj in left.childrenRecursive:
				obj.localScale.y = 1/(height + self.PADDING*2)
				obj.color[3] = color
			for obj in right.childrenRecursive:
				obj.localScale.y = 1/(height + self.PADDING*2)
				obj.color[3] = color
			self._update_pointer()
			
			
	def _update_pointer(self):
		pointer = self.obj.childrenRecursive['Pointer']
		world_pos = mathutils.Vector(self.pointer_target) - mathutils.Vector([0.5, 0.5])
		world_pos.y *= -1
		aspect = (bge.render.getWindowHeight() / bge.render.getWindowWidth())
		world_pos.x = world_pos.x * self.obj.scene.active_camera.ortho_scale / 2 / aspect
		world_pos.y = world_pos.y * self.obj.scene.active_camera.ortho_scale / 2
		delta = pointer.worldPosition.xy - world_pos.xy
		
		
		pointer.worldOrientation = [0, 0, math.atan2(
			delta.x, -delta.y
		) - math.pi]
		
		pointer.localScale.y = delta.length - 0.2
			
			
	def close(self):
		self.closing = True
			
	def show_all(self):
		"""Show the text instantly"""
		self.obj.text = self._final_text
			
	@property
	def all_visible(self):
		return len(self.obj.text) == len(self._final_text)
			
	def set_pointer_position(self, screen_pos):
		pointer = self.obj.childrenRecursive['Pointer']
		self.pointer_target = mathutils.Vector(screen_pos)
		




def fix_text(obj):
    '''Compute a font object's ideal resolution assuming an orthographic camera'''
    # Defined in blender source: an object 1 unit high with a resultion of 1 will have 100px
    default_px_per_bu = 100  

    window_width = bge.render.getWindowWidth()

    # Measure the size of the font object (height)
    text = obj.text
    obj.text = '|'
    obj_height = obj.dimensions[1]
    obj.text = text
    
    if not obj.scene.active_camera.perspective:
        view_width = obj.scene.active_camera.ortho_scale
    else:
        raise Exception("Only for orthographic cameras at the moment")


    pixel_ratio = window_width / view_width # pixels / bu
    obj_pixels = pixel_ratio * obj_height
