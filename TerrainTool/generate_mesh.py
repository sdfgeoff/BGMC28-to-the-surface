import bpy
import sys
import mathutils
import os
import time

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

    to_delete = []

    print("Pre-cleanup of small objects")
    i = 0
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects[:]:
        if obj.dimensions.length < config.MERGE_DISTANCE:
            i += 1
            obj.select = True
    bpy.ops.object.delete()
    print("Deleted {} objects".format(i))

    print("Converting to meshes")
    for obj_id, obj in enumerate(bpy.context.scene.objects[:]):
        obj.select = True
        obj.data.fill_mode = 'NONE'
        obj.data.resolution_u = 5
        bpy.context.scene.objects.active = obj
        bpy.ops.object.convert(target='MESH')



    obj = bpy.context.scene.objects[0]
    bpy.context.scene.objects.active = obj

    print("Joining")
    bpy.ops.object.join()

    obj.scale *= config.SVG_SCALE_FACTOR
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    group.objects.link(obj)

    bpy.context.scene.objects.active = obj

    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action='SELECT')

    # Simplify Mesh
    print("Limited Dissolve")
    bpy.ops.mesh.dissolve_limited(angle_limit=config.ANGLE_LIMIT)
    print("Removing Doubles")
    bpy.ops.mesh.remove_doubles(threshold=config.MERGE_DISTANCE)

    print("Removing lone edges")
    bpy.ops.mesh.select_loose()
    bpy.ops.mesh.delete(type='VERT')

    print("Extruding")
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.extrude_edges_move()
    bpy.ops.transform.translate(value=(0, 0, 1.0))
    bpy.ops.object.mode_set(mode = 'OBJECT')

    print("Splitting")
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    for j in range(config.NUM_TILES):
        for i in range(config.NUM_TILES):
            print('{}/{}'.format(j*config.NUM_TILES + i, config.NUM_TILES**2))
            bpy.ops.mesh.select_mode(type="VERT")
            bpy.ops.object.mode_set(mode = 'OBJECT')
            max_x = obj.dimensions.x / (config.NUM_TILES) * (i + 1) + 1
            max_y = -obj.dimensions.x / (config.NUM_TILES) * (j + 1) - 1
            selected = False
            for vert in obj.data.vertices:
                if vert.co.x < max_x and vert.co.y > max_y:
                    vert.select = True
                    selected = True
            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.ops.mesh.select_mode(type="FACE")
            try:
                bpy.ops.mesh.separate(type="SELECTED")
            except RuntimeError:
                pass
            bpy.ops.mesh.select_all(action='DESELECT')

    bpy.ops.object.mode_set(mode = 'OBJECT')
    for obj in bpy.context.scene.objects:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select = True
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        assign_material(obj)

def main(input_file):
    for obj in bpy.context.scene.objects:
        obj.select = True
    bpy.ops.object.delete()
    print("Importing SVG")
    bpy.ops.import_curve.svg(filepath=input_file[0])

    process()

    bpy.ops.wm.save_as_mainfile(
        filepath=input_file[0].replace('.svg', '-physics.blend'),
        compress=True
    )


def run_function_with_args(function):
    '''Finds the args to the python script rather than to blender as a whole
    '''
    arg_pos = sys.argv.index('--') + 1

    function(sys.argv[arg_pos:])
    print("SUCCESS")
    sys.exit(0)


run_function_with_args(main)
