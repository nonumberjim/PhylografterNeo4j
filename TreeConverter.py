import os, types, string, sys
import imp
from neo4j import GraphDatabase

db = GraphDatabase('Test')
exists = db.node.indexes.exists('tree')

if exists == 1:
    tree_idx = db.node.indexes.get('tree')
elif exists == 0:
    print 'error'

##this early implementation will search by date
query = raw_input('Query?')
##query = str(query)
hits = tree_idx.query(query)
for item in hits:
    print item
hits.close()

choose = raw_input('Choose?')
choose = int(choose)
treeNode = db.node[choose]

print 'Tree ID:'
print treeNode
with db.transaction:
    for rel in treeNode.is_root.outgoing:
        childNode = rel.end
    

def processNode(node):        
    print node
    with db.transaction:
        for rel in node.has_parent.incoming:
            childNode = rel.start
            return processNode(childNode)

processNode(childNode)
        
db.shutdown()
