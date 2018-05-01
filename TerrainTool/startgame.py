import bpy

def leave(*args):
	exit(0)

bpy.app.handlers.game_post.append(leave)
bpy.ops.view3d.game_start()
