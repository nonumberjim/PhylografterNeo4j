"""
module for building trees of ivy.tree.Nodes from database tables
"""
from ivy.tree import Node
from collections import defaultdict

## def root_taxon(db):
##     "return the root taxon record for taxon table"
##     t = db.taxon
##     q = (t.parent==None)
##     v = db(q).select()
##     assert len(v)==1
##     return v[0]


def node2tree(db, nodeId, type, q=None, lim=0, maxdepth=None):
    if type == 'source':
        rootRec = db( db.snode.id == nodeId ).select()[0]
        return getSClade( db, rootRec, [ ] )
    else:
        #return getGClade( db, i )
        return gnode2tree( db, i, q, lim, maxdepth )

def tree( db, treeId, treeType ):
    if treeType == 'source':
        return getSTree( db, treeId )
    else:
        return getGTree( db, treeId )
   
    
def treeFromRootRow( db, rootRecord, treeType, collapsedNodeRecs ):
    if( treeType == 'source' ):
        return getSClade( db, rootRecord, collapsedNodeRecs )
    else:
        return getGClade( db, rootRecord, collapsedNodeRecs )


def getGClade( db, rootRec, collapsedNodeRecs ):
  
    cladeRoot = None

    parentStack = []

    query = db( ( db.gnode.tree == rootRec.tree ) &
                ( db.gnode.next >= rootRec.next ) &
                ( db.gnode.back <= rootRec.back ) )
    
    for rec in collapsedNodeRecs:
        query=query( ~( ( db.gnode.next > rec['gnode']['next'] ) & ( db.gnode.back < rec['gnode']['back'] ) ) )

    for gnodeRow in query.select( db.gnode.ALL, orderby = db.gnode.next ).as_list():

        node = Node()

        node.id = gnodeRow['id']; node.next = gnodeRow['next']; node.back = gnodeRow['back']
        node.label = gnodeRow['label']; node.depth = len( parentStack ); node.text = node.label


        if( node.next - node.back == 1 ):
            node.isleaf = True

        if( node.next == rootRec.next ):
            cladeRoot = node
            parentStack.append( node )
            continue

        while( node.back > parentStack[ -1 ].back ):
            parentStack.pop() 

        node.parent = parentStack[ -1 ]
        parentStack[ -1 ].add_child( node )
        parentStack.append( node )

    return cladeRoot


def getSClade( db, rootRec, collapsedNodeRecs ):
  
    cladeRoot = None

    parentStack = []

    query = db( ( db.snode.tree == rootRec.tree ) &
                ( db.snode.next >= rootRec.next ) &
                ( db.snode.back <= rootRec.back ) )

    for rec in collapsedNodeRecs:
        query=query( ~( ( db.snode.next > rec['snode']['next'] ) & ( db.snode.back < rec['snode']['back'] ) ) )

    for snodeRow in query.select( db.snode.ALL, db.taxon.ALL, left = db.taxon.on( db.taxon.id == db.snode.taxon ), orderby = db.snode.next ).as_list():

        node = Node()

        node.id = snodeRow['snode']['id']; node.next = snodeRow['snode']['next']; node.back = snodeRow['snode']['back']; node.length = snodeRow['snode']['length']
        node.label = snodeRow['snode']['label']; node.taxon = snodeRow['taxon']['name']; node.depth = len( parentStack ); node.text = node.taxon if node.taxon else node.label

        if( node.next - node.back == 1 ):
            node.isleaf = True

        if( node.next == rootRec.next ):
            cladeRoot = node
            parentStack.append( node )
            continue

        while( node.back > parentStack[ -1 ].back ):
            parentStack.pop() 

        node.parent = parentStack[ -1 ]
        parentStack[ -1 ].add_child( node )
        parentStack.append( node )

    return cladeRoot


def getGTree( db, treeId ):
   
    root = None

    parentStack = []

    for gnodeRow in db( ( db.gnode.tree == treeId ) &
                        ( db.gnode.pruned == False ) ).select( db.gnode.ALL, orderby = db.gnode.next ).as_list():

        node = Node()

        node.id = gnodeRow['id']; node.next = gnodeRow['next']; node.back = gnodeRow['back']
        node.label = gnodeRow['label']; node.depth = len( parentStack )

        if( node.next - node.back == 1 ):
            node.isleaf = True

        if( node.next == 1 ):
            node.isroot = True
            root = node
            parentStack.append( node )
            continue

        while( node.back > parentStack[ -1 ].back ):
            parentStack.pop() 

        parentStack[ -1 ].add_child( node )
        parentStack.append( node )

    return root


def getSTree( db, treeId ):
   
    root = None

    parentStack = []

    for snodeRow in db( db.snode.tree == treeId ).select( db.snode.ALL, db.taxon.ALL, left = db.taxon.on( db.taxon.id == db.snode.taxon ), orderby = db.snode.next ).as_list():

        node = Node()

        node.id = snodeRow['snode']['id']; node.next = snodeRow['snode']['next']; node.back = snodeRow['snode']['back']; node.length = snodeRow['snode']['length']   
        node.label = snodeRow['snode']['label']; node.taxon = snodeRow['taxon']['name']; node.depth = len( parentStack )

        if( node.next - node.back == 1 ):
            node.isleaf = True

        if( node.next == 1 ):
            node.isroot = True
            root = node
            parentStack.append( node )
            continue

        while( node.back > parentStack[ -1 ].back ):
            parentStack.pop() 

        parentStack[ -1 ].add_child( node )
        parentStack.append( node )

    return root


def root_snode(db, tree):
    "return the root snode record for stree id 'tree'"
    t = db.snode
    q = (t.tree==tree)&(t.next==1)
    v = db(q).select()
    assert len(v)==1
    return v[0]

def leaves(t, rec):
    db = t._db
    q = (t.next>rec.next)&(t.back<rec.back)&(t.next==t.back-1)
    return list(db(q).select(orderby=t.next))

def mrca(t, recs):
    db = t._db
    n = min([ x.next for x in recs ])
    b = max([ x.back for x in recs ])
    q = (t.next<n)&(t.back>b)
    return db(q).select(orderby=t.back,limitby=(0,1)).first()

def stree(db, i, lim=0, maxdepth=None):
    "build a tree of ivy.tree.Nodes for db.stree.id==i"
    t = db.snode
    q = t.tree==i
    r = root_snode(db, i)
    root = nextbacktree(db.snode, r.id, q, lim=lim, maxdepth=maxdepth)
    #for n in root:
        #n.label = n.rec.label
    return root

def snode2tree(db, i, q=None, lim=0, maxdepth=None):
    """
    build a tree of ivy.tree.Nodes from root db.snode.id==i,
    filtered by query q
    """
    t = db.snode
    r = t[int(i)]
    if q: q &= (t.tree==r.tree)
    else: q = (t.tree==r.tree)
    root = nextbacktree(db.snode, r.id, q, lim=lim, maxdepth=maxdepth)
    for n in root:
        n.label = n.rec.label
    return root

def gnode2tree(db, i, q=None, lim=0, maxdepth=None):
    """
    build a tree of ivy.tree.Nodes from root db.snode.id==i,
    filtered by query q
    """
    t = db.gnode
    r = t[int(i)]
    if q: q &= (t.tree==r.tree)
    else: q = (t.tree==r.tree) & ( t.pruned==False )
    root = nextbackgtree(db.gnode, r.id, q, lim=lim, maxdepth=maxdepth)
    for n in root:
        n.label = n.rec.label
    return root

## def taxa2tree(db, i, lim=0, maxdepth=None):
##     root = nextbacktree(db.taxon, i, lim=lim, maxdepth=maxdepth)
##     for n in root:
##         n.label = n.rec.name
##     return root

def ncbi2tree(db, i, lim=0, maxdepth=None):
    root = nextbacktree(db.ncbi_taxon, i, lim=lim, maxdepth=maxdepth)
    for n in root:
        n.label = n.rec.name
    return root

def nextbacktree(t, i, q=None, lim=0, maxdepth=None):
    """
    create a tree of ivy.tree.Nodes from table t, with
    records having fields next, back, parent, and depth
    """
    db = t._db
    r = t[int(i)]
    limits = dict(orderby=t.next)
    limits['orderby'] = t.next
    if lim: limits["limitby"] = (0,lim)
    q2 = (t.next>r.next)&(t.back<r.back)
    if maxdepth:
        q2 &= (t.depth <= maxdepth)
    recs = db(q)(q2).select(**limits)
    
    root = Node(); root.isroot = True
    root.rec = r; root.id = r.id; root.next = r.next; root.back = r.back;

    i2n = {}; i2n[r.id] = root
    for r in recs:
        n = Node()
        n.rec = r; n.id = r.id; n.next = r.next; n.back = r.back; n.parent = i2n[r.parent];
        if (((not maxdepth) and (r.next==r.back-1)) or
            (maxdepth and (n.depth == maxdepth))):
            n.isleaf = True
        i2n[r.id] = n
        i2n[r.parent].add_child(n)
    return root

def nextbackgtree(t, i, q=None, lim=0, maxdepth=None):
    """
    create a tree of ivy.tree.Nodes from table t, with
    records having fields next, back, parent, and depth
    """
    db = t._db
    r = t[int(i)]
    limits = dict(orderby=t.next)
    if lim: limits["limitby"] = (0,lim)
    q2 = (t.next>r.next)&(t.back<r.back)
    if maxdepth:
        q2 &= (t.depth <= maxdepth)
    recs = db(q)(q2).select(**limits)
   
    #Node = ivy.tree.Node
    root = Node(); root.isroot = True
    root.rec = r; root.id = r.id; root.next = r.next; root.back = r.back; root.stree = r.stree; root.snode = r.snode 

    i2n = {}; i2n[r.id] = root

    for r in recs:
    
        n = Node()

        if( not hasattr( r, 'id' ) ):
            r = r.gnode

        n.rec = r; n.id = r.id; n.next = r.next; n.back = r.back; n.stree = r.stree; n.snode = r.snode
        if (((not maxdepth) and (r.next==r.back-1)) or
            (maxdepth and (n.depth == maxdepth))):
            n.isleaf = True
        i2n[r.id] = n
        i2n[r.parent].add_child(n)
    return root

def add_child(t, parent, child):
    """
    'parent' and 'child' are assumed to be ivy.tree.Nodes with 'rec'
    attributes
    """
    db = t._db
    
    child_next = parent.back
    
    pass

def prune(t, rec):
    "for a tree table with next, back and parent fields, prune a subtree"
    db = t._db
    assert rec.parent
    parent = t[rec.parent]
    ## children = db(t.parent==parent.id).select(orderby=t.next)

def recurse(table, rec, d=None):
    """
    recursively create a tree of ivy.tree.Nodes from table, with root
    rec, using parent references only
    """
    db = table._db
    isroot = False
    if not d:
        d = defaultdict(list)
        isroot = True
    children = db(table.parent==rec.id).select()
    for c in children:
        recurse(table, c, d)
        d[rec.id].append(c)
    if isroot:
        r = ivy.tree.Node(); r.isroot=True; r.rec = rec
        r.label = rec.name
        def f(n):
            for x in d[n.id]:
                c = ivy.tree.Node(); c.rec = x; c.label = x.name
                n.add_child(c)
                f(c)
        f(r)
        for x in r:
            if not x.children:
                x.isleaf = True
        return r

def gtree(db, i, lim=0, maxdepth=None):
    "build a tree of ivy.tree.Nodes for db.gtree.id==i"
    t = db.gnode
    q = ( t.tree==i ) & ( t.pruned == False )
    r = root_gnode(db, i)
    root = nextbackgtree(db.gnode, r.id, q, lim=lim, maxdepth=maxdepth)
    #for n in root:
        #n.label = n.rec.label
    return root

def root_gnode(db, tree):
    "return the root gnode record for stree id 'tree'"
    t = db.gnode
    q = (t.tree==tree)&(t.next==1)
    v = db(q).select()
    assert len(v)==1
    return v[0]

## def rootpath(table, rec, d=None):
##     db = table._db
##     v = []
##     p = table(rec.parent)
##     while p:
##         v.append(p)
##         p = table(p.parent)
##     return v

def rootpath(t, r, q=None, d=None):
    "return a list of records leading up to record 'r'"
    db = t._db
    q2 = (t.next<r.next)&(t.back>r.back)
    return list(db(q)(q2).select(orderby=~t.next))

## def taxa(db):
##     t = db.taxon
##     root = db(t.next==0).select().first()
##     i2r = dict([ (rec.id, rec) for rec in db(t.id>0).select() ])
##     p2c = defaultdict(list)
##     for i, r in i2r.items():
##         if r.parent:
##             p2c[r.parent].append(i)
##     def build(i):
##         rec = i2r[i]
##         n = ivy.tree.Node()
##         n.id = rec.id; n.rec = rec; n.label = rec.name
##         for j in p2c.get(i) or []:
##             c = build(j)
##             n.add_child(c)
##         return n
##     n = build(root.id)
##     for x in n:
##         if not x.children:
##             x.isleaf = True
##     return n

