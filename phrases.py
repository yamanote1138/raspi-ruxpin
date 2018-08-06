import json

# read config file
with open('phrases.json', 'r') as f:
  phrases = json.load(f)

for key in phrases:
  print key, ' = ', phrases[key] 