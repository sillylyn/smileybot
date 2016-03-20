smileydict = {}

with open('list.txt', 'r') as smileylist:
    for line in smileylist:
        smileydict[line.partition(' ')[0]] = line.partition(' ')[2]
