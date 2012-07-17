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

##depth
def processNode(node, current, depth):
    ##print current
    ##print depth
    ##print node
    if current>=depth['d'] and not node.has_parent.incoming:            
        depth['d']=current
    for rel in node.has_parent.incoming:
        childNode = rel.start
        processNode(childNode, current+1, depth)

##width       
def width(node, current):
    ##print current
    ##print node
    widthdict = dict(d = 0)
    for rel in node.has_parent.incoming:
        childNode = rel.start
        branchlength = childNode['length']
        branchlength = float(branchlength)
        width(childNode, current+branchlength)
    if current >= widthdict['d']:
        widthdict['d']=current
    print widthdict
    return widthdict
    

def leafReader(node, current):
    depth = 0
    for rel in node.has_parent.incoming:
        childNode = rel.start
        leafReader(childNode, current+1)
    if current >= depth:            
        depth=current
    ##print depth
"""
def desCount(node):
    count = 0
    for rel in node.has_parent.incoming:
        childNode = rel.start
        recursion = desCount(childNode)
        count += 1
    with db.transaction:
        node['desc'] = count
    return count

def leafCount(node):
    count = 0
    leaf = 0
    for rel in node.has_parent.incoming:
        childNode = rel.start
        recursion = leafCount(childNode)
        if len(childNode.has_parent.incoming) == 0:
            count +=1
    with db.transaction:
        node['desc'] = count
    return count
"""

def labelCount(node):
    count = 0
    for rel in node.has_parent.incoming:
        childNode = rel.start
        recursion = labelCount(childNode)
        try:
            if childNode['label']:
                count += 1
        except KeyError:
            pass
    with db.transaction:
        node['desc'] = count
    return count

def leafDist(node):
    new = None
    counter = -1
    for rel in node.has_parent.incoming:
        childNode = rel.start        
        counter = leafDist(childNode)
        if new == None:
            new = counter
        if counter <= new:
            new = counter   
    counter += 1
    with db.transaction:
        node['leafDistance'] = counter
    return counter

def closestLabel(node):
    descendant = dict(closestDescendantLabel = None)
    for rel in node.has_parent.incoming:
        childNode = rel.start
        recursion = closestLabel(childNode)
        try:
            descendant['closestDescendantLabel'] = childNode['label']
        except KeyError:
            with db.transaction:
                childNode['closestlabel'] = recursion['closestDescendantLabel']
            ##print childNode['closestlabel']
    if len(node.has_parent.incoming)==0:
        descendant['closestDescendantLabel'] = node['label']
    ##print descendant
    return descendant

def descendantTips(node):
    count = 0
    for rel in node.has_parent.incoming:
        childNode = rel.start        
        recursion = descendantTips(childNode)
        count = recursion + count
    with db.transaction:
        node['descendantTips'] = count
    print count
    if len(node.has_parent.incoming) == 0:
        return 1
    return count


def weight(node):
    for rel in node.has_parent.incoming:
        childNode = rel.start
        recursion = weight(childNode)
    if len(node.has_parent.incoming) != 0:
        tips = node['descendantTips']
        leaf = node['leafDistance']
        nodeWeight = float(tips/leaf)
        try:
            node['closestlabel']
        except KeyError:
            nodeWeight *= .25
        with db.transaction:
            node['weight']=nodeWeight
        print nodeWeight
        
    

##gets the depth of the tree     
##processNode(childNode, 0, depth)

##gets the longest traversal of branchlength (check)
##width(childNode, 0)

##gets the distance from treenode using bottom-up recursion (works)
leafReader(childNode, 0)

##gets count of number of descendents (works)
##desCount(childNode)

##gets count of number of labeled descendents (works)
labelCount(childNode)

##gets count of number of leaf descendents (works)
##leafCount(childNode)

##gets shortest distance from leaf (works)
leafDist(childNode)

##gets the closest labelled descendant of a given node (fix treemaker)
closestLabel(childNode)

##gets the number of leafs descended from a node (check)
descendantTips(childNode)

##gets the nodeweight of each node (check)
weight(childNode)

db.shutdown()

