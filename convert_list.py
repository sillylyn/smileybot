import json

list = {}
with open('list.txt', 'r') as smileylist:
    for line in smileylist:
        if len(line.split()) == 2:
            list[line.split()[0]] = {'url':line.split()[1].rstrip('\n'), 'count': '0'}
with open('list.json','w') as imagelist:
    json.dump(list, imagelist)