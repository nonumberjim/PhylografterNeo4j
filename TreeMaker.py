import os, types, string, sys
import imp
from tokenize import generate_tokens
from cStringIO import StringIO
from neo4j import GraphDatabase
from datetime import datetime, date
import time
import uuid
import re

nowdate = datetime.now()
nowdate = str(nowdate)
print 'Current time: ' + nowdate

datey = time.strftime( "%Y%m%d" )
print 'Remember this code for search: ' + datey

newID = uuid.uuid1()
newID = str(newID)
print newID

db = GraphDatabase('Test')
data = raw_input('Newick String?')
print 'Your input is ' + data

data = StringIO(data)

STRING = 1
stringdata = list(token[STRING] for token
     in generate_tokens(data.readline)
     if token[STRING])

print stringdata

exists = db.node.indexes.exists('tree')

if exists == 0:
    with db.transaction:
        tree_idx = db.node.indexes.create('tree')

elif exists == 1:
    tree_idx = db.node.indexes.get('tree')

##i is counter
i=0
value = stringdata[i]
nextvalue = stringdata[i+1]

##print value
##print nextvalue

first = 0
mynodelist=[]
with db.transaction:
    node = db.node()
    root = db.node(name="Root")
    root['date'] = nowdate  
    root['uID'] = newID
    relationship = root.is_root(node)
    ID = root.id

print ID

lp = 0
rp = 0

for i in range(0, len(stringdata)):
    if value == '(':
        first+=1
        lp += 1
        with db.transaction:
            newnode = db.node()
            relationship = newnode.has_parent(node)
            print node
            node = newnode
            print newnode
    elif value == ')':
        rp += 1
        if i==len(stringdata)-1:
            continue
        else:
            check = stringdata[i+1]
            if re.match("^[A-Za-z]*$", check):
                with db.transaction:
                    for rel in newnode.has_parent.outgoing:
                        print node
                        node = rel.end
                        node['label']=check           
            else:
                with db.transaction:
                    for rel in newnode.has_parent.outgoing:
                        print node
                        node = rel.end
                        print node
    elif value == ',':
        with db.transaction:
            for rel in node.has_parent.outgoing:
                node = rel.end
                print node
    elif value == ';':
        break
    elif value == ':':
        print stringdata[i+1]
        branchlength = float(stringdata[i+1])
        with db.transaction:
            node['length'] = branchlength
    else:
        try:
            print float(value)               
        except ValueError:
            if lp == rp:
                continue
            elif oldvalue == ')':
                continue
            else:
                if first == 1:
                    with db.transaction:
                        node['label']=value
                        print node
                        print value
                        first += 1
                else:
                    with db.transaction:
                        newnode = db.node()
                        relationship = newnode.has_parent(node)
                        mynodelist.append(db.node(name=value))
                        newnode['label']=value
                        node = newnode
                        print newnode
                        print value                
    if i <= len(stringdata)-2:
        nextvalue = stringdata[i+1]
    i+=1
    oldvalue = value
    value = nextvalue

db.shutdown()
