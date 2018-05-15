import math
import bge
import time
import aud
import os
import mathutils

import common

DUST_DISTANCE = 8
TORQUE = 20
FORCE = 40
LIN_DRAG = 0.05
ANG_DRAG = 10


def init(cont):
    """Tester for the ship"""
    if 'SHIP' not in cont.owner:
        cont.owner['SHIP'] = Ship(cont.owner)
    cont.owner['SHIP'].update()







class Ship:
    """The thing the player flies around"""
    def __init__(self, rootobj):
        self.rootobj = rootobj
        objs = common.NamedList()
        objs.append(rootobj)
        for child in rootobj.childrenRecursive:
            objs.append(child)

        self.objs = objs

        for obj in self.objs:
            if obj.getPhysicsId() != 0:
                obj.collisionCallbacks.append(self._onhit)

        self._leg_constraints = {}
        self._setup_legs()

        self._particles = []

        self.legs_deployed = True
        self.rootobj.scene.active_camera = self.objs["ShipCamera"]

        self._left = 0
        self._right = 0
        self._target_left = 0
        self._target_right = 0
        self.fly(0, 0)


        self.hit_sound = HitSound()
        self.left_booster_sound = BoosterSound()
        self.right_booster_sound = BoosterSound()
        self.wind_sound = WindSound()
        self.left_leg_sound = LegMotorSound()
        self.right_leg_sound = LegMotorSound()


        self.on_ship_move = common.FunctionList()  # Called with world position

    @property
    def speed(self):
        return self.rootobj.worldLinearVelocity.xz.length

    @property
    def orientation(self):
        return self.rootobj.worldOrientation.to_euler().y

    def update(self):
        """Ensures the rocket is flying. Call every frame"""
        self._update_legs()
        self._update_drag()
        self._update_engines()
        self._update_particles()
        self._update_light()
        self.hit_sound.update()

        self._check_underwater()

        self.on_ship_move.fire(self.rootobj.worldPosition)

    def _update_light(self):
        light = self.rootobj.childrenRecursive['AntennaTip']
        color = light.color[0]
        color = color * 0.7
        if time.time() % 2.0 < 0.02:
            color = 1.0
        if (time.time() + 0.5) % 2.0 < 0.02:
            color = 1.0

        light.color = [color, color, color, 1.0]

    def _check_underwater(self):
        start = self.rootobj.worldPosition
        end = start + mathutils.Vector([0, 1, 0])
        if self.rootobj.rayCast(start, end, 50, "WATER")[0] is not None:
            # Underwater
            self.rootobj.applyForce([0, 0, 15.0], False)
            self.rootobj.applyForce(-self.rootobj.worldLinearVelocity * 5, False)

    def _update_legs(self):
        for obj in self.objs:
            if 'ALIGN' in obj:
                obj_name = obj['ALIGN']
                obj.worldOrientation = self.objs[obj_name].worldOrientation

        # Leg springs
        for constraint_name in self._leg_constraints:
            target = 1.0 if self.legs_deployed else -1.0
            if target > 0:
                force = 3
            else:
                force = 1000
            if constraint_name == 'left':
                target *= -1

            constraint = self._leg_constraints[constraint_name]
            constraint.setParam(10, target, force)
            if constraint_name == 'left':
                self.left_leg_sound.set_position(constraint.getParam(4))
            else:
                self.right_leg_sound.set_position(constraint.getParam(4))

    def _update_drag(self):
        damping = self.rootobj.worldAngularVelocity.copy()
        damping *= -ANG_DRAG
        self.rootobj.applyTorque(damping)

        drag = self.rootobj.worldLinearVelocity.copy()
        drag *= drag.length
        drag *= -LIN_DRAG

        self.rootobj.applyForce(drag)
        self.objs['LeftLegPhysics'].applyForce(drag)
        self.objs['RightLegPhysics'].applyForce(drag)

        self.wind_sound.set_velocity(drag.length)

    def _update_particles(self):
        """Dust created by the rockets when near the ground"""

        if self._left > 0.1 or self._right > 0.1:
            # Make smoke
            left_flame = self.objs['LeftFlame']
            right_flame = self.objs["RightFlame"]
            down_vec = left_flame.getAxisVect([bge.logic.getRandomFloat() - 0.5, 1, 0])
            pos = (left_flame.worldPosition + right_flame.worldPosition) / 2
            obj, rayhit, _nor = left_flame.rayCast(
                pos,
                pos + down_vec,
                DUST_DISTANCE,
                "", 1, False, 0,
                1
            )
            if obj is not None:
                dist = (rayhit - pos).length
                particle = self.rootobj.scene.addObject(
                    "DustParticle",
                    right_flame, 60
                )

                particle.worldLinearVelocity = down_vec * bge.logic.getRandomFloat() * 10.0
                particle.worldLinearVelocity.x *= -2
                particle.worldPosition = rayhit
                particle.worldOrientation = [0, bge.logic.getRandomFloat(), 0]

                amt = (DUST_DISTANCE - dist)/DUST_DISTANCE
                particle.color = [amt] * 3 + [1.0]
                self._particles.append(particle)

        for particle in self._particles[:]:
            if not particle.invalid:
                particle.color = particle.color * 0.9
                if particle.color[0] < 0.05:
                    particle.endObject()
            else:
                self._particles.remove(particle)

    def _update_engines(self):
        self._left = self._left * 0.8 + self._target_left * 0.2
        self._right = self._right * 0.8 + self._target_right * 0.2

        self.left_booster_sound.set_thrust(self._left)
        self.right_booster_sound.set_thrust(self._right)

        self.rootobj.applyForce([0, 0, self._left*FORCE], True)
        self.rootobj.applyTorque([0, self._left*TORQUE, 0])
        self.rootobj.applyForce([0, 0, self._right*FORCE], True)
        self.rootobj.applyTorque([0, self._right*-TORQUE, 0])

        light = self.objs['EngineLights']
        light.energy = min(10.0, (self._left + self._right) * 10.0)
        n_steer = self._left - self._right
        light.localPosition.x = -n_steer/4
        light.spotblend = abs(n_steer) * 0.5 + 0.5
        light.spotsize = 80.0 - abs(n_steer) * 20.0 - bge.logic.getRandomFloat() * 8

        light.localPosition.y = (4.1-light.spotsize/40) / 2

        self.objs['LeftFlame'].color = [self._left] * 3 + [1]
        self.objs['RightFlame'].color = [self._right] * 3 + [1]

    def _setup_legs(self):
        self.objs['LeftLegPhysics'].removeParent()
        self.objs['RightLegPhysics'].removeParent()
        self._leg_constraints["left"] = bge.constraints.createConstraint(
            self.objs['LeftLegPhysics'].getPhysicsId(),
            self.rootobj.getPhysicsId(),
            bge.constraints.GENERIC_6DOF_CONSTRAINT,
            pivot_x=0.0, pivot_y=0.0, pivot_z=0.0,
            axis_x=math.pi, axis_y=0.0, axis_z=0.0,
            flag=0
        )
        self._leg_constraints["right"] = bge.constraints.createConstraint(
            self.objs['RightLegPhysics'].getPhysicsId(),
            self.rootobj.getPhysicsId(),
            bge.constraints.GENERIC_6DOF_CONSTRAINT,
            pivot_x=0.0, pivot_y=0.0, pivot_z=0.0,
            axis_x=0.0, axis_y=math.pi/2, axis_z=0.0,
            flag=0
        )

        for constraint_name in self._leg_constraints:
            constraint = self._leg_constraints[constraint_name]
            # Translation
            constraint.setParam(0, 0, 0)
            constraint.setParam(1, 0, 0)
            constraint.setParam(2, 0, 0)
            # Rotation
            constraint.setParam(3, 0, 0)
            ori = self.rootobj.worldOrientation.to_euler()
            if constraint_name == 'right':
                constraint.setParam(4, -math.pi/4, math.pi/4 + 0.2)
                ori.y += 0.2
                self.objs['RightLegPhysics'].worldOrientation = ori
            else:
                constraint.setParam(4, -math.pi/4 - 0.2, math.pi/4)
                ori.y -= 0.2
                self.objs['LeftLegPhysics'].worldOrientation = ori
            constraint.setParam(5, 0, 0)

    def fly(self, thrust, steer):
        """Sets the state of the engines"""
        self._target_left = min(1, max(0, thrust + steer))
        self._target_right = min(1, max(0, thrust - steer))


    def _onhit(self, *args):

        force = self.speed
        if len(args) == 4:
            for hitpoint in args[3]:
                force = hitpoint.appliedImpulse

        self.hit_sound.set_speed(force)

    def pause(self):
        self.rootobj.suspendDynamics()

    def resume(self):
        self.rootobj.restoreDynamics()


class HitSound:
    DEVICE = aud.device()
    def __init__(self):
        path = os.path.dirname(os.path.abspath(__file__))
        factory = aud.Factory(path + '/booster.wav').loop(-1)

        # play the audio, this return a handle to control play/pause
        self.handle = self.DEVICE.play(factory)
        self.handle.volume = 0.001

        self.prev_speed = 0

    def set_speed(self, percent):
        accel = self.prev_speed - percent
        self.prev_speed = percent
        if abs(accel) > 1.0:
            self.handle.volume = max(0, -accel, self.handle.volume)
            self.handle.pitch = bge.logic.getRandomFloat()*5

    def update(self):
        self.handle.volume *= 0.8
        self.handle.pitch *= 0.5



class BoosterSound:
    DEVICE = aud.device()
    def __init__(self):
        path = os.path.dirname(os.path.abspath(__file__))
        factory = aud.Factory(path + '/booster.wav').loop(-1)

        # play the audio, this return a handle to control play/pause
        self.handle = self.DEVICE.play(factory)
        self.handle.volume = 0.001
        self.prev_percent = 0

        self.oscillator = 0

    def set_thrust(self, percent):
        diff = percent - self.prev_percent
        self.prev_percent = percent


        self.handle.volume = percent ** 2
        self.handle.pitch = max(0, (diff * 4 + 1.0) ** 2.0 * 0.8 + self.oscillator)


        self.oscillator = (bge.logic.getRandomFloat() - 0.5) * 2 * 0.1 + self.oscillator * 0.9
        self.oscillator = self.oscillator * 0.99


class WindSound:
    DEVICE = aud.device()
    def __init__(self):
        path = os.path.dirname(os.path.abspath(__file__))
        factory = aud.Factory(path + '/wind.wav').loop(-1)

        self.oscillator = 0

        # play the audio, this return a handle to control play/pause
        self.handle = self.DEVICE.play(factory)
        self.handle.volume = 0.001
        self.prev_percent = 0

    def set_velocity(self, speed):
        speed = speed ** 0.5
        self.handle.volume = max(0, speed * 0.02 + self.oscillator * 0.2)
        self.handle.pitch = max(0, (speed * 0.5 + self.oscillator * 0.2) * 0.3)


        self.oscillator = (bge.logic.getRandomFloat() - 0.5) * 2 * 0.1 + self.oscillator * 0.9
        self.oscillator = self.oscillator * 0.5 + 0.5 * 0.5


class LegMotorSound:
    DEVICE = aud.device()
    def __init__(self):
        path = os.path.dirname(os.path.abspath(__file__))
        factory = aud.Factory(path + '/legmotors.wav').loop(-1)

        self.handle = self.DEVICE.play(factory)
        self.handle.volume = 0.001
        self.prev_position = 0
        self.prev_speed = 0

    def set_position(self, position):
        speed = abs(self.prev_position - position)
        accel = abs(speed - self.prev_speed)
        self.prev_speed = speed


        self.prev_position = position
        accel = min(accel, 0.016)
        speed = min(speed, 0.016)

        self.handle.volume = max(0, speed * 10 - accel * 10)
        self.handle.pitch = max(0, (speed * 50) ** 10 + 0.2 - accel * 10.0)

