tree = local_import("tree", reload=True)
build = local_import("build", reload=True)
util = local_import( "plugin_treeViewer", reload = True )

def index():
    return dict()

def update_snode():
    t = db.snode
    rec = t(int(request.args(0) or 0))
    w = SQLFORM.widgets.autocomplete(
        request, db.taxon.name, id_field=db.taxon.id
        )
    t.taxon.widget = w

    ## w = SQLFORM.widgets.autocomplete(
    ##     request, db.taxon.name, id_field=db.taxon.id,
    ##     keyword='_ac2_%(fieldname)s'        
    ##     )
    ## t.exemplar.widget = w

    d = dict()
    
    needToProcess = False

    for k,v in request.vars.items():
        if k in t.fields:
            d[k] = v
        if( ( k == 'label' ) or ( k == 'taxon' ) or ( k == 'length' ) ):
            needToProcess = True

    #d = dict([ (k, v) for k, v in request.vars.items()
               #if k in t.fields ])

    if d:
        rec.update_record(**d)

    if( needToProcess ):
        tree = build.tree( db, session.TreeViewer.treeId, session.TreeViewer.type )
        util.gatherTreeInfo( tree, session, db )

    form = SQLFORM(t, rec, showid=False, _id="updateform",
                   _action=URL(c="snode",f="update_snode.load",args=[rec.id]))

    ## if form.accepts(request):
    ##     pass

    return dict(form=form)

def editSnodeTaxon():
    t = db.snode
    rec = t( int(request.args(0)) )
    w = SQLFORM.widgets.autocomplete(
        request, db.taxon.name, id_field=db.taxon.id
        )
    t.taxon.widget = w

    d = dict([ (k, v) for k, v in request.vars.items()
               if k in t.fields ])
    if d:
        rec.update_record(**d)

    form = SQLFORM(t, rec, fields=["label","taxon"], showid=False, _id="updateForm",
                   _action=URL(c="snode", f="editSnodeTaxon.load", args=[rec.id]))

    return dict(form=form)


def get_label_html():
    t = db.snode
    rec = t(int(request.args(0) or 0))
    label = rec.label
    if rec.taxon:
        label = db.taxon[rec.taxon].name
    u = URL(c="snode",f="update_snode.load", args=[rec.id])
    onclick = "hbranch_clicked(%s, '%s', 'mymodal', 'cmymodal');" % (rec.id, u)
    e = SPAN(A(label, _onclick=onclick), _style="background-color:yellow")
    return e#.xml()#dict(html=e.xml(), width=len(label))

    
def get_node_html():
    t = db.snode
    rec = t(int(request.args(0) or 0))
    root = build.stree(db, rec.tree)
    node = root[rec.id]
    if node.rec.taxon:
        label = db.taxon[node.rec.taxon].name
    node.label = label
    def onclick(nid):
        u = URL(c="snode",f="update_snode.load", args=[nid])
        return ("hbranch_clicked(%s, '%s', 'mymodal', 'cmymodal');"
                % (nid, u,mid,cid))
    width, height, style = tree.style_nodes(root, wscale=0.9)
    div = tree.render_node_html(node, style, onclick, session)
    return div.xml()
    
