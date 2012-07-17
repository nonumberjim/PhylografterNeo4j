##purpose of this program is to find the weight of each boy

import os, types, string, sys
import imp
from neo4j import GraphDatabase

db = GraphDatabase('Test')

choose = raw_input('Choose?')
choose = int(choose)
treeNode = db.node[choose]

print 'Tree ID:'
print treeNode

for rel in treeNode.is_root.outgoing:
    childNode = rel.end

def nodeweight:
    global depth
    global leafCount
    weight = depth/leafCount
    if childNode['Label'] is not '':
        weight*= .25
