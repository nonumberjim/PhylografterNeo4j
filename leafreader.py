import os, types, string, sys
import imp
from neo4j import GraphDatabase

db = GraphDatabase('Test')

choose = raw_input('Choose?')
choose = int(choose)
treeNode = db.node[choose]

antidepth = dict(d = 0)

print 'Tree ID:'
print treeNode

for rel in treeNode.is_root.outgoing:
    childNode = rel.end


def leafreader(node, current, antidepth):
    for rel in node.has_parent.incoming:
        childNode = rel.start
        leafreader(childNode, current+1, antidepth)
    if current >= depth['d'] and not node.has_parent.incoming:            
        antidepth['d']=current

leafreader(childNode, 0, antidepth)
print antidepth

db.shutdown()
