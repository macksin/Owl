import json

with open('/home/mackson/dev/Owl/.cache/instruct/0.json', 'r') as f:
    a = f.read()
    s = json.loads(a)
print(s)