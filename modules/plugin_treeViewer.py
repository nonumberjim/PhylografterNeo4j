import plugin_common as common
import build as build
import forceDirected
reload( forceDirected )
import sunburst
reload( sunburst )
import math

from gluon.storage import Storage
from types import *

def handleViewerInstantiation( request, response, session, db ):
    """
    This function handles a viewer instantiation request.  This is not fully fleshed out - more details to come.
    In controllers/plugin_treeViewer.py, def treeViewer, can provide more information as well.
    """
    
    viewInfo = common.evaluate( request.vars.viewInfo )

    initializeConfig( session, viewInfo, request ) 

    instanceParams = dict( containerId = request.cid, treeType = session.TreeViewer.type )

    if( request.vars.tree ):

        tree = session.treeViewerTree

        if( viewInfo['mode'] == 'navigate' ):

            autoCollapse( tree, session, db, [ ] )
    
        instanceParams['renderInfo'] = getRenderResponse( response, session, session.treeViewerTree, db )

    elif( request.vars.treeId ):
        
        instanceParams['treeId'] = session.TreeViewer.treeId = request.vars.treeId

    dbNodeTable = db.snode if session.TreeViewer.type == 'source' else db.gnode
    session.TreeViewer.strNodeTable = 'snode' if session.TreeViewer.type == 'source' else 'gnode'

    instanceParams[ 'allNodesHaveLength' ] = True if db( ( dbNodeTable.tree == request.vars.treeId ) &
                                                         ( dbNodeTable.next != 1 ) &
                                                         ( dbNodeTable.length == None ) ).count() == 0 else False
       

    for param in [ 'eventInfo', 'viewInfo', 'menuInfo' ]:
        if( param in request.vars ):
            instanceParams[ param ] = session.TreeViewer.viewInfo = common.evaluate( request.vars[ param ] )

    for param in [ 'auxPlugins' ]:
        if( param in request.vars ):
            if( type( request.vars[ param ] ) is ListType ):
                instanceParams[ param ] = [ common.evaluate( strDict ) for strDict in request.vars[ param ] ]
            else:
                instanceParams[ param ] = [ common.evaluate( request.vars[ param ] ) ]

    
    for param in [ 'modal' ]:
        if( param in request.vars ):
            instanceParams[ param ] = request.vars[ param ]

    return dict( instanceParams = response.json( instanceParams ) )


def initializeConfig( session, viewInfo, request ):
    """
    This function is called when a tree viewer is instantiated - it sets default configuration settings in the session
    """

    renderType = viewInfo['renderType'] if 'renderType' in viewInfo else 'phylogram'
    
    session.TreeViewer = Storage( status = Storage( keepVisibleNodeIds = [ ] ),
                                  type = 'grafted' if( request.vars.treeType == 'grafted' ) else 'source' )

    session.TreeViewer.config = Storage( Storage( fontFamily = 'Verdana', fontSize = 12 ).items() + globals()[''.join( [ renderType, 'Config' ] ) ]( session ).items() )



def phylogramConfig( session ):
    """
    This function returns the 'phylogram' renderType default config.  'phylogram' is a little of a misnomer,
    its simply the initial way this application rendered a tree using svg and raphael.js
    """

    config = Storage( verticalTipBuffer = 20,
                      branchLength = 20,
                      branchLengthStyle = 'smooth',
                      scaledBranchMultiplier = 0,
                      maxTips = 50,
                      verticalPadding = 50,
                      horizontalPadding = 50,
                      tipLabelBuffer = 5,
                      treeColor = 'black',
                      pathWidth = 3,
                      collapsedCladeColor = 'grey',
                      nonTipLabelBuffer = -5,
                      nodeSelectorRadius = 5,
                      nodeSelectorColor = 'blue' )

    if( session.TreeViewer.type == 'grafted' ):

        config.primaryShowEditColor = 'red'
        config.secondaryShowEditColor = 'blue'
        config.tertiaryShowEditColor = 'yellow'

    return config

def d3Config():
    """
    This function returns the 'd3' renderType default config.  
    """

    return Storage( verticalTipBuffer = 20,
                    branchLength = 10,
                    verticalPadding = 100,
                    horizontalPadding = 100,
                    tipLabelBuffer = 5,
                    branchColor = 'black',
                    branchWidth = 3,
                    collapsedCladeColor = 'white' )


def needsCollapsing( clade, session, renderType ): 
    """
    This function returns True or False depending on whether the given clade needs to have nodes collapsed in
    order to fit inside the plugin container.

    Should maybe add an optional height parameter rather than always use the containerHeight session variable.
    """ 
   
    if( 'meta' not in clade ):
        gatherTreeInfo( clade, session, db )

    config = session.TreeViewer.config

    if( renderType == 'forceDirected' ):

        return True if( ( session.TreeViewer.containerHeight ) <
                        ( ( config.verticalPadding * 2 ) + ( config.verticalTipBuffer * clade.meta.tips ) ) ) else False

    else:

        return True if( ( session.TreeViewer.containerHeight - session.scrollbarWidth ) <
                        ( ( config.verticalPadding * 2 ) + ( float( config.verticalTipBuffer ) * clade.meta.tips ) ) ) else False



def determineCollapsedNodes( nodeInfo, tableName, curTips, collapsedNodeInfo, keepVisible, maxTips ):
    """
    This function returns an array of node ids to be collapsed.
    """

    import sys

    for infoRec in nodeInfo:

        nodeId = infoRec[ tableName ]['id']

        if( nodeId not in keepVisible ):

            toCollapse = True
            for colNode in collapsedNodeInfo:

                if( colNode[ tableName ]['id'] == nodeId ):
                    toCollapse = False
                    break

                if( isAncestor( Storage( next = colNode[ tableName ]['next'], back = colNode[ tableName ]['back'] ),
                                Storage( next = infoRec[ tableName ]['next'], back = infoRec[ tableName ]['back'] ) ) ):
                    toCollapse = False
                    break

            if( toCollapse ):

                previouslyCollapsedTips = collapsedDescendantsTipCount( infoRec, tableName, collapsedNodeInfo )
                curTips = curTips - infoRec['phylogramNodeMeta']['descendantTipCount'] + previouslyCollapsedTips
                
                collapsedNodeInfo.append( infoRec )

                if( previouslyCollapsedTips == 0 ):
                    curTips += 1
                
                if( curTips <= maxTips ):
                    break;

    return collapsedNodeInfo

 
def collapsedDescendantsTipCount( nodeInfoRec, tableName, collapsedNodes ):
    """
    This is a helper function used by the determineCollapsedNodes function.
    It returns the number of tips already collapsed by nodes that are descendants of the
    passed in parameter nodeId.
    """

    collapsedDescendantsTipCount = 0

    for collapsedNodeRec in collapsedNodes:
       
        if( ( nodeInfoRec[ tableName ]['next'] < collapsedNodeRec[ tableName ]['next'] ) and
            ( nodeInfoRec[ tableName ]['back'] > collapsedNodeRec[ tableName ]['back'] ) ):
            collapsedDescendantsTipCount += collapsedNodeRec['phylogramNodeMeta']['descendantTipCount']
            collapsedNodes.remove( collapsedNodeRec )

    return collapsedDescendantsTipCount


def getSunburstResponse( response, session, clade ):
    """
    This function takes a web2py response object, a session object, a ivy/node object
    and returns a data structure that d3 can turn into a force directed tree
    """
    if( 'meta' not in clade ):
        gatherTreeInfo( clade, session, db )

    return response.json( sunburst.getRenderResponse( clade, session ) )


def getForceDirectedResponse( response, session, clade ):
    """
    This function takes a web2py response object, a session object, a ivy/node object
    and returns a data structure that d3 can turn into a force directed tree
    """

    #if( not hasattr( clade, 'meta' ) ):
    if( 'meta' not in clade ):
        gatherTreeInfo( clade, session, db )

    return response.json( forceDirected.getRenderResponse( clade, clade.groupId, session ) )


def determineLeftLabelBuffer( db, session, treeMetaRec, branchLength ):

    leftMost = 0
    
    depthDetail = db( db.treeMetaDepthDetail.treeMeta == treeMetaRec.id ).select().as_dict( key = 'depth' )

    for i in range( 1, treeMetaRec.depth ):

        if( depthDetail[i]['longestLabel'] is not None ):

            xCoord = ( i * branchLength ) - ( depthDetail[i]['longestLabel'] * session.textWidthMetric )

            if( xCoord < leftMost ):
                leftMost = xCoord

    return leftMost


def getRenderResponseNew( response, session, db, tree, collapsedNodeRecs ):
    
    config = session.TreeViewer.config

    treeMetaRec = db( ( db.treeMeta.tree == session.TreeViewer.treeId ) &
                      ( db.treeMeta.treeType == session.TreeViewer.type ) ).select().first()
    
    leftLabelBuffer = determineLeftLabelBuffer( db, session, treeMetaRec, int( config.branchLength ) )          
    
    treeWidth = int( config.branchLength ) * treeMetaRec.depth

    nodeTable = db.snode if session.TreeViewer.type == 'source' else db.gnode
    tableName = 'snode' if session.TreeViewer.type == 'source' else 'gnode'
    
    totalNodes = ( tree.back - tree.next - 1 ) / 2
   
    nodeMeta = db( ( db.phylogramNodeMeta.tree == session.TreeViewer.treeId ) &
                   ( db.phylogramNodeMeta.treeType == session.TreeViewer.type ) &
                   ( db.phylogramNodeMeta.nodeId == tree.id ) ).select( db.phylogramNodeMeta.descendantTipCount, db.phylogramNodeMeta.longestTraversal ).first()
    
    numberOfTips = nodeMeta.descendantTipCount

    heightAddedByCollapseUI = 0

    collapsedNodeDict = dict()
    for rec in collapsedNodeRecs:
        collapsedNodeDict[ rec[ tableName ]['id' ] ] = rec
        numberOfTips -= rec[ 'phylogramNodeMeta' ]['descendantTipCount']
        rec['descendantCount'] = int( math.floor( ( rec[ tableName ]['back'] - rec[ tableName ]['next'] - 1 ) / 2 ) )
        rec['collapseUIHeightByTwo'] = ( math.log( rec['descendantCount'] ) / math.log( totalNodes ) ) * ( float( session.TreeViewer.config.verticalTipBuffer ) / 2 )
        heightAddedByCollapseUI += ( rec['collapseUIHeightByTwo'] * 2 )
    
    collapsedNodeIds = collapsedNodeDict.keys()
    numberOfTips += 1

    max = db.phylogramNodeMeta.text.len().max()

    longestTipLabel = db( ( nodeTable.tree == session.TreeViewer.treeId ) &
                          ( nodeTable.next >= tree.next ) &
                          ( nodeTable.back <= tree.back ) &
                          ( nodeTable.isleaf == True ) &
                          ( nodeTable.id == db.phylogramNodeMeta.nodeId ) &
                          ( nodeTable.tree == db.phylogramNodeMeta.tree ) &
                          ( ~nodeTable.id.belongs( collapsedNodeIds ) ) &
                          ( db.phylogramNodeMeta.treeType == session.TreeViewer.type ) ).select( max ).first()[ max ]

    canvasWidth = treeWidth + ( int( config.horizontalPadding ) * 2 ) + ( longestTipLabel * int( session.textWidthMetric ) ) + ( float( config.tipLabelBuffer ) - leftLabelBuffer )
    
    canvasHeight = ( int( config.verticalTipBuffer ) * numberOfTips ) + ( int( config.verticalPadding ) * 2 ) + heightAddedByCollapseUI
  
    nodeMap = None

    if( config.branchLengthStyle == 'scale' ):
        config.scaledBranchMultiplier = treeWidth / nodeMeta.longestTraversal
        nodeMap = assignScaledNodeMappings( tree, session, collapsedNodeDict, totalNodes )
    else: 
        nodeMap = assignNodeMappings( tree, session, collapsedNodeDict, treeMetaRec.depth, totalNodes )

    pathString = getSVGCladePathString( tree )

    return response.json( dict( canvas = dict( x = canvasWidth, y = canvasHeight ),
                                rootId = tree.id,
                                pathString = pathString,
                                collapsedNodeIds = collapsedNodeIds,
                                nodeInfo = nodeMap ) )


def determineMaxTips( session ):
    """
    This function returns the maximum number of tips that can fit in the tree viewer
    """

    return int( session.TreeViewer.config.maxTips )
        
    if( renderType == 'forceDirected' ):
        return math.floor( ( ( session.TreeViewer.containerHeight ) - ( session.TreeViewer.config.verticalPadding * 2 ) ) / session.TreeViewer.config.verticalTipBuffer )

    else:
        return math.floor( ( session.TreeViewer.containerHeight - ( float( session.TreeViewer.config.verticalPadding ) * 2 ) ) / float( session.TreeViewer.config.verticalTipBuffer ) )



def gatherTreeInfo( node, session, db, newTree = False ):
    """
    """

    treeInfoObj = Storage( depth = 0, depthTipCount = Storage(), depthLongestLabel = Storage(), depthNodeCount = Storage(), nodeUpdater = dict() )

    import sys, datetime
    sys.stdout.write( str( 'recurse for info db : ' ) )
    sys.stdout.write( str( datetime.datetime.now() ) )
    sys.stdout.write( "\n" )

    gatherTreeInfoRecurseNew( treeInfoObj, node, Storage( generation = 1 ), session, db )
    
    sys.stdout.write( str( 'done recursing info db : ' ) )
    sys.stdout.write( str( datetime.datetime.now() ) )
    sys.stdout.write( "\n" )
    
    sys.stdout.write( str( 'begin node meta inserts : ' ) )
    sys.stdout.write( str( datetime.datetime.now() ) )
    sys.stdout.write( "\n" )
   
    for nodeId, metaData in treeInfoObj[ 'nodeUpdater' ].iteritems():

        if newTree:

            metaData['tree'] = session.TreeViewer.treeId
            metaData['treeType'] = session.TreeViewer.type
            metaData['nodeId'] = nodeId
            db.phylogramNodeMeta.insert( **metaData )

        else:

            record =  db( ( db.phylogramNodeMeta.treeType == session.TreeViewer.type ) &
                          ( db.phylogramNodeMeta.nodeId == nodeId ) ).select().first()


            if( record ):
                
                record.update_record( **metaData )

            else:

                metaData['tree'] = session.TreeViewer.treeId
                metaData['treeType'] = session.TreeViewer.type
                metaData['nodeId'] = nodeId
                db.phylogramNodeMeta.insert( **metaData )

    sys.stdout.write( str( 'end node meta inserts : ' ) )
    sys.stdout.write( str( datetime.datetime.now() ) )
    sys.stdout.write( "\n" )


    treeMetaRecord = db( ( db.treeMeta.tree == session.TreeViewer.treeId ) &
                         ( db.treeMeta.treeType == session.TreeViewer.type ) ).select().first()

    treeMetaId = None

    if( treeMetaRecord ):

        treeMetaRecord.update( depth = treeInfoObj.depth )
        treeMetaId = treeMetaRecord.id

    else:

        treeMetaId = db.treeMeta.insert( tree = session.TreeViewer.treeId, treeType = session.TreeViewer.type, depth = treeInfoObj.depth )


    sys.stdout.write( str( 'meta depth db insert : ' ) )
    sys.stdout.write( str( datetime.datetime.now() ) )
    sys.stdout.write( "\n" )

    for i in range( treeInfoObj.depth ):

        depthRecord = db( ( db.treeMetaDepthDetail.id == treeMetaId ) &
                          ( db.treeMetaDepthDetail.depth == i ) ).select().first()

        if( depthRecord ):

            depthRecord.update( nodeCount = treeInfoObj.depthNodeCount[i],
                                tipCount = treeInfoObj.depthTipCount[i],
                                longestLabel = treeInfoObj.depthLongestLabel[i] )

        else:

            db.treeMetaDepthDetail.insert( treeMeta = treeMetaId, 
                                           depth = i,
                                           nodeCount = treeInfoObj.depthNodeCount[i],
                                           tipCount = treeInfoObj.depthTipCount[i],
                                           longestLabel = treeInfoObj.depthLongestLabel[i] )
    
    sys.stdout.write( str( 'done meta depth db insert : ' ) )
    sys.stdout.write( str( datetime.datetime.now() ) )
    sys.stdout.write( "\n" )



def gatherTreeInfoRecurseNew( infoObj, node, recurseStruct, session, db ):
    """
    A recursive function that does the work for gatherTreeInfo
    """

    curGeneration = recurseStruct.generation

    if( infoObj.depth < curGeneration ):
        infoObj.depth = curGeneration

    if curGeneration not in infoObj.depthTipCount:
        infoObj.depthTipCount[ curGeneration ] = 0

    if curGeneration in infoObj.depthNodeCount:
        infoObj.depthNodeCount[ curGeneration ] += 1
    else:
        infoObj.depthNodeCount[ curGeneration ] = 1
      
    currentIterationInfo = Storage( distanceFromLeaf = 0, descendantTipCount = 0, longestTraversal = 0, closestDescendantLabel = '', hasDescendantLabel = False )
    
    node.text = node.taxon if node.taxon else node.label

    updater = infoObj[ 'nodeUpdater' ][ node.id ] = dict( text = node.text )
       
    if node.children:

        for child in node.children:

            recursiveIterationInfo = \
                gatherTreeInfoRecurseNew( infoObj, child, Storage( generation = curGeneration + 1 ), session, db )

            currentIterationInfo.descendantTipCount += recursiveIterationInfo.descendantTipCount

            if( recursiveIterationInfo.distanceFromLeaf >= currentIterationInfo.distanceFromLeaf ):
                currentIterationInfo.distanceFromLeaf = recursiveIterationInfo.distanceFromLeaf + 1
           
            if( recursiveIterationInfo.longestTraversal >= currentIterationInfo.longestTraversal ):
                currentIterationInfo.longestTraversal = recursiveIterationInfo.longestTraversal
            
            if( len( recursiveIterationInfo.closestDescendantLabel ) ):
                updater['closestDescendantLabel'] = currentIterationInfo.closestDescendantLabel = recursiveIterationInfo.closestDescendantLabel


        if( node.length ):
            currentIterationInfo.longestTraversal += node.length
        
        nodeWeight = ( currentIterationInfo.descendantTipCount / float( currentIterationInfo.distanceFromLeaf ) )

        if( recursiveIterationInfo.hasDescendantLabel ):
            currentIterationInfo.hasDescendentLabel = True
            nodeWeight *= .25

        updater['weight'] = nodeWeight

        if( node.text ):

            if( ( curGeneration not in infoObj.depthLongestLabel ) or
                ( len( node.text ) > infoObj.depthLongestLabel[ curGeneration ] ) ):
                infoObj.depthLongestLabel[ curGeneration ] = len( node.text )

            currentIterationInfo.hasDescendentLabel = True
    
    else:

        infoObj.depthTipCount[ curGeneration ] += 1
        
        currentIterationInfo.descendantTipCount += 1 
        currentIterationInfo.distanceFromLeaf = 1 

        if( node.length ):
            currentIterationInfo.longestTraversal = node.length



    if( node.text ):
        currentIterationInfo.closestDescendantLabel = node.text

    updater['longestTraversal'] = currentIterationInfo.longestTraversal
    updater['descendantTipCount'] = currentIterationInfo.descendantTipCount

        
    return Storage( distanceFromLeaf = currentIterationInfo.distanceFromLeaf,
                    descendantTipCount = currentIterationInfo.descendantTipCount,
                    closestDescendantLabel = currentIterationInfo.closestDescendantLabel,
                    longestTraversal = currentIterationInfo.longestTraversal )


def assignScaledNodeMappings( clade, session, collapsedNodeDict, totalNodes ):
    """
    A function that manages a tree recusrion that sets 'scaled' (style) node coordiates.
    Based on node.length properties
    """

    nodeMap = dict()
    nodeMap[ clade.id ] = dict()

    config = session.TreeViewer.config

    clade.x = float( config.horizontalPadding )
    nodeMap[ clade.id ]['x'] = clade.x

    if( clade.next == 1 ):
        clade.dx = -( float( config.branchLength ) )
    else:
        distance = clade.length * config.scaledBranchMultiplier
        clade.dx = -( distance )
    
    nodeMap[ clade.id ]['dx'] = clade.dx
    
    firstTip = Storage( y = float( session.TreeViewer.config.verticalPadding ) )

    childIds = [ ]
    for child in clade.children:
        childIds.append( child.id )
        assignScaledNodeMappingsRecurse( child, nodeMap, session, firstTip, collapsedNodeDict, totalNodes )
   
    clade.y = ( ( nodeMap[ clade.children[ -1 ].id ]['y'] + nodeMap[ clade.children[ 0 ].id ]['y'] ) / 2 )

    nodeMap[ clade.id ] = dict( nodeMap[ clade.id ].items() + dict( id = clade.id, y = clade.y, label = clade.text, next = clade.next, back = clade.back, children = childIds ).items() )

    return nodeMap


def assignScaledNodeMappingsRecurse( node, nodeMap, session, currentTip, collapsedNodeDict, totalNodes ):
    """
    A function that recurses through a tree adding node coordinates and labels to a dictionary where the keys are node ids.
    """

    nodeMap[ node.id ] = dict()

    distance = node.length * session.TreeViewer.config.scaledBranchMultiplier

    node.x = node.parent.x + distance
    node.dx = -( distance )
       
    childIds = [ ] 
    for child in node.children:
        childIds.append( child.id )
        assignScaledNodeMappingsRecurse( child, nodeMap, session, currentTip, collapsedNodeDict, totalNodes )

    if( node.children ):
        node.y = ( ( nodeMap[ node.children[ -1 ].id ]['y'] + nodeMap[ node.children[ 0 ].id ]['y'] ) / 2 )
    else:
        node.y = currentTip.y

        if( node.id in collapsedNodeDict ):

            assignCollapseDetail( node, collapsedNodeDict[ node.id ], session, currentTip, totalNodes )

            nodeMap[ node.id ]['collapsed'] = collapsedNodeDict[ node.id ]

        currentTip.y += float( session.TreeViewer.config.verticalTipBuffer )

    nodeMap[ node.id ] = dict( nodeMap[ node.id ].items() + dict( id = node.id, x = node.x, y = node.y, dx = node.dx, label = node.text, next = node.next, back = node.back, children = childIds ).items() )


def assignNodeMappings( clade, session, collapsedNodeDict, depth, totalNodes ):
    """
    A function that manages a tree recusrion that sets node coordiates and labels
    """

    nodeMap = dict() 

    firstTip = Storage( x = ( float( session.TreeViewer.config.branchLength ) * depth ) + float( session.TreeViewer.config.horizontalPadding ),
                        y = float( session.TreeViewer.config.verticalPadding ) )

    assignNodeMappingsRecurse( clade, nodeMap, session, collapsedNodeDict, firstTip, depth, totalNodes )

    return nodeMap


def assignNodeMappingsRecurse( node, nodeMap, session, collapsedNodeDict, currentTip, currentDepth, totalNodes ):
    """
    A function that recurses through a tree adding node coordinates and labels to a dictionary where the keys are node ids.
    """

    nodeMap[ node.id ] = dict()
    childIds = [ ]

    for child in node.children:
        childIds.append( child.id )
        assignNodeMappingsRecurse( child, nodeMap, session, collapsedNodeDict, currentTip, currentDepth - 1, totalNodes )

    if node.children:

        node.x = nodeMap[ node.children[0].id ]['x'] + nodeMap[ node.children[0].id ]['dx']
        node.dx = -( float( session.TreeViewer.config.branchLength ) )
        node.y = ( ( nodeMap[ node.children[ -1 ].id ]['y'] + nodeMap[ node.children[ 0 ].id ]['y'] ) / 2 )

    else:

        node.x = currentTip.x
        node.dx = -( float( session.TreeViewer.config.branchLength ) * currentDepth )
        node.y = currentTip.y

        if( node.id in collapsedNodeDict ):

            assignCollapseDetail( node, collapsedNodeDict[ node.id ], session, currentTip, totalNodes )

            nodeMap[ node.id ]['collapsed'] = collapsedNodeDict[ node.id ]

        currentTip.y += float( session.TreeViewer.config.verticalTipBuffer )

    parentId = node.parent.id if node.parent else None

    for child in node.children:
       
        if len( child.children ) == 0:
            continue

        closestChildX = None

        for grandkid in child.children:
            if( ( closestChildX is None ) or ( grandkid.x < closestChildX ) ):
                closestChildX = grandkid.x

        child.x = ( node.x + closestChildX ) / 2;
        nodeMap[ child.id ]['x'] = child.x
        child.dx = node.x - child.x;
        nodeMap[ child.id ]['dx'] = child.dx

        for grandkid in child.children:
            nodeMap[ grandkid.id ]['dx'] = child.x - nodeMap[ grandkid.id ]['x']
            grandkid.dx = nodeMap[ grandkid.id ]['dx']

            if( 'collapsed' in nodeMap[ grandkid.id ] ):
                info = nodeMap[ grandkid.id ]['collapsed']
                info['pathString'] = getCollapseUIPathString( grandkid, info )

    nodeMap[ node.id ] = dict( nodeMap[ node.id ].items() + dict( id = node.id, x = node.x, y = node.y, dx = node.dx, label = node.text, next = node.next, back = node.back, children = childIds, parent = parentId ).items() )



def assignCollapseDetail( node, infoDict, session, currentTip, totalNodes ):
    """
    This function gets the path string of a collapsed node UI and makes adjustments to its
    neighboring tips if the UI is larger than the normal vertical tip buffer
    """
    
    nodeTable = 'snode' if session.TreeViewer.type == 'source' else 'gnode'

    difference = ( infoDict['collapseUIHeightByTwo'] * 2 ) - float( session.TreeViewer.config.verticalTipBuffer )

    if( difference > 0 ):
        
        node.y += ( difference / 2 )
    
        currentTip.y += difference

    infoDict['text'] = ''.join( [ infoDict[ 'phylogramNodeMeta' ]['closestDescendantLabel'], ' (', str( infoDict['descendantCount'] ), ' nodes)' ] )
    infoDict['pathString'] = getCollapseUIPathString( node, infoDict )


def getCollapseUIPathString( node, infoDict ):
    """
    This function computes the path string of a collapsed node UI
    """
    return ''.join( [ "M", str( node.x + node.dx ), ' ', str( node.y ),
                      "l", str( - node.dx ), ' ', str( - infoDict['collapseUIHeightByTwo'] ),
                      'l0 ', str( 2 * infoDict['collapseUIHeightByTwo'] ), 'z' ] )


def getSVGCladePathString( clade ):
    """
    The function takes a clade and returns its path string
    """

    strList = []

    getSVGCladePathStringRecurse( clade, strList )

    return ''.join( strList )


def getSVGCladePathStringRecurse( node, strList ):
    """
    The function iterates through a clade recursively appending a path string for each node to a list.
    Used by getSVGCladePathString
    """

    strList.append( getSVGNodePathString( node ) )

    for child in node.children:
        getSVGCladePathStringRecurse( child, strList )


def getSVGNodePathString( node ):
    """
    The function accepts a modules.ivy.Node object and returns an svg path string using x, dx and y associated with the given node.
    Should this use a 'dx' attribute as well, or a branch length session variable or parameter?
    """

    returnString = [ ]

    strX = str( node.x )
    strDX = str( node.dx )
    strY = str( node.y )

    if node.children: 
        returnString.append( ''.join( [ 'M', strX, ' ', str( node.children[0].y ), 'L', strX, ' ', str( node.children[ len( node.children) - 1 ].y ) ] ) )
    
    returnString.append( ''.join( [ 'M', strX, ' ', strY, 'h', strDX ] ) )

    return ''.join( returnString )


def determineTreeToRender( db, session, root, collapsedNodeIds ):

    dbNodeTable = db.snode if session.TreeViewer.type == 'source' else db.gnode

    rootRecord = None

    if( root == 'root' ):
        rootRecord = db( ( dbNodeTable.tree == session.TreeViewer.treeId ) &
                         ( dbNodeTable.next == 1 ) ).select().first()
    else:
        rootRecord = db( ( dbNodeTable.tree == session.TreeViewer.treeId ) &
                         ( dbNodeTable.id == root ) ).select().first()

    collapsedNodeRecs = autoCollapse( rootRecord, session, db, collapsedNodeIds )

    tree = build.treeFromRootRow( db, rootRecord, session.TreeViewer.type, collapsedNodeRecs )
    
    return ( tree, collapsedNodeRecs )
    

def autoCollapse( cladeRecord, session, db, curCollapsedNodeIds ):
    """
    If the tree viewer is in 'navigate' mode ( rendering trees inside the tree viewer container ), then this
    function is called to do the work
    """

    nodeTable = db.snode if session.TreeViewer.type == 'source' else db.gnode

    numberOfTips = db( ( nodeTable.tree == session.TreeViewer.treeId ) &
                       ( nodeTable.isleaf == True ) ).count()

    maxTips = determineMaxTips( session )
    
    collapsedNodeInfo = [ ] 

    if( numberOfTips > maxTips ):

        nodeInfo = db( ( nodeTable.tree == session.TreeViewer.treeId ) & 
                       ( nodeTable.next >= cladeRecord.next ) &
                       ( nodeTable.back <= cladeRecord.back ) &
                       ( nodeTable.id == db.phylogramNodeMeta.nodeId ) &
                       ( nodeTable.tree == db.phylogramNodeMeta.tree ) &
                       ( nodeTable.isleaf == False ) &
                       ( session.TreeViewer.type == db.phylogramNodeMeta.treeType ) ).select(
            nodeTable.id,
            nodeTable.next,
            nodeTable.back,
            db.phylogramNodeMeta.weight,
            db.phylogramNodeMeta.descendantTipCount,
            db.phylogramNodeMeta.closestDescendantLabel, orderby=~db.phylogramNodeMeta.weight ).as_list()

        curCollapsedNodeInfo = db( ( nodeTable.id.belongs( curCollapsedNodeIds ) ) &
                                   ( nodeTable.id == db.phylogramNodeMeta.nodeId ) &
                                   ( session.TreeViewer.type == db.phylogramNodeMeta.treeType ) &
                                   ( session.TreeViewer.treeId == db.phylogramNodeMeta.tree ) ).select(
            nodeTable.id,
            nodeTable.next,
            nodeTable.back,
            db.phylogramNodeMeta.weight,
            db.phylogramNodeMeta.descendantTipCount,
            db.phylogramNodeMeta.closestDescendantLabel ).as_list()
   

        collapsedNodeInfo = determineCollapsedNodes( \
            nodeInfo,
            session.TreeViewer.strNodeTable,
            numberOfTips,
            curCollapsedNodeInfo,
            session.TreeViewer.status.keepVisibleNodeIds + [ int( cladeRecord.id ) ],
            maxTips )

    return collapsedNodeInfo


def isAncestor( possibleAncestor, possibleDescendant ):

    if( ( possibleDescendant.next <= possibleAncestor.next ) or
        ( possibleDescendant.back >= possibleAncestor.back ) ):

        return False

    else:

        return True


def getNodeById( currentNode, nodeId ):

    if( nodeId == currentNode.id ):
        return currentNode
    else:
        for child in currentNode.children:
            ret = getNodeById( child, nodeId )
            if ret:
                return ret
    return None
