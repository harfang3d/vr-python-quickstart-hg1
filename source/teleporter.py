"""
 ===========================================================

			- HARFANG® 3D - www.harfang3d.com

					- Lua tutorial -

						VR teleporter

 ===========================================================
"""
import harfang as hg
import math

authorise_ground_node = None
controller_id_teleporter = 0
flag_rotate = False
rotation_step = 45


def draw_circle(scene_simple_graphic, world, r, color=hg.Color.White):
	step = 50
	prev = hg.Vector3(math.cos(0) * r, 0, math.sin(0) * r) * world
	for i in range(step + 1):
		val = hg.Vector3(math.cos(math.pi * 2 * float(i) / step) * r, 0,
						 math.sin(math.pi * 2 * float(i) / step) * r) * world
		scene_simple_graphic.Line(prev.x, prev.y, prev.z, val.x, val.y, val.z, color, color)
		prev = val


def draw_curve(scene_simple_graphic, p1, p2, p3, p4, color=hg.Color.Blue, steps=10):
	pa = p1
	for i in range(0, steps):
		t = i / steps
		p12 = p1 * (1 - t) + p2 * t
		p23 = p2 * (1 - t) + p3 * t
		p34 = p3 * (1 - t) + p4 * t
		p1223 = p12 * (1 - t) + p23 * t
		p2334 = p23 * (1 - t) + p34 * t
		pb = p1223 * (1 - t) + p2334 * t
		scene_simple_graphic.Line(pa.x, pa.y, pa.z, pb.x, pb.y, pb.z, color, color)
		pa = pb


def setup_teleporter(scn, ground_size:hg.Vector2):
	global authorise_ground_node
	authorise_ground_node = hg.Node()
	trans=hg.Transform()
	authorise_ground_node.AddComponent(trans)
	rb = hg.RigidBody()
	rb.SetCollisionLayer(2)
	rb.SetType(hg.RigidBodyKinematic)
	authorise_ground_node.AddComponent(rb)

	box_col = hg.BoxCollision()
	box_col.SetDimensions(hg.Vector3(ground_size.x, 0.1, ground_size.y))
	box_col.SetMass(0)
	authorise_ground_node.AddComponent(box_col)
	scn.AddNode(authorise_ground_node)

	while authorise_ground_node.GetRigidBody().GetState() == hg.NotReady:
		scn.UpdateAndCommitWaitAll()


def update_camera_teleporter(plus, scn, scene_simple_graphic, world, use_vr, controller):
	global flag_rotate
	pos_start = None
	dir_teleporter = None
	teleporter_activate = False
	rotation = 0
	authorise_movement = False

	if use_vr and controller is not None:

		# --Rotation:
		value = controller.GetValue(hg.InputButton4)
		if abs(value) > 0.5:
			if not flag_rotate:
				if value < 0:
					rotation = -math.radians(rotation_step)
				else:
					rotation = math.radians(rotation_step)
				flag_rotate = True
		elif flag_rotate:
			flag_rotate = False

		# -- Translation:
		if controller.GetValue(hg.InputButton0) != 0 or controller.GetValue(hg.InputButton1) != 0:
			mat_controller = world * controller.GetMatrix(hg.InputDeviceMatrixHead)
			dir_teleporter = mat_controller.GetZ()
			pos_start = mat_controller.GetTranslation()

			teleporter_activate = controller.WasButtonPressed(hg.Button0)
	else:
		if plus.KeyDown(hg.KeyX) or plus.KeyDown(hg.KeyC):
			pos_start = world.GetTranslation()
			dir_teleporter = world.GetZ()
			if plus.KeyPress(hg.KeyC):
				teleporter_activate = True

	if pos_start is not None:
		if pos_start.y < 0:
			return None, rotation

		# -- project point on the ground
		cos_angle = hg.Dot(dir_teleporter, hg.Vector3(dir_teleporter.x, 0, dir_teleporter.z).Normalized())
		cos_angle = min(1.0, max(cos_angle, -1))
		angle = math.acos(cos_angle)
		if dir_teleporter.y < 0:
			angle = -angle

			velocity = 5
			d = ((velocity * cos_angle) / 9.81) * (velocity * math.sin(angle) + math.sqrt(
				(velocity * math.sin(angle)) ** 2 + 2 * 9.81 * pos_start.y))

		else:
			velocity = 5.0
			min_d = ((velocity * 1) / 9.81) * (
					velocity * math.sin(0) + math.sqrt((velocity * math.sin(0)) ** 2 + 2 * 9.81 * pos_start.y))
			max_d = 30
			d = min_d + (1.0 - abs(cos_angle)) * max_d

		# -- find the height from pos
		ground_pos = hg.Vector3(pos_start.x, 0, pos_start.z) + hg.Vector3(dir_teleporter.x, 0,
																		  dir_teleporter.z).Normalized() * d

		hit, trace = scn.GetPhysicSystem().Raycast(ground_pos + hg.Vector3(0, pos_start.y + 0.5, 0),
												   hg.Vector3(0, -1, 0), 4, 5)
		ground_pos.y = 0
		if hit:
			ground_pos.y = trace.GetPosition().y
			color=hg.Color.Green
			authorise_movement = True

			if authorise_ground_node is not None:
				dist = (ground_pos - pos_start).Len()
				f = min(1, dist / 5)
				dir0 = dir_teleporter * f
				n0 = trace.GetNormal() * f

				p1 = pos_start
				p2 = pos_start + dir0
				p3 = ground_pos + n0
				p4 = ground_pos
				#scene_simple_graphic.Line(p1.x, p1.y, p1.z, p2.x, p2.y, p2.z, hg.Color.Red, hg.Color.Red)
				#scene_simple_graphic.Line(p2.x, p2.y, p2.z, p3.x, p3.y, p3.z, hg.Color.Red, hg.Color.Red)
				#scene_simple_graphic.Line(p3.x, p3.y, p3.z, p4.x, p4.y, p4.z, hg.Color.Red, hg.Color.Red)

				draw_curve(scene_simple_graphic, p1, p2,p3, p4, color,50)
				draw_circle(scene_simple_graphic, hg.Matrix4.TranslationMatrix(ground_pos), 1, color)

		# --Get movement:
		if authorise_movement and teleporter_activate:
			if use_vr:
				head_controller = hg.GetInputSystem().GetDevice("HMD")
				head_pos = head_controller.GetMatrix(hg.InputDeviceMatrixHead).GetTranslation()
				head_pos.y = 0
				ground_pos = ground_pos - head_pos
			else:
				ground_pos += hg.Vector3(0, 1.75, 0)

			return ground_pos, rotation

	return None, rotation
