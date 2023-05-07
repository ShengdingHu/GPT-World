import os
import json

env_file = 'environment.json'
env_data = json.loads(open(env_file, 'r').read())


def change_obj(name):
    file = name + '.json'
    
    eid = env_data['objects'][name]['eid']
    location = env_data['objects'][name]['location']
    area_location = env_data['areas'][eid]['location']
    location[0] += area_location[0][0] - 1
    location[1] += area_location[0][1] - 1
    env_data['objects'][name]['location'] = location

    if os.path.exists(file):
        data = json.loads(open(file, 'r').read())
        data['location'] = location
        with open(file, 'w') as output:
            output.write(json.dumps(data))
            output.close()

for obj, info in env_data['objects']:
    change_obj(obj)

with open(env_file, 'w') as output:
    output.write(json.dumps(env_data))
    output.close()