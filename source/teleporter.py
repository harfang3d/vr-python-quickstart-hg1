# -*-coding:Utf-8 -*

# ===========================================================

#              - HARFANG® 3D - www.harfang3d.com

#                    - Python tutorial -

#						VR teleporter

# ===========================================================

import harfang as hg
import math
import bspline

plus = hg.GetPlus()

authorise_ground_node = None
controller_id_teleporter = 1

def draw_spline(scene_simple_graphic, p1, p2, p3, p4, color=hg.Color.White):
	P = [(p1.x, p1.y, p1.z), (p2.x, p2.y, p2.z), (p3.x, p3.y, p3.z), (p4.x, p4.y, p4.z)]

	C = bspline.C_factory(P, 3, "clamped")
	if C:
		step = 50
		prev_value = [p1.x, p1.y, p1.z]
		for i in range(step):
			val = C(float(i)/step * C.max)
			scene_simple_graphic.Line(prev_value[0], prev_value[1], prev_value[2], val[0], val[1], val[2], color, color)
			prev_value = val

def draw_circle(scene_simple_graphic, world, r, color=hg.Color.White):
	step = 50
	prev = hg.Vector3(math.cos(0) * r, 0, math.sin(0) * r) * world
	for i in range(step+1):
		val = hg.Vector3(math.cos(math.pi*2*float(i)/step) * r, 0, math.sin(math.pi*2*float(i)/step) * r) * world
		scene_simple_graphic.Line(prev.x, prev.y, prev.z, val.x, val.y, val.z, color, color)
		prev = val

def setup_teleporter(scn):
	global authorise_ground_node

	authorise_ground_node = scn.GetNode("chaperone_area")

	if authorise_ground_node is not None:
		p = authorise_ground_node.GetTransform().GetPosition()
		p.y += 0.001
		authorise_ground_node.GetTransform().SetPosition(p)
		rb = hg.RigidBody()
		rb.SetCollisionLayer(2)
		rb.SetType(hg.RigidBodyKinematic)
		authorise_ground_node.AddComponent(rb)
		mesh_col = hg.MeshCollision()
		geo = hg.Geometry()
		hg.LoadGeometry(geo, authorise_ground_node.GetObject().GetGeometry().GetName())
		mesh_col.SetGeometry(geo)
		mesh_col.SetMass(0)
		authorise_ground_node.AddComponent(mesh_col)
		mat = plus.GetRenderSystemAsync().LoadMaterial("assets/selected_ground.mat", False)
		while not mat.IsReady():
			scn.UpdateAndCommitWaitAll()

		authorise_ground_node.GetObject().GetGeometry().SetMaterial(0, mat)
		# authorise_ground_node.SetIsStatic(True)

		# update to be sure everything is loaded
		while not authorise_ground_node.IsReady():
			scn.UpdateAndCommitWaitAll()
		while not authorise_ground_node.GetObject().GetGeometry().GetMaterial(0).IsReady():
			scn.UpdateAndCommitWaitAll()
		while authorise_ground_node.GetRigidBody().GetState() == hg.NotReady:
			scn.UpdateAndCommitWaitAll()


def update_camera_teleporter(scn, scene_simple_graphic, world, use_vr):
	try:
		controller = hg.GetInputSystem().GetDevice("VR Controller {}".format(controller_id_teleporter))
	except:
		controller = None
	pos_start = None
	dir_teleporter = None
	teleporter_activate = False

	if use_vr and controller is not None:
		if controller.GetValue(hg.InputButton0) != 0 or controller.GetValue(hg.InputButton1) != 0:
			pos_cam = world.GetTranslation()
			mat_controller = controller.GetMatrix(hg.InputDeviceMatrixHead)
			dir_teleporter = mat_controller.GetZ()
			pos_start = mat_controller.GetTranslation() + pos_cam

			teleporter_activate = controller.WasButtonPressed(hg.Button0)
	else:
		if plus.KeyDown(hg.KeyX) or plus.KeyDown(hg.KeyC):
			pos_start = world.GetTranslation()
			dir_teleporter = world.GetZ()
			if plus.KeyPress(hg.KeyC):
				teleporter_activate = True

	if pos_start is not None:
		if pos_start.y < 0:
			return

		# project point on the ground
		cos_angle = hg.Dot(dir_teleporter, hg.Vector3(dir_teleporter.x, 0, dir_teleporter.z).Normalized())
		cos_angle = min(1.0, max(cos_angle, -1))
		angle = math.acos(cos_angle)
		if dir_teleporter.y < 0:
			angle = -angle

			velocity = 5
			d = ((velocity * cos_angle) / 9.81) * (velocity * math.sin(angle) + math.sqrt(
				(velocity * math.sin(angle)) ** 2 + 2 * 9.81 * pos_start.y))

		else:
			velocity = 5
			min_d = ((velocity * 1) / 9.81) * (
						velocity * math.sin(0) + math.sqrt((velocity * math.sin(0)) ** 2 + 2 * 9.81 * pos_start.y))
			max_d = 10
			d = min_d + (1.0 - abs(cos_angle)) * max_d

		# find the height from pos
		ground_pos = hg.Vector3(pos_start.x, 0, pos_start.z) + hg.Vector3(dir_teleporter.x, 0,
																		  dir_teleporter.z).Normalized() * d

		hit, trace = scn.GetPhysicSystem().Raycast(ground_pos + hg.Vector3(0, pos_start.y + 0.5, 0),
												   hg.Vector3(0, -1, 0), 4, 5)
		ground_pos.y = 0
		if hit:
			ground_pos.y = trace.GetPosition().y

		authorise_movement = True

		if authorise_ground_node is not None:
			authorise_ground_node.GetObject().GetGeometry().GetMaterial(0).SetFloat3("pos_touched", ground_pos.x,
																					 ground_pos.y, ground_pos.z)
			hit, trace = scn.GetPhysicSystem().Raycast(ground_pos + hg.Vector3(0, 0.5, 0), hg.Vector3(0, -1, 0), 4, 5)
			if not hit or trace.GetNode() != authorise_ground_node:
				authorise_movement = False

		strength_force = math.pow((math.sin(angle) + 1) / 2, 2) * 2

		color = hg.Color(0, 1, 198 / 255) if authorise_movement else hg.Color(1, 18 / 255, 0)
		draw_spline(scene_simple_graphic, pos_start, pos_start + dir_teleporter * strength_force,
							  ground_pos + hg.Vector3(0, strength_force, 0), ground_pos, color)

		if authorise_ground_node is None:
			draw_circle(scene_simple_graphic, hg.Matrix4.TranslationMatrix(ground_pos), 1, color)

		if authorise_movement and teleporter_activate:
			if use_vr:
				head_controller = hg.GetInputSystem().GetDevice("HMD")
				head_pos = head_controller.GetMatrix(hg.InputDeviceMatrixHead).GetTranslation()
				head_pos.y = 0
				ground_pos = ground_pos - head_pos
			else:
				ground_pos += hg.Vector3(0, 1.75, 0)
			return ground_pos
	else:
		if authorise_ground_node is not None and authorise_ground_node.GetObject().GetGeometry().GetMaterial(
				0) is not None:
			authorise_ground_node.GetObject().GetGeometry().GetMaterial(0).SetFloat3("pos_touched", 99999, 99999, 99999)
	return None

