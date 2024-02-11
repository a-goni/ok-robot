![Intro Figure](https://drive.google.com/uc?export=view&id=1IAyAMZS__gcZmsZevQyeETLU369a0n9X)
# Ok-Robot

[<u>Project Website</u>](https://ok-robot.github.io/) . [<u>Paper</u>](https://arxiv.org/abs/2401.12202)

**Authors List**: [<u>Peiqi Liu</u>](https://leo20021210.github.io/), [<u>Yaswanth Orru</u>](https://www.linkedin.com/in/yaswanth-orru/), [<u>Jay Vakil</u>](https://www.linkedin.com/in/jdvakil/), [<u>Chris Paxton</u>](https://cpaxton.github.io/), [<u>Mahi Shafiuallah</u>](https://mahis.life/), [<u>Lerrel Pinto</u>](https://www.lerrelpinto.com/) 

Ok-Robot is a framework that combines the state-of-art navigation and manipualtion models in a intelligent way to design a modular system that can effectively perform pick and place tasks in real homes. It has been tested in 10 real homes on 170+ objects and achieved a total success rate of 58%. 

<details open>
  <summary>ok-robot.mp4</summary>
  
  <!-- Your embedded video code goes here -->
  <iframe width="560" height="315" src="https://drive.google.com/file/d/1IC_wUHmnvq_Aon-fKdiNUNRawQC3patP/view?usp=sharing" frameborder="0" allowfullscreen></iframe>
</details>

## Hardware and software requirements
Hardware required:
* iPhone with Lidar sensors
* Stretch robot with Dex Wrist installed
* A workstation machine to run pretrained models 
  
Software required:
* Python 3.9
* Record3D (installed on iPhone) [has to mention the version]

## Clone this repository to your local machine
```
git clone https://github.com/NYU-robot-learning/home-engine
cd home-engine
git checkout peiqi
```

## Workspace Installation and Setup
Install [Mamba](https://mamba.readthedocs.io/en/latest/installation/mamba-installation.html) if it is not present 

### CUDA 12.*
```
# Environment creation
mamba env create -n ok-robot-env -f ./env-cu121.yml
mamba activate ok-robot-env

# Pointnet setup for anygrasp
cd anygrasp/pointnet2/
python setup.py install
cd ../../

# Additional pip packages isntallation
pip install -r requirements-cu121.txt
pip install --upgrade --no-deps --force-reinstall scikit-learn==1.4.0 
pip install torch_cluster -f https://data.pyg.org/whl/torch-2.1.0+cu121.html 
pip install graspnetAPI

```

### CUDA 11.*
```
mamba env create -n ok-robot-env -f ./env-cu118.yml
mamba activate ok-robot-env

pip install --upgrade --no-deps --force-reinstall scikit-learn==1.4.0
pip install graspnetAPI

# Setup poincept
cd anygrasp/pointnet2/
python setup.py install
```

## Anygrasp Setup
Please refer licence [readme](/anygrasp/license_registration/README.md) for detailed information on how to get the anygrasp license. After completing the necessary steps you will receive the license and checkpoint.tar through email.

Once you receive these files
* Received license folder should be renamed to `license` and place in anygrasp/src/ directory.
* Move the checkpoint.tar into the anygrasp/src/checkpoints/ directory.

## Installation Verification

Run `/Navigation/path_planning.py` file and set debug be True. If run succesfully, the process will load the semantic memory from record3D file, and you should see a prompt asking to enter A. Enter a object name and you should see a 2d map of the scene with the object localised with a green dot in visualization folder, by default it is `Navigation/test/{object_name}`. 
```
python path_planning.py debug=True
cd ../
```

Then verify the grasping module. It should ask prompts for task [pick/place] and object of interest. You can view in scene image in `/anygrasp/src/example_data/ptest_rgb.png`. Choose a object from the scene and you can see visualizations showing a grasp around the object for pick and a green disk showing the area it want to place. [If you face any memory issues try reducing the sampling rate to 0.2 in `anygrasp/src/demo.py`]
```
cd anygrasp/src
python demo.py --debug 
# run in debug mode to see 3D Manipulation Visualisations. If you are running remotely its better to avoid this option
```

## Robot Installation and Setup
**Home Robot Instatallation:** Follow the [home-robot installation instructions](https://github.com/leo20021210/home-robot/blob/main/docs/install_robot.md) to install home-robot on your Stretch robot.

**Copy Hab Stretch Folder:** Copy hab stretch folder from [home robot repo](https://github.com/facebookresearch/home-robot/tree/main/assets/hab_stretch) 
```
cd $OK-Robot/
cp home-robot/assets/hab_stretch/ grasperNet
```

**New calibrated URDF:** If you already have a calibrated urdf these steps can be skipped. 

* Follow [home-robot calibration instructions](https://github.com/hello-robot/stretch_ros/blob/noetic/stretch_description/README.md#changing-the-tool) to create a new calibrated urdf for your robot.

* Ensure the generated urdf has `wrist_roll` and `wrist_pitch` joints. If not, follow these documentations for [re1](https://docs.hello-robot.com/0.2/stretch-hardware-guides/docs/dex_wrist_guide_re1/) and [re2](https://docs.hello-robot.com/0.2/stretch-hardware-guides/docs/dex_wrist_guide_re2/) hello stretch for installating a dex wrist on the robot. 

* Once you have a proper urdf add the following link and joint to the urdf
```
<link name="fake_link_x">
    <inertial>
      <origin rpy="0.0 0.0 0." xyz="0. 0. 0."/>
      <mass value="0.749143203376"/>
      <inertia ixx="0.0709854511955" ixy="-0.00433428742758" ixz="-0.000186110788698" iyy="0.000437922053343" iyz="-0.00288788257713" izz="0.0711048085017"/>
    </inertial>
  </link>
  <joint name="joint_fake" type="prismatic">
    <origin rpy="0. 0. 0." xyz="0. 0. 0."/>
    <axis xyz="1.0 0.0 0.0"/>
    <parent link="base_link"/>
    <child link="fake_link_x"/>
    <limit effort="100.0" lower="-1.0" upper="1.1" velocity="1.0"/>
  </joint>
```

* Also, modify the `parent link` of `joint_mast` joint from `base_link` to `fake_link_x`. The joint should finally look like this
```
<joint name="joint_mast" type="fixed">
    <origin xyz="-0.06886239813360509 0.13725755297906447 0.025143215009302215" rpy="1.5725304449603004 0.0027932103811125764 0.013336895699597295"/>
    <axis xyz="0.0 0.0 0.0"/>
    <parent link="fake_link_x"/>
    <child link="link_mast"/>
  </joint>
```

**URDF Location:** After that replace the strech_manip_mode.urdf in `graspernet/hab_stretch/urdf/` directory with this new calibrated urdf.

## Experiment Setup
**Environment Setup:** Use Record3D to scan the environments. Recording should include: 
* All Obstacles in environments
* Complete floor where the robots can navigate
* All testing objects.
* Two tapes in the scene which will serve as a orgin for the robot.

**Tape Placement:** This [drive folder](https://drive.google.com/drive/folders/1qbY5OJDktrD27bDZpar9xECoh-gsP-Rw?usp=sharing) has illustrations on how to place tapes on the ground and scan the environment properly.

**Scan the Environment:** After positioning the objects and tapes, proceed to scan the environment and save the Record3D r3d file in the `navigation/r3d/` folder. If you just want to try out a sample r3d file, you can use `navigation/r3d/sample.r3d`.

**Extract PointCloud:** Then, use the `navigation/get_point_cloud.py` script to extract the pointcloud of the scene, which will be stored as `navigation/pointcloud.ply`. 
```
python get_point_cloud.py --input_file=[your r3d file]
```
**Identify Tape Co-ordinates** Use a 3D Visualizer to determine the coordinates of the two orange tapes in the environment. Let the co-ordinates of these tapes are (x1, y1) for the first tape(tape1) and (x2, y2) for the second tape(tape2).

**Robot Base Placement** Position the robot's base on tape1 and orient it towards tape2 as shown in the [image](https://drive.google.com/drive/folders/1qbY5OJDktrD27bDZpar9xECoh-gsP-Rw). Make sure the position and rotation of the robot as accurate as possible as it is crucial for the experiments to run properly. 

We recommend using CloudCompare to localize coordinates of tapes. See the [google drive folder above](https://drive.google.com/drive/folders/1qbY5OJDktrD27bDZpar9xECoh-gsP-Rw?usp=sharing) to see how to use CloudCompare.

<!--## Load voxel map 
Once you setup the environment run voxel map with your r3d file which will save the semantic information of 3D Scene in `Navigation/voxel-map` directory. 
```
cd navigation/voxel-map
python load_voxel_map.py dataset_path=[your r3d file location]
```
You can check other config settings in `navigation/voxel-map/configs/train.yaml`.

After this process finishes, you can see the semantic map in the path specified by `cache_path` in `navigation/voxel-map/configs/train.yaml`-->
<!-- ## Config files `navigation/configs/path.yaml` 
* **sample_freq** - sampling frequency of frames while training voxel map
* **min_height** - z co-ordinate value below which everything is not considered as obstacles. Ideally you should choose a point on the floor of the scene and set this value slightly more than that [+ 0.1].
* **max_height** - z co-ordiante of the scene above which everything is not considered as obstacles.
* **map_type** - "conservative_vlmap" (space not scanned is non-navigable) "brave_vlmap" (sapce scanned is navigable, used when you forget to scan the floor)
* **port_number** - zmq communication port, need to the the same with robot's navigation port number
* **save_file** - planned path and generated localization results will be saved here -->

## Running experiments
<!-- Once the above config filesa reset you can start running experiments -->
Scan the environments with Record3D, follow steps mentioned above in Environment Setup and Load Voxel map to load semantic map and obstacle map. Move the robot to the starting point specified by the tapes or other labels marked on the ground.

**Start home-robot on the Stretch**:
```
roslaunch home_robot_hw startup_stretch_hector_slam.launch
```

Navigation planning (See `navigation/configs/path.yaml` for any config settings):
```
mamba activate ok-robot-env

cd navigation
python path_planning.py debug=False
```

**Pose estimation:**
More details can be found in Manipulation [ReadME](./anygrasp/README.md)
```
mamba activate ok-robot-env

cd anygrasp/src/
python demo.py --debug
```

**Robot control:**
More details can be found in graspernet [ReadME](./graspernet/README.md)
```
python run.py -x1 [x1] -y1 [y1] -x2 [x2] -y2 [y2] -ip [your workstation ip]
```

