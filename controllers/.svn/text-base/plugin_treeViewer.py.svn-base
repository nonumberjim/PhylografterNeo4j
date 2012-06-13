build = local_import("build", reload=True)

util = local_import( "plugin_treeViewer", reload = True )

from gluon.storage import Storage


def treeViewer():
    """
    This function handles a request made when plugin_treeViewer is invoked in a view.
    Because the treeViewer plugin is a superclass to the treeGrafter plugin, on the client and server,
    this function routes the request to the tree viewer module where plugins that inherit from the
    tree viewer can use. 

    Currently, there are two ways to instantiate a treeViewer. You can either pass in a treeId and a treeType
    ( 'source', 'grafted' ), or, you can pass in a python tree object.  All of the parameters have not
    been fully fleshed out.

    Load from treeId :

    {{=plugin_treeViewer(
        dict( treeId = request.args(0),
              treeType = 'source',
              eventInfo = dict( labelClick = dict( type = 'getUrlForm', url = str( URL( c='modal', f='editSnodeTaxon' ) ) ),
                                nodeRightClick = dict( type = 'contextMenu', options = [ 'collapseClade', 'addToClipboard' ] ) ),
              viewInfo = dict( mode = 'navigate' ) ) ) }}
    
              
    Load from tree obj :

    {{=plugin_treeViewer( dict( tree = tree, modal = True, viewInfo = dict( mode = 'browse' ) ) ) }}
    """

    return util.handleViewerInstantiation( request, response, session, db )


def getMatchingLabels():

    value = ''.join( [ '%', request.vars.value, '%' ] )

    return response.json( db( ( db.snode.tree == request.vars.treeId ) &
                              ( ( db.snode.label.like( value ) ) |
                                ( db.taxon.name.like( value ) ) ) ).select( db.snode.id, db.snode.label, db.taxon.name, left = db.taxon.on( db.snode.taxon == db.taxon.id ) ).as_list() )


def setTreeViewerHeight():
    """
    When a webpage containing a tree viewer is loaded, the client sends the height of the tree viewer container
    to the server so that it can be referenced when necessary - for example, if the viewer is displaying a large tree
    without scrolling, then this value is needed
    """
    session.TreeViewer.containerHeight = int( request.args[0] )


def updateConfig():
    """This function updates the tree viewer configuration on the server."""

    config = session.TreeViewer.config

    names = request.vars.names.split(',')
    values = request.vars.vals.split(',')

    for i in range ( len( names ) ):
        config[ names[i] ] = values[i]


def getConfig():
    """
    This function returns tree viewer configuration to the client.  You can find the configuration variables
    in the tree viewer module in the setConfig function.
    """

    return response.json( session.TreeViewer.config )


def collapseClade():
    """
    This function handles a collapse clade request

    request.vars : nodeId ( node to be collapsed ),
                   rootId ( clade being refreshed ),
                   collapsedNodeIds ( a list of nodeIds that are already collapsed, if any )
    """

    collapsedNodeIds = [ int( request.vars.nodeId ) ]

    if( len( request.vars.collapsedNodeIds ) ):

        collapsedNodeIds.extend( [ int( id ) for id in request.vars.collapsedNodeIds.split(':') ] )

    ( clade, collapsedNodeRecs ) = util.determineTreeToRender( db, session, request.vars.rootId, collapsedNodeIds )

    return util.getRenderResponseNew( response, session, db, clade, collapsedNodeRecs )

    
def d3ExpandNode():
    """
    This function handles a request to expand a collapsed node in a d3 forced directed view

    request.vars : nodeId ( node to be expanded )
                   groupId ( incremental id to distinguish nodes (not fully fleshed out) )
    """

    clade = build.node2tree( db, request.vars.nodeId, session.TreeViewer.type )
    clade.groupId = request.vars.groupId

    util.autoCollapse( clade, session, db, [ ] )

    return util.getForceDirectedResponse( response, session, clade )


def refreshColumn():
    """This function handles a request to refresh a column - this is called when changes are made to a node

      request.vars : rootId ( clade being refreshed ),
                     collapsedNodeIds ( a list of nodeIds that are already collapsed )
    """
  
    collapsedNodeIds = [ int( id ) for id in request.vars.collapsedNodeIds.split(',') if id != request.vars.nodeId ]
     
    ( clade, collapsedNodeRecs ) = util.determineTreeToRender( db, session, request.vars.rootId, collapsedNodeIds )

    return util.getRenderResponseNew( response, session, db, clade, collapsedNodeRecs )



def navigateToNode():
    """
    This function handles a request to render a particular node
    """
    
    session.TreeViewer.status.keepVisibleNodeIds = [ int( request.vars.nodeId ) ];

    nodeTable = db.snode if session.TreeViewer.type == 'source' else db.gnode
    nodeRec = db( nodeTable.id == request.vars.nodeId ).select()[0]

    session.TreeViewer.status.keepVisibleNodeIds.extend(
        [ rec['id'] for rec in db( ( nodeTable.next < nodeRec.next ) &
                                   ( nodeTable.back > nodeRec.back ) &
                                   ( nodeTable.tree == int( request.vars.treeId ) ) ).select().as_list() ] )

    
    ( clade, collapsedNodeRecs ) = util.determineTreeToRender( db, session, request.vars.nodeId, [ ] )

    return util.getRenderResponseNew( response, session, db, clade, collapsedNodeRecs )

    
    
def verticallyExpandNode():
    """
    This function handles a request to expand a collapsed node in a vertical manner
                          
    request.vars : nodeId ( node to be expanded ),
                   rootId ( clade being refreshed ),
                   collapsedNodeIds ( a list of nodeIds that are already collapsed )
                   keepVisibleNodeIds ( a list of nodeIds that ancestors of the nodeToBeExpanded )
    """

    collapsedNodeIds = [ int( id ) for id in request.vars.collapsedNodeIds.split(',') if id != request.vars.nodeId ]

    session.TreeViewer.status.keepVisibleNodeIds.append( int( request.vars.nodeId ) )
    session.TreeViewer.status.keepVisibleNodeIds.extend( [ int( id ) for id in request.vars.keepVisible.split(',') ] )

    session.TreeViewer.config.maxTips += int( session.TreeViewer.config.maxTips * .5 )
    
    ( clade, collapsedNodeRecs ) = util.determineTreeToRender( db, session, request.vars.rootId, collapsedNodeIds )

    return util.getRenderResponseNew( response, session, db, clade, collapsedNodeRecs )

    

def getClade():
    
    ( clade, collapsedNodeRecs ) = util.determineTreeToRender( db, session, request.vars.nodeId, [ ] )

    return util.getRenderResponseNew( response, session, db, clade, collapsedNodeRecs )


def horizontallyExpandNode():
    """
    This function handles a request to expand a collapsed node in an horizontal manner
    ( in a column to the right of the expanding node )
    """

    ( clade, collapsedNodeRecs ) = util.determineTreeToRender( db, session, request.vars.nodeId, [ ] )

    return util.getRenderResponseNew( response, session, db, clade, collapsedNodeRecs )


def sunburstGetTree():
    """
    This function handles a request for an entire tree.  Right now, sunburst  refers to a plugin view mode where the
    tree is "sunburst" - ( using the d3 javascript library here )
    """    
    
    tree = build.tree( db, request.args[0], session.TreeViewer.type )

    return util.getSunburstResponse( response, session, tree )


def forceDirectedGetTree():
    """
    This function handles a request for an entire tree.  Right now, forceDirected  refers to a plugin view mode where the
    tree is "force directed" - ( using the d3 javascript library here )
    """    
    
    tree = build.tree( db, request.args[0], session.TreeViewer.type )

    tree.groupId = 0

    util.autoCollapse( tree, session, db, [ ] )

    return util.getForceDirectedResponse( response, session, tree )


def isTreePreProcessed():

    rv = 'false'

    if( db( ( db.treeMeta.tree == session.TreeViewer.treeId ) &
            ( db.treeMeta.treeType == session.TreeViewer.type ) ).count() == 1 ):

        rv = 'true'

    return response.json( dict( value = rv ) )


def preProcessTree():
        
    tree = build.tree( db, session.TreeViewer.treeId, session.TreeViewer.type )
    util.gatherTreeInfo( tree, session, db, True )


def navigateGetTree():
    """
    This function handles a request for an entire tree.  Right now, navigate refers to a plugin view mode where the rendered
    tree has collapsed nodes so that fits inside the plugin container
    """

    ( clade, collapsedNodeRecs ) = util.determineTreeToRender( db, session, 'root', [ ] )

    return util.getRenderResponseNew( response, session, db, clade, collapsedNodeRecs )


def browseGetTree():
    """
    This function handles a request for an entire tree.  Browse refers to a plugin view mode where the entire tree is rendered
    and scroll bars will appear if necessary.
    """

    ( clade, collapsedNodeRecs ) = util.determineTreeToRender( db, session, request.args[0], [ ] )

    return util.getRenderResponseNew( response, session, db, clade, collapsedNodeRecs )


def getDescendantLabels():

    nodeTable = db.snode if session.TreeViewer.type == 'source' else db.gnode

    nodeRecord = db( nodeTable.id == request.vars.nodeId ).select().first()

    labels = db( ( nodeTable.tree == session.TreeViewer.treeId ) &
                 ( nodeTable.next > nodeRecord.next ) &
                 ( nodeTable.back < nodeRecord.back ) &
                 ( db.phylogramNodeMeta.nodeId == nodeTable.id ) &
                 ( db.phylogramNodeMeta.treeType == session.TreeViewer.type ) &
                 ( db.phylogramNodeMeta.tree == session.TreeViewer.treeId ) &
                 ( db.phylogramNodeMeta.text != None ) ).select( db.phylogramNodeMeta.text ).as_list()

    return response.json( dict( nodeId = request.vars.nodeId, labels = labels ) )


