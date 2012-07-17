import os, types, string, sys
import imp
from neo4j import GraphDatabase


db = GraphDatabase('Test')

choose = raw_input('Choose?')
choose = int(choose)
treeNode = db.node[choose]

##dictionaries for all the individual functions
depth = dict(d = 0)
print 'Tree ID:'
print treeNode

for rel in treeNode.is_root.outgoing:
    childNode = rel.end

allNodes = dict()

##width       
def preProcessor(node, current, deepest, nodeinfo):
    nodeinfo[node.id] = dict(weight = 0, counter = -1, longestTraversal = 0, leafDist = 0, closestLabel = '', labelCheck = '', descendantTips = 0, labelCount = 0)    
    depth = 0
    new = 10000000
    for rel in node.has_parent.incoming:
        childNode = rel.start
        
        branchlength = childNode['length']            
        branchlength = float(branchlength)
        recursion = preProcessor(childNode, current+branchlength, deepest+1, nodeinfo)
        if recursion['counter'] <= new:            
            new = recursion['counter']
        nodeinfo[node.id]['descendantTips'] = recursion['descendantTips'] + nodeinfo[node.id]['descendantTips']
        
        try:
            if childNode['label']:
                nodeinfo[node.id]['labelCount'] += 1
        except KeyError:
            pass
        
        if new == None:
            new = nodeinfo[node.id]['counter']
        if nodeinfo[node.id]['counter'] <= new:
            new = nodeinfo[node.id]['counter']

        try:
            nodeinfo[node.id]['closestLabel'] = childNode['label']
        except KeyError:
            nodeinfo[node.id]['labelCheck'] = recursion[node.id]['closestLabel']
            
    nodeinfo[node.id]['counter'] = nodeinfo[node.id]['counter'] + 1
    
    if len(node.has_parent.incoming)==0:
        nodeinfo[node.id]['closestLabel'] = node['label']
        nodeinfo[node.id]['descendantTips'] = 1
        nodeinfo[node.id]['leafDist'] = 1
    else:
        print len(node.has_parent.incoming)
        tips = nodeinfo[node.id]['descendantTips']
        leaf = nodeinfo[node.id]['leafDist']
        nodeWeight = float(tips/leaf)
        if nodeinfo['closestLabel'] != '':
            nodeWeight *= .25
        nodeinfo[node.id]['weight']=nodeWeight
        

    if current >= nodeinfo[node.id]['longestTraversal']:
        nodeinfo[node.id]['longestTraversal']=current
    if deepest >= depth:            
        depth=deepest
    print nodeinfo
    return nodeinfo[node.id]

def writeDatabase(node, nodeinfo)
    for rel in node.has_parent.incoming:
        childNode = rel.start
        recursion = writeDatabase(childNode, nodeinfo)
    with db.transaction:
        node['descendantLabel'] = nodeinfo[node.id]['labelCount']
        node['leafDistance'] = nodeinfo[node.id]['leafDist']
        node['descendantTips'] = nodeinfo[node.id]['descendantTips']
        try:
            childNode['closestLabel'] = nodeinfo[node.id]['labelCheck']
        except KeyError:
            pass
        

    

##gets the longest traversal of branchlength (check)
preProcessor(childNode, 0, 0, allNodes)

print nodeinfo
writeDatabase(childNode, nodeinfo)
                  
db.shutdown()

