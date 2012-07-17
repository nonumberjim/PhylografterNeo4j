import os, types, string, sys
import imp
from neo4j import GraphDatabase


db = GraphDatabase('Test')

choose = raw_input('Choose?')
choose = int(choose)
treeNode = db.node[choose]

depth = dict(d = 0)

print 'Tree ID:'
print treeNode

for rel in treeNode.is_root.outgoing:
    childNode = rel.end

def processNode(node, current, depth):
    ##current +=1
    print current
    print depth
    print node
    if current>=depth['d'] and not node.has_parent.incoming:            
        depth['d']=current
    for rel in node.has_parent.incoming:
        childNode = rel.start
        processNode(childNode, current+1, depth)
        
processNode(childNode, 0, depth)
print depth
        
db.shutdown()

