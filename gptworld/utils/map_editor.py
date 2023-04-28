import os
import json

def find_area(pos, areas):
    for eid, area in areas:
        x0 = area['location'][0][0]
        y0 = area['location'][0][1]
        x1 = area['location'][1][0]
        y1 = area['location'][1][1]

        if x0 <= pos[0] <= x1 and y0 <= pos[1] <= y1:
            return eid, pos[0] - x0 + 1, pos[1] - x1 + 1

    assert False

def move_agent(agent, pos):
    env_file = agent.file_dir + 'environment.json'
    agent_file = agent.agent_file

    print(env_file)
    print(agent_file)
    assert 0

    env_json = json.loads(open(env_file, 'r').read())
    agent_json = json.loads(open(agent_file, 'r').read())
    id = agent.id

    areas = env_json['areas']
    new_eid, new_pos = find_area(pos, areas)

    env_json['object'][id]['eid'] = new_eid
    env_json['object'][id]['location'] = new_pos

    agent_json['eid'] = new_eid
    agent_json['location'] = new_pos

    with open(env_file, 'w') as output:
        output.write(env_json.dumps())
        output.close()

    with open(agent_file, 'w') as output:
        output.write(agent_json.dumps())
        output.close()
