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

def move_agent(agent, location, eid):
    env_file = agent.environment.file_dir + 'environment.json'
    agent_file = agent.agent_file

    env_json = json.loads(open(env_file, 'r').read())
    agent_json = json.loads(open(agent_file, 'r').read())
    id = agent.id

    env_json['objects'][id]['location'] = location
    env_json['objects'][id]['eid'] = eid

    agent_json['location'] = location
    agent_json['eid'] = eid

    with open(env_file, 'w') as output:
        output.write(json.dumps(env_json))
        output.close()

    with open(agent_file, 'w') as output:
        output.write(json.dumps(agent_json))
        output.close()

    agent.location = location
    agent.eid = eid
