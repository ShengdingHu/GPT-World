import os
import json

exit(0)

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

change_obj('a_001')
change_obj('a_002')
change_obj('o_001')
change_obj('o_002')
change_obj('o_003')
change_obj('o_004')
change_obj('o_005')
change_obj('o_006')
change_obj('o_007')
change_obj('o_008')
change_obj('o_009')

with open(env_file, 'w') as output:
    output.write(json.dumps(env_data))
    output.close()