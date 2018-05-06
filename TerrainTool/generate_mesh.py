import bpy
import sys
import mathutils
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config


mat = bpy.data.materials.new("Wire")
#mat.type = 'WIRE'
mat.use_shadeless = True
mat.diffuse_color = mathutils.Color([0,1,0])
mat.use_transparency = True
mat.alpha = 0.00
mat.specular_alpha = 0.00
mat.physics.friction = 1.0

def assign_material(obj):
	obj.data.materials[0] = mat


def process():
	bpy.ops.group.create(name="PhysicsMeshes")
	group = bpy.data.groups.get('PhysicsMeshes')

	for obj in bpy.context.scene.objects:
		bpy.ops.object.select_all(action='DESELECT')
		obj.select = True
		
		obj.scale *= config.SVG_SCALE_FACTOR
		bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
		bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
		
		group.objects.link(obj)
		
		bpy.context.scene.objects.active = obj
		
		obj.data.fill_mode = 'NONE'
		bpy.ops.object.convert(target='MESH')
		
		bpy.ops.object.mode_set(mode = 'EDIT')
		bpy.ops.mesh.select_all(action='SELECT')
		# Simplify Mesh
		bpy.ops.mesh.dissolve_limited(angle_limit=config.ANGLE_LIMIT)
		bpy.ops.mesh.remove_doubles(threshold=config.MERGE_DISTANCE)
		
		# Give it faces
		bpy.ops.mesh.extrude_edges_move()
		bpy.ops.transform.translate(value=(0, 0, 1.0))
		
		bpy.ops.mesh.extrude_edges_move
		bpy.ops.object.mode_set(mode = 'OBJECT')
		
		
		assign_material(obj)
		


def main(input_file):
	for obj in bpy.context.scene.objects:
		obj.select = True
	bpy.ops.object.delete()
	
	bpy.ops.import_curve.svg(filepath=input_file[0])
	
	process()
		
	bpy.ops.wm.save_as_mainfile(filepath=input_file[0].replace('.svg', '-physics.blend'))


def run_function_with_args(function):
    '''Finds the args to the python script rather than to blender as a whole
    '''
    arg_pos = sys.argv.index('--') + 1
	
    function(sys.argv[arg_pos:])
    print("SUCCESS")
    sys.exit(0)


run_function_with_args(main)
