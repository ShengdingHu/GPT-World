from gptworld.core.agent import GPTAgent
from datetime import datetime
import openai
import os
import json
from gptworld.models.openai import chat as request

openai.api_key = "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"
openai.api_key_path=None
openai.organization=None
os.environ['OPENAI_METHOD'] = "pool"
## if you want to run this test, run 'query_reflection.py' first

# 科目一
file_dir='unit_test'
file_name='../static_files/test_env0/a_001r.json'
agent_path = os.path.join(file_dir, file_name)
if os.path.exists(agent_path):
    with open(os.path.join(file_dir, file_name), 'r') as f:
        data = json.load(f)
    data['Memory']='test_agent_reflection'
IRagent=GPTAgent(**{"state_dict": data, "agent_file": './static_files/test_env0/a_001r.json','environment':None})

summary=IRagent.generate_summary(datetime.now().replace(microsecond=0))

# 科目二
# observations=request(f'{summary}\n Generate 50 random observations that is closely related to the character from above document. ')
observations="""1. Isabella Rodriguez enjoys hosting dinner parties for her friends and family.
2. She often volunteers at community events to meet new people.
3. Isabella is always willing to lend a listening ear to those in need.
4. She is known for her warm and welcoming personality.
5. Isabella loves to travel and meet new people from different cultures.
6. She values honesty and authenticity in her relationships.
7. Isabella is a great communicator and enjoys meaningful conversations.
8. She enjoys attending social events and meeting new people.
9. Isabella is always willing to help others in any way she can.
10. She enjoys spending time with her loved ones and cherishes those moments.
11. Isabella loves to cook and often shares her recipes with others.
12. She is a great listener and provides thoughtful advice to her friends.
13. Isabella is a loyal friend and values trust in her relationships.
14. She enjoys learning about different perspectives and cultures.
15. Isabella is always up for trying new things and stepping out of her comfort zone.
16. She is passionate about making a positive impact on the world.
17. Isabella values diversity and inclusivity in her relationships.
18. She enjoys spending time outdoors and connecting with nature.
19. Isabella is a great team player and enjoys collaborating with others.
20. She values open-mindedness and encourages others to be themselves.
21. Isabella is always looking for ways to improve herself and her relationships.
22. She enjoys reading and expanding her knowledge on various topics.
23. Isabella is a great problem solver and enjoys finding solutions for others.
24. She values respect and kindness in her relationships.
25. Isabella enjoys attending concerts and music festivals with her friends.
26. She is a great mediator and helps to resolve conflicts between others.
27. Isabella is always looking for ways to give back to her community.
28. She values empathy and understanding in her relationships.
29. Isabella enjoys attending art exhibits and exploring different forms of creativity.
30. She is a great mentor and enjoys helping others reach their goals.
31. Isabella is always willing to learn from others and their experiences.
32. She values integrity and honesty in her relationships.
33. Isabella enjoys practicing yoga and meditation to stay grounded.
34. She is a great motivator and encourages others to pursue their passions.
35. Isabella values patience and understanding in her relationships.
36. She enjoys attending sporting events and cheering on her favorite teams.
37. Isabella is a great listener and provides emotional support to her friends.
38. She values loyalty and dedication in her relationships.
39. Isabella enjoys traveling to new places and experiencing different cultures.
40. She is a great problem solver and enjoys finding creative solutions.
41. Isabella values communication and transparency in her relationships.
42. She enjoys attending book clubs and discussing literature with others.
43. Isabella is a great leader and enjoys guiding others towards success.
44. She values forgiveness and second chances in her relationships.
45. Isabella enjoys attending comedy shows and laughing with her friends.
46. She is a great role model and sets a positive example for others.
47. Isabella values authenticity and genuineness in her relationships.
48. She enjoys attending charity events and supporting important causes.
49. Isabella is a great listener and provides non-judgmental support to her friends.
50. She values growth and personal development in her relationships.
""".split('\n')
for ob in observations:
    IRagent.incoming_observation.append(ob)
    if len(IRagent.incoming_observation)>2:
        IRagent.step(datetime(2023,4,23,9,0,0).replace(microsecond=0))