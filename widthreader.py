import os, types, string, sys
import imp
from neo4j import GraphDatabase


db = GraphDatabase('Test')

choose = raw_input('Choose?')
choose = int(choose)
treeNode = db.node[choose]

##depth = dict(d = 0)
dept = 0

print 'Tree ID:'
print treeNode

for rel in treeNode.is_root.outgoing:
    childNode = rel.end

def width(node, current):
    global dept
    print current
    print dept
    print node
    for rel in node.has_parent.incoming:
        childNode = rel.start
        branchlength = childNode['length']
        branchlength = float(branchlength)
        width(childNode, current+branchlength)
    if current >= dept:
        depth=current

width(childNode, 0)
print 'final answer'
print dept 
db.shutdown 
