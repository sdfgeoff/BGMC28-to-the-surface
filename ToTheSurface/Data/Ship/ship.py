import math
import bge


DUST_DISTANCE = 8


def init(cont):
    """Tester for the ship"""
    if 'SHIP' not in cont.owner:
        cont.owner['SHIP'] = Ship(cont.owner)
    cont.owner['SHIP'].update()

    if bge.logic.keyboard.events[bge.events.EKEY] == 1:
        cont.owner['SHIP'].legs_deployed = not cont.owner['SHIP'].legs_deployed

    thrust = float(bge.events.UPARROWKEY in bge.logic.keyboard.active_events)
    steer = 0
    steer -= bge.events.LEFTARROWKEY in bge.logic.keyboard.active_events
    steer += bge.events.RIGHTARROWKEY in bge.logic.keyboard.active_events
    cont.owner['SHIP'].fly(thrust, steer)


class Ship:
    """The thing the player flies around"""
    def __init__(self, rootobj):
        self.rootobj = rootobj
        objs = self.rootobj.groupObject.groupMembers
        for obj in self.rootobj.groupObject.groupMembers:
            objs += obj.childrenRecursive

        self.objs = objs

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

    def update(self):
        """Ensures the rocket is flying. Call every frame"""
        self._update_legs()
        self._update_drag()
        self._update_engines()
        self._update_particles()

    def _update_legs(self):
        for obj in self.objs:
            if 'ALIGN' in obj:
                obj.worldOrientation = self.objs[obj['ALIGN']].worldOrientation

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

    def _update_drag(self):
        damping = self.rootobj.worldAngularVelocity.copy()
        damping *= -10
        self.rootobj.applyTorque(damping)

        drag = self.rootobj.worldLinearVelocity.copy()
        drag *= drag.length
        drag *= -0.01

        self.rootobj.applyForce(drag)
        self.objs['LeftLegPhysics'].applyForce(drag)
        self.objs['RightLegPhysics'].applyForce(drag)

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

        self.rootobj.applyForce([0, 0, self._left*40], True)
        self.rootobj.applyTorque([0, self._left*40, 0])
        self.rootobj.applyForce([0, 0, self._right*40], True)
        self.rootobj.applyTorque([0, self._right*-40, 0])

        light = self.objs['EngineLights']
        light.energy = min(10.0, (self._left + self._right) * 10.0)
        n_steer = self._left - self._right
        light.localPosition.x = -n_steer/2
        light.spotblend = abs(n_steer) * 0.5 + 0.5
        light.spotsize = 80.0 - abs(n_steer) * 20.0 - bge.logic.getRandomFloat() * 8

        light.localPosition.y = 4.1-light.spotsize/40

        self.objs['LeftFlame'].color = [self._left] * 3 + [1]
        self.objs['RightFlame'].color = [self._right] * 3 + [1]

    def _setup_legs(self):
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
        self._target_left = max(0, thrust + steer)
        self._target_right = max(0, thrust - steer)
