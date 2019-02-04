# -*-coding:Utf-8 -*

# ===========================================================

#              - HARFANG® 3D - www.harfang3d.com

#                    - Python tutorial -

#						VR setup

# ===========================================================

import harfang as hg

# load all plugin for harfang, like VR plugin
hg.LoadPlugins()

# Get Plus, which is Harfang high level api
plus = hg.GetPlus()

# activate the multi-threading
plus.CreateWorkers()

# mount the system file driver
hg.MountFileDriver(hg.StdFileDriver("assets"), "@assets")

# create a windows or resolution 800*600 with antialiasing set to 4
plus.RenderInit(800, 600, 4, hg.Windowed)

# add a new scene, which is a container of all objects you want to draw/update
scn = plus.NewScene()

# add light
plus.AddLight(scn, hg.Matrix4.TranslationMatrix(hg.Vector3(4, 4, -4)))

# add camera to the sene (to actually see something)
cam = plus.AddCamera(scn, hg.Matrix4.Identity)
scn.SetCurrentCamera(cam)

# add some objects in the scene
plus.AddPlane(scn, hg.Matrix4.Identity)
plus.AddCube(scn, hg.Matrix4.TranslationMatrix(hg.Vector3(0, 1, 2)), 0.5, 0.5, 0.5)
plus.AddCube(scn, hg.Matrix4.TranslationMatrix(hg.Vector3(0, 1, -2)), 0.5, 0.5, 0.5)
plus.AddSphere(scn, hg.Matrix4.TranslationMatrix(hg.Vector3(2, 1, 0)), 0.25)
plus.AddSphere(scn, hg.Matrix4.TranslationMatrix(hg.Vector3(-2, 1, 0)), 0.25)

# check if there is VR available and Initialise the frame renderer
try:
    openvr_frame_renderer = hg.CreateFrameRenderer("VR")
    # we have the vr frame renderer
    # Initialize it to open steamVR
    if openvr_frame_renderer.Initialize(plus.GetRenderSystem()):
        # add the new frame renderer to the scene.
        # the scene will automatically use it to render the scene.
        scn.GetRenderableSystem().SetFrameRenderer(openvr_frame_renderer)
        print("!! Use VR")
    else:
        openvr_frame_renderer = None
        print("!! No VR detected")
except:
    print("!! No VR detected")
    openvr_frame_renderer = None

# load geometry for the controllers
controller_nodes = []
for i in range(2):
    controller_nodes.append(plus.AddGeometry(scn, "@assets/vr_controller_low/whole_model_group1.geo"))

# add little sphere to show where the thumb is touching the tactil surface
sphere_touch_nodes = []
for i in range(2):
    sphere_touch_nodes.append(plus.AddSphere(scn, hg.Matrix4.Identity, 0.001))

# make sure everything is loaded
scn.UpdateAndCommitWaitAll()

# main loop
while not plus.IsAppEnded():
    # second pass between frame
    dt_sec = plus.UpdateClock()
    # The VR renderer don't render the frame from the camera matrix, but instead add the offset between the helmet matrix and the calibration position to the camera matrix
    # in real
    #      # headset position
    #     /
    #    /
    #   /
    #  # calibration center   (which is the position of the camera)

    # In the scene:     camera mat = calibration center
    # for the rendering: rendering camera = camera mat + headset mat

    # update the position of the controllers
    for i in range(2):
        # get the controller from the input system
        try:
            controller = hg.GetInputSystem().GetDevice("VR Controller {0}".format(i))
        except:
            controller = None
        try:
            # make sure we have a controller and the nodes
            if controller is not None and controller_nodes[i].GetTransform() is not None and sphere_touch_nodes[
                i].GetTransform() is not None:
                # compute the world matrix of the controller from the position of the camera and the position of the controller in real
                cam_matrix = scn.GetCurrentCamera().GetTransform().GetWorld()
                controller_mat = controller.GetMatrix(hg.InputDeviceMatrixHead)
                virtual_controller_mat = cam_matrix * controller_mat
                controller_nodes[i].GetTransform().SetWorld(virtual_controller_mat)

                # get tactile surface values
                x_val = controller.GetValue(hg.InputButton0)
                y_val = controller.GetValue(hg.InputButton1)
                if x_val == 0 and y_val == 0:
                    mat = hg.Matrix4.TranslationMatrix(hg.Vector3(0, -500, 0))
                else:
                    mat = hg.Matrix4.TranslationMatrix(hg.Vector3(0, 0.0053, -0.049)) * hg.Matrix4.RotationMatrix(
                        hg.Vector3(-6.0 * 3.1415 / 180.0, 0, 0)) * hg.Matrix4.TranslationMatrix(
                        hg.Vector3(x_val * 0.02, 0, y_val * 0.02))
                sphere_touch_nodes[i].GetTransform().SetWorld(virtual_controller_mat * mat)
        except:
            pass

    # plus update the scene, call all the components update and render the VR system
    plus.UpdateScene(scn, dt_sec)

    # the frame is finish, flip de buffer and finish some internal update, like the input system
    plus.Flip()
    plus.EndFrame()

plus.RenderUninit()

