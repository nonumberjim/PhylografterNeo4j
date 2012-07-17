# coding: utf-8
## tree = local_import("tree", reload=True)
## build = local_import("build", reload=True)
## link = local_import("link")
import sys
#sys.path.append('/Users/cbaron/Desktop/web2py/applications/phylografter/modules')
#sys.path.append('/Users/cbaron/Desktop/web2py/applications/phylografter/modules/ivy')
from ivy import tree
import build
import link
import ivy
import treeUtil
import re
import time
import os, types, string
import imp
from tokenize import generate_tokens
from cStringIO import StringIO
from neo4j import GraphDatabase


## ivy = local_import("ivy")

from gluon.storage import Storage

response.subtitle = "Source trees"

def index():
    t = db.stree

    class Virtual(object):
        @virtualsettings(label='Study')
        def study_url(self):
            study = t[self.stree.id].study
            u = URL(c="study",f="view",args=[study.id])
            s = study.citation
            N = 50
            if len(s)>N: s = s[:N-3]+" ..."
            return A(s, _href=u, _title=study.citation)

        @virtualsettings(label='Tree')
        def tree_url(self):
            stree = t[self.stree.id]
            u = URL(c="stree",f="svgView",args=[self.stree.id])
            return A(stree.type, _href=u)

        @virtualsettings(label='Focal Clade')
        def clade(self):
            study = t[self.stree.id].study
            fc = db.study[study].focal_clade
            name = fc.name if fc else ""
            return name
            

        @virtualsettings(label='OTUs')
        def ntax(self):
            q = ((db.snode.tree==self.stree.id)&
                 (db.snode.isleaf==True))
            return db(q).count()

    powerTable = plugins.powerTable
    powerTable.datasource = t
    powerTable.virtualfields = Virtual()
    powerTable.dtfeatures["sScrollY"] = "100%"
    powerTable.dtfeatures["sScrollX"] = "100%"
    #powerTable.virtualfields = Virtual()
    powerTable.headers = "labels"
    powerTable.showkeycolumn = False
    powerTable.dtfeatures["bJQueryUI"] = request.vars.get("jqueryui",True)
    ## powerTable.uitheme = request.vars.get("theme","cupertino")
    powerTable.uitheme = request.vars.get("theme","smoothness")
    powerTable.dtfeatures["iDisplayLength"] = 25
    powerTable.dtfeatures["aaSorting"] = [[6,'desc']]
    powerTable.dtfeatures["sPaginationType"] = request.vars.get(
        "pager","full_numbers"
        ) # two_button scrolling
    powerTable.columns = ["stree.id",
                          "virtual.clade",
                          "virtual.study_url",
                          "virtual.tree_url",
                          "virtual.ntax",
                          ## "stree.contributor",
                          "stree.uploaded"]
    powerTable.hiddencolumns = ["stree.type"]

    ## details = dict(detailscallback=URL(c="stree",f="details"))
    powerTable.extra = dict(autoresize=True)
   
    return dict(table=powerTable.create())

def details():
    return DIV()

def delete():
    i = int(request.args(0) or 0)
    rec = db.stree(i)
    assert rec
    db(db.snode.tree==i).delete()
    rec.delete_record()

def _lookup_taxa(nodes):
    def f(x):
        try: float(x.label or "x"); return False
        except: return True
    v = [ (n.label or "").replace("_", " ") for n in filter(f, nodes) ]
    t = db.taxon
    rows = db(t.name.belongs(v)).select(t.name, t.id)
    return dict([ (x.name, x.id) for x in rows ])

def _study_otus(study):
    q = ((db.otu.study==db.study.id)&(db.study.id==study))
    return db(q).select(db.otu.ALL)

def _insert_stree(study, data):
    ##given form submission data, insert a source tree
    
    """root = ivy.tree.read(data.newick)
    assert root, data.newick
    ivy.tree.index(root)
    nodes = list(root)
    lab2tax = _lookup_taxa(nodes)
    lab2otu = dict([ (x.label, x) for x in _study_otus(study) ])
    stree = db.stree.insert(**data)
    db.stree[stree].update_record(study=study)
    i2n = {}
    for n in nodes:
        label = (n.label or "").replace("_", " ")
        taxid = lab2tax.get(label)
        otu = None
        if n.isleaf:
            otu = lab2otu.get(label)
            if otu and otu.taxon: taxid = otu.taxon
            if not otu:
                otu = db.otu.insert(study=study, label=label, taxon=taxid)

        i = db.snode.insert(label=n.label, isleaf=n.isleaf, otu=otu,
                            next=n.next, back=n.back, depth=n.depth,
                            length=n.length, tree=stree, taxon=taxid,
                            pruned=False)
        n.id = i
        i2n[i] = n
    ##     n.rec = Storage(taxon=taxid)

    ## node2anc, node2desc = link.suggest(db, root)
    ## for n, s in node2anc.items():
    ##     if s:
    ##         taxid = sorted(s)[-1][1]
    ##         db.snode[n.id].update_record(taxon=taxid)

    t = db.snode
    if data.clade_labels_represent == "bootstrap values":
        n2sup = {}
        for n in filter(lambda x: x.children and x.label, nodes):
            try: n2sup[n] = float(n.label)
            except ValueError: pass
        if n2sup:
            m = max(n2sup.values())
            if 1 <= m <= 101:
                for n, sup in n2sup.items(): n2sup[n] = sup/100.
            for n, sup in n2sup.items():
                t[n.id].update_record(bootstrap_support=sup, label=None)

    elif data.clade_labels_represent == "posterior support":
        n2sup = {}
        for n in filter(lambda x: x.children and x.label, nodes):
            try: n2sup[n] = float(n.label)
            except ValueError: pass
        for n, sup in n2sup.items():
            t[n.id].update_record(posterior_support=sup, label=None)
                
    for n in nodes:
        if n.parent:
            t[n.id].update_record(parent=n.parent.id)
        n.label = str(n.id)
        n.length = None
    db.stree[stree].update_record(newick_idstr=root.write())
    return stree"""

    try:
        datey = time.strftime( "%Y%m%d" )
        ##print 'Remember this code for search: ' + datey


        db = GraphDatabase('C:\Documents and Settings\Guest\Desktop\Test')
        ##print 'Your input is ' + data.newick
    except:
        print "Unexpected error:", sys.exc_info()[0]
        raise

    """newickstring = StringIO(data.newick)

    STRING = 1
    stringdata = list(token[STRING] for token
         in generate_tokens(newickstring.readline)
         if token[STRING])

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

    ##print ID

    lp = 0
    rp = 0

    for i in range(0, len(stringdata)):
        if value == '(':
            first+=1
            lp += 1
            with db.transaction:
                newnode = db.node()
                relationship = newnode.has_parent(node)
                ##print node
                node = newnode
                ##print newnode
        elif value == ')':
            rp += 1
            if i==len(stringdata)-1:
                continue
            else:
                check = stringdata[i+1]
                if re.match("^[A-Za-z]*$", check):
                    with db.transaction:
                        for rel in newnode.has_parent.outgoing:
                            ##print node
                            node = rel.end
                            node['label']=check           
                else:
                    with db.transaction:
                        for rel in newnode.has_parent.outgoing:
                            ##print node
                            node = rel.end
                            ##print node
        elif value == ',':
            with db.transaction:
                for rel in node.has_parent.outgoing:
                    node = rel.end
                    ##print node
        elif value == ';':
            break
        elif value == ':':
           ## print stringdata[i+1]
            branchlength = float(stringdata[i+1])
            with db.transaction:
                node['length'] = branchlength
        else:
            try:
                float(value)               
            except ValueError:
                if lp == rp:
                    continue
                elif oldvalue == ')':
                    continue
                else:
                    if first == 1:
                        with db.transaction:
                            node['label']=value
                            ##print node
                            ##print value
                            first += 1
                    else:
                        with db.transaction:
                            newnode = db.node()
                            relationship = newnode.has_parent(node)
                            mynodelist.append(db.node(name=value))
                            newnode['label']=value
                            node = newnode
                            ##print newnode
                            ##print value                
        if i <= len(stringdata)-2:
            nextvalue = stringdata[i+1]
        i+=1
        oldvalue = value
        value = nextvalue"""

    ##db.shutdown()

#@auth.requires_membership('contributor')
@auth.requires_login()

def create():
    study = db.study(request.args(0)) or redirect(URL("index"))
    def w(f,v):
        u = URL(c="study",f="view",args=[study.id])
        return A(_study_rep(study), _href=u)
    db.stree.study.widget = w
    
    fields = ["study", "contributor", "newick",
              "author_contributed",
              "type",
              "clade_labels_represent", "clade_labels_comment",
              "branch_lengths_represent", "branch_lengths_comment",
              "comment"]
    form = SQLFORM(db.stree, fields=fields)
    form.vars.study=int(study)

    name = "%s %s" % (auth.user.first_name, auth.user.last_name)
    form.vars.contributor = name
    ## form.vars.newick = "(a,(b,((c,d),(e,f))));"
    ## form.vars.comment = "test test"
    ## base = "/home/rree/Dropbox/phylografter/private/Jansen-2007-PNAS/"
    ## form.vars.newick = file(base+"Jansen_2007.newick").read()
    ## form.vars.comment = "RAxML bootstrap tree; re-analysis of published data"
    ## form.vars.type = "RAxML 7.2.6 bootstrap"
    
    treestr = ""
    if form.accepts(request.vars, session, dbio=False):
        response.flash ="accepted"
        session.contributor = form.vars.contributor
        i = _insert_stree(study, form.vars)
        redirect(URL("v", args=[i]))

    return dict(form=form)
    
def edit():
    rec = db.stree(request.args(0))
    def w(f,v):
        u = URL(c="study",f="view",args=[v])
        return A(_study_rep(db.study(v)), _href=u)
    db.stree.study.widget = w
    response.subtitle = "Edit source tree %s" % rec.id
    fields = ["study", "contributor", "newick", "type",
              "clade_labels_represent", "clade_labels_comment",
              "branch_lengths_represent", "branch_lengths_comment",
              "comment"]
    readonly = not auth.has_membership(role="contributor")
    form = SQLFORM(db.stree, int(rec), fields=fields, showid=False,
                   deletable=False, submit_button="Update record",
                   readonly=readonly)
    form.vars.study = rec.id
    if form.accepts(request.vars, session):
        response.flash = "record updated"
    return dict(form=form)

def view():
    return dict()

def sunburst():
    i = int(request.args(0))
    if i:
        rec = db.stree(i)
    return dict(rec=rec)

def d3():
    i = int(request.args(0))
    if i:
        rec = db.stree(i)
    return dict(rec=rec)


def svgView():
    i = int(request.args(0))
    if i:
        rec = db.stree(i)
    return dict(rec=rec)

def editOTUs():
    response.title = 'Edit OTUs'
    return dict()

def getNodeInfo():
    i = int(request.vars.nodeId)
    node = db.snode[i]
    color = "black"
    label = node.label or "[%s]" % node.id
    if node.taxon:
        label = node.taxon.name
        color = "green"
    return {'nodeId': node.id, 'label': label, 'labelcolor': color}

def v():
    rec = db.stree(request.args(0) or 0)
    study = db.study(rec.study) 
    u = URL(c="study",f="view",args=[study.id])
    study = A(_study_rep(study), _href=u, _target="_blank")
    wscale = float(request.vars.wscale or 0.9)
    wider = wscale+0.1; narrower = max(0.1, wscale-0.1)
    wider = A("wider", _href=URL(args=request.args,
                                 vars=dict(wscale="%0.1f" % wider)))
    narrower = A("narrower", _href=URL(args=request.args,
                                       vars=dict(wscale="%0.1f" % narrower)))
    
    treeurl = URL(c='stree',f='treediv',args=request.args,vars=request.vars)
    return dict(treeurl=treeurl, wider=wider, narrower=narrower, study=study)

def load_html():
    i = int(request.args(0) or 0)
    root = build.stree(db, i)
    nodes = list(root.iternodes())
    for node in nodes:
        label = node.rec.label or node.label
        if node.rec.taxon:
            label = db.taxon[node.rec.taxon].name
        node.label = label
    def onclick(nid):
        u = URL(c="snode",f="update_snode.load", args=[nid])
        return ("hbranch_clicked(%s, '%s', 'modal', 'modal_content');"
                % (nid, u))
    if auth.has_membership(role="contributor"): f = onclick
    else: f = ""
    div, mapping, w, h = tree.render_html(root, session, request,
                                          db, onclick=f)
    return dict(tree=div)

def treediv():
    i = int(request.args(0) or 0)
    root = build.stree(db, i)
    nodes = list(root.iternodes())
    for node in nodes:
        label = node.rec.label or node.label
        if node.rec.taxon:
            label = db.taxon[node.rec.taxon].name
        node.label = label
    def onclick(nid):
        u = URL(c="snode",f="update_snode.load", args=[nid])
        return ("hbranch_clicked(%s, '%s', 'modal', 'modal_content');"
                % (nid, u))
    if auth.has_membership(role="contributor"): f = onclick
    else: f = ""
    wscale = float(request.vars.wscale or 0.9)
    div, mapping, w, h = tree.render_html(root, session, request,
                                          db, onclick=f,
                                          wscale=wscale)
    return div.xml()

def html():
    i = int(request.args(0) or 0)
    root = build.stree(db, i)
    nodes = list(root.iternodes())
    for node in nodes:
        label = node.rec.label or node.label
        if node.rec.taxon:
            label = db.taxon[node.rec.taxon].name
        node.label = label

    modal = PluginMModal(id="mymodal", title="Edit node properties", content="")
    mid = modal.id; cid = "c"+mid
    def onclick(nid):
        u = URL(c="snode",f="update_snode.load", args=[nid])
        return "hbranch_clicked(%s, '%s', '%s', '%s');" % (nid, u, mid, cid)
    if auth.has_membership(role="contributor"): f = onclick
    else: f = ""
    div, mapping, w, h = tree.render_html(root, session, request,
                                          db, onclick=f)

    return dict(tree=div, root=root, modal=modal, w=w, h=h)


def modalTreeObj():
    return dict( tree = build.stree( db, request.args[0] ) )


def suggest():
    i = int(request.args(0) or 0)
    root = build.stree(db, i)
    
@auth.requires_membership('contributor')
def import_cached_nexml():
    key = "uploaded_nexml_%s" % auth.user.id
    contributor = "%s %s" % (auth.user.first_name, auth.user.last_name)
    ## nexml = cache.ram(key, lambda:None, time_expire=10000)
    nexml = cache.ram(key, lambda:None, time_expire=10000)
    if not nexml:
        session.flash = "Please upload the Nexml file again"
        redirect(URL('study','tbimport'))
    cache.ram(key, lambda:nexml, time_expire=10000)
    get = lambda x: nexml.meta.get(x) or None
    treebase_id = int(get('tb:identifier.study'))
    study = db(db.study.treebase_id==treebase_id).select().first()
    if not study:
        session.flash = 'Study record needed!'
        redirect(URL('study','tbimport2'))
    d = dict([ (x.attrib.id, x) for x in nexml.trees ])
    t = d.get(request.args(0))
    if not t:
        session.flash = 'Cannot find tree in cache'
        redirect(URL('study','tbimport2'))

    ivy.tree.index(t.root)

    for n in t.root.leaves():
        if not n.otu.otu:
            session.flash = 'Leaf node %s lacks OTU record' % (n.label or n.id)
            redirect(URL('study','tbimport2'))

    ## for leaf in t.root.leaves():
    ##     print leaf.__dict__
    ## for k, v in nexml.otus.items():
    ##     print v

    #print t.root.write()
    ## print t.attrib
    
    sdata = dict(study=study.id,
                 contributor=contributor,
                 newick=t.root.write().replace(" ", "_"),
                 author_contributed=True,
                 tb_tree_id=t.attrib.id,
                 type=t.attrib.label)

    for k,v in sdata.items():
        db.stree[k].default=v

    def w(f,v):
        u = URL(c="study",f="view",args=[study.id])
        return A(_study_rep(study), _href=u)
    db.stree.study.widget = w
    db.stree.uploaded.readable=False
    form = SQLFORM(db.stree)
    if form.accepts(request.vars, session):

        bootstraps = {}
        if form.vars.clade_labels_represent == "bootstrap values":
            for n in t.root.iternodes(lambda x: x.children and x.label):
                try: bootstraps[n] = float(n.label)
                except ValueError: pass
            for n in bootstraps:
                n.label = None

        elif form.vars.branch_lengths_represent == "bootstrap values":
            for n in t.root.iternodes(
                lambda x: x.children and x.length is not None):
                try: bootstraps[n] = float(n.label)
                except ValueError: pass
            for n in bootstraps:
                n.length = None

        if bootstraps:
            m = max(bootstraps.values())
            if 1 <= m <= 101:
                for n, sup in bootstraps.items():
                    bootstraps[n] = sup/100.

        posteriors = {}
        if form.vars.clade_labels_represent == "posterior support":
            for n in t.root.iternodes(lambda x: x.children and x.label):
                try: posteriors[n] = float(n.label)
                except ValueError: pass
            for n in posteriors:
                n.label = None

        elif form.vars.branch_lengths_represent == "posterior support":
            for n in t.root.iternodes(
                lambda x: x.children and x.length is not None):
                posteriors[n] = n.length
            for n in posteriors:
                n.length = None

        for d in filter(None, (bootstraps, posteriors)):
            m = max(d.values())
            if 1 <= m <= 101:
                for n, sup in d.items():
                    d[n] = sup/100.

        i2n = {}
        for n in t.root.iternodes():
            taxid = None
            label = n.otu.otu.label if n.isleaf and n.otu.otu else n.label
            if n.isleaf and n.otu.otu and n.otu.otu.taxon:
                taxid = n.otu.otu.taxon
            else:
                taxon = db(db.taxon.name==label).select().first()
                if taxon: taxid=taxon.id

            i = db.snode.insert(label=label,
                                isleaf=n.isleaf,
                                otu=n.otu.otu.id if n.isleaf and n.otu else None,
                                next=n.next, back=n.back, depth=n.depth,
                                length=n.length,
                                bootstrap_support=bootstraps.get(n),
                                posterior_support=posteriors.get(n),
                                tree=form.vars.id,
                                taxon=taxid,
                                pruned=False)
            n.id = i
            i2n[i] = n

        for n in t.root.iternodes():
            if n.parent:
                db.snode[n.id].update_record(parent=n.parent.id)
            n.label = str(n.id)
            n.length = None
        db.stree[form.vars.id].update_record(newick_idstr=t.root.write())

        session.flash = 'tree %s inserted' % t.attrib.id
        redirect(URL('study','tbimport_trees'))

    return dict(study=study, tree=t, form=form)
