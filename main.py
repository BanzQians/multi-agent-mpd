import pybullet as p
import pybullet_data
import time
import numpy as np

# initialize the simulation
p.connect(p.GUI) 
# p.connect(p.DIRECT) # no graph
p.setAdditionalSearchPath(pybullet_data.getDataPath())
p.setGravity(0, 0, -9.8)

# set the ground
planeId = p.loadURDF("plane.urdf")

# set agents
agent1_start = [0, -1, 0.5]
agent2_start = [0, 1, 0.5]
agent_orientation= p.getQuaternionFromEuler([0, 0, 0])

# load agents
agent1_id = p.loadURDF("r2d2.urdf", agent1_start, agent_orientation)
agent2_id = p.loadURDF("r2d2.urdf", agent2_start, agent_orientation)

# set up objects
num_objects = 3
object_ids = []
for i in range(num_objects):
    pos = np.random.uniform(low=[-2, -2, 0.5], high=[2, 2, 0.5])
    obj_id = p.loadURDF("cube_small.urdf", pos)
    object_ids.append(obj_id)

# fundamental moving functions
def move_towards(agent_id, target_pos, step_size=0.002):
    pos, _ = p.getBasePositionAndOrientation(agent_id)
    pos = np.array(pos)
    direction = np.array(target_pos) - pos
    norm = np.linalg.norm(direction)
    if norm > step_size:
        direction = direction / norm * step_size
    new_pos = pos + direction
    p.resetBasePositionAndOrientation(agent_id, new_pos.tolist(), agent_orientation)

# each agent pairs with one object(here randomly select)
# agent1_target = p.getBasePositionAndOrientation(object_ids[0][0])
# agent2_target = p.getBasePositionAndOrientation(object_ids[1][0])

agent1_target = p.getBasePositionAndOrientation(object_ids[0])[0]
agent2_target = p.getBasePositionAndOrientation(object_ids[1])[0]


# simulation for a duration
for i in range(1000):
    move_towards(agent1_id, agent1_target)
    move_towards(agent2_id, agent2_target)
    p.stepSimulation()
    time.sleep(1./240)

p.disconnect()