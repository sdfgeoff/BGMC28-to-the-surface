UPBGE = upbge
BLENDER = blender


LEVEL_SOURCE_IMAGES = $(wildcard ToTheSurface/Data/level.png)
LEVEL_SVGS = $(patsubst %.png, %.svg, $(LEVEL_SOURCE_IMAGES))
LEVEL_BLENDS = $(patsubst %.png, %.blend, $(LEVEL_SOURCE_IMAGES))


%.svg: %.png TerrainTool/renderer.py TerrainTool/TerrainRenderer.blend
	$(UPBGE) TerrainTool/TerrainRenderer.blend --python TerrainTool/startgame.py -- $<


%.blend: %.svg TerrainTool/generate_mesh.py
	$(BLENDER) -b --python TerrainTool/generate_mesh.py -- $<


svgs: $(LEVEL_SVGS)
blends: $(LEVEL_BLENDS)
