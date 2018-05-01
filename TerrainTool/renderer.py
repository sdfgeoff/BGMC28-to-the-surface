"""This module converts from a terrain map into a svg image
that can be used for collision mesh generation"""
import os
import bge
import sys
import argparse
from PIL import Image
import config

def run(cont):
	if "RENDERER" not in cont.owner:
		cont.owner["RENDERER"] = Renderer(cont.owner)
	cont.owner["RENDERER"].update()

class Renderer:
	def __init__(self, cam):
		self.cam = cam
		self.images = get_files()
		self.in_tex = bge.texture.Texture(self.cam.children["WorldMapFinal"], 0, 0)
		self.out_tex = bge.texture.Texture(self.cam.children["Output"], 0, 0)
		
		self.status = self.cam.children["Status"]
		self.status.resolution = 4
		
		self.mode = self.done
		self.source = None
		self.data = None
		self.size = None

	def update(self):
		self.mode()
		
	def log(self, message):
		print(message)
		self.status.text = message

	def load(self):
		image = self.images.pop()
		self.source = image
		
		self.in_tex.source = bge.texture.ImageFFmpeg(image)
		self.in_tex.refresh(True)
		self.size = [config.HIGHRES_MULTIPLIER * i for i in self.in_tex.source.size]
		
		self.mode = self.render_high
		self.log("Rendering to {}".format(self.size))
		
	def render_high(self):
		self.out_tex.source = bge.texture.ImageRender(
			self.cam.scene, self.cam, 
			*self.size
		)
		
		self.out_tex.refresh(True)
		
		self.mode = self.extract
		self.log("Extracting from GPU")
		
	def extract(self):
		
		self.data = bytes(self.out_tex.source.image)
		
		self.mode = self.save_to_bmp
		self.log("Saving to bmp")
		
	def save_to_bmp(self):
		img = Image.frombytes('RGBA', self.size, self.data)
		img.save("/tmp/tmp.bmp")
		
		self.mode = self.convert_to_svg
		
	
	def done(self):
		self.log("Done")
		if self.images:
			self.log("Loading {}".format(self.images[-1]))
			self.mode = self.load
		else:
			bge.logic.endGame()
		

	def convert_to_svg(self):
		new_name = self.source.rsplit('.', maxsplit=1)[0] + '.svg'
		print("Saving to SVG at {}".format(new_name))
		os.system("potrace /tmp/tmp.bmp -s -o {}".format(new_name))
		
		self.mode = self.done


def get_files():
	arg_pos = sys.argv.index('--') + 1
	return(sys.argv[arg_pos:])
	
