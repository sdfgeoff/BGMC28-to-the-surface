import bge

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

    obj.resolution = obj_pixels / obj_height / default_px_per_bu
