import math
import bge
import mathutils
import time
import os
import math
import text_tools
import common

SCREENSHOT_PATH = common.BASE_PATH + '/../Found'

class HUD:
    def __init__(self, scene):
        self.scene = scene
        self.radio_box_left = RadioBox(scene.objects['RadioBoxLeft'])
        self.radio_box_right = RadioBox(scene.objects['RadioBoxRight'])
        self.major_text = MajorText(scene.objects['MajorText'])

        self.log_book = LogBook(scene.objects['LogBook'])
        self.log_icon_glow = False

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

    @property
    def log_icon_glow(self):
        return self.scene.objects['LogSymbol'].color[0] < 0.99

    @log_icon_glow.setter
    def log_icon_glow(self, val):
        if val:
            col = [1, 1, 1, 1]
        else:
            col = [0.5, 0.5, 0.5, 0.5]
        self.scene.objects['LogSymbol'].color = col


class MajorText:
    MAX_TIME = 8.0
    def __init__(self, root_obj):
        self.obj = root_obj
        text_tools.fix_text(self.obj)
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
        text_tools.fix_text(self.obj)
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


class LogBook:
    def __init__(self, rootobj):
        self.objs = rootobj.groupMembers

        self._left_page = LogPanel(self.objs['LeftImage'])
        self._right_page = LogPanel(self.objs['RightImage'])
        self.close_text = self.objs['CloseText']
        text_tools.fix_text(self.objs['FoundText'])
        text_tools.fix_text(self.objs['PageNumText'])
        text_tools.fix_text(self.close_text)

        self.visible = False
        self._location_list = []
        self._been_locations = []

        self._page = 0
        self._num_pages = 0



    def set_location_list(self, loc_list):
        self._location_list = loc_list
        self._num_pages = math.ceil(len(self._location_list)/2)

    def set_found_location_list(self, found_list):
        self._been_locations = found_list

    @property
    def page(self):
        return self._page

    @page.setter
    def page(self, num):
        self._page = max(min(num, self._num_pages - 1), 0)
        self._update_page()
        self._update_text()

    def _update_page(self):
        left_index = self._page*2
        right_index = self._page*2 + 1
        if left_index < len(self._been_locations):
            loc = self._been_locations[left_index]
            self._left_page.location = self._location_list[loc]
        else:
            self._left_page.location = None


        if right_index > len(self._location_list) - 1:
            self._right_page.visible = False
        else:
            self._right_page.visible = True

            if right_index < len(self._been_locations):
                loc = self._been_locations[right_index]
                self._right_page.location = self._location_list[loc]
            else:
                self._right_page.location = None


    def _update_text(self):
        self.objs['FoundText'].text = "Found {} of {} areas".format(
            len(self._been_locations),
            len(self._location_list)
        )
        self.objs['PageNumText'].text = "Page {}/{}".format(
            self._page + 1,
            self._num_pages
        )

        self.objs['LeftArrow'].visible = self._page > 0
        self.objs['RightArrow'].visible = self._page < self._num_pages - 1

    @property
    def visible(self):
        return self._left_page.visible

    @visible.setter
    def visible(self, val):
        self._left_page.visible = val
        self._right_page.visible = val

        self.objs['FoundText'].visible = val
        self.objs['PageNumText'].visible = val
        self.objs['Background'].visible = val

        self.objs['LeftArrow'].visible = val
        self.objs['RightArrow'].visible = val
        self.close_text.visible = val
        if val:
            self._update_text()
            self._update_page()


class LogPanel:
    MAX_WIDTH = 6.0
    def __init__(self, root_obj):
        self.img = root_obj
        self.text_obj = self.img.children[0]

        text_tools.fix_text(self.text_obj)

        self.texture = bge.texture.Texture(self.img, 0)
        self.texture.source = bge.texture.ImageFFmpeg(common.BASE_PATH + "/None.png")
        self.texture.refresh(True)

        self._location = ""
        self.location = None

    @property
    def visible(self):
        return self.img.visible

    @visible.setter
    def visible(self, val):
        self.img.visible = val
        self.text_obj.visible = val

    @property
    def text(self):
        return self.text_obj.text

    @text.setter
    def text(self, val):
        words = val.split(' ')
        self.text_obj.text = ''
        for word in words:
            old_text = self.text_obj.text
            self.text_obj.text += word + ' '
            if self.text_obj.dimensions.x > self.MAX_WIDTH:
                self.text_obj.text = old_text# + '\n' + word
                self.text_obj.text += '\n' + word + ' '

    @property
    def location(self):
        return self.location

    @location.setter
    def location(self, location):
        if location is None:
            self.text = "Undiscovered"
            self.image = None
        else:
            self.text = '{}\n{}\n{}'.format(location['AREA'], '-'*len(location['AREA']), location.get('TEXT', "No Description"))
            self.image = os.path.join(SCREENSHOT_PATH, location['AREA'] + '.png')

    @property
    def image(self):
        return "UNIMPLEMENTED"

    @image.setter
    def image(self, image_name):
        if image_name == None:
            self.texture.source.reload(common.BASE_PATH + "/None.png")
            self.texture.refresh(False)
        else:
            self.texture.source.reload(image_name)
            self.texture.refresh(False)
