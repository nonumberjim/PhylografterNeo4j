BioSync.TreeViewer.RenderUtil.phylogram.navigate.prototype = {

    start: function( viewer ) {

        this.viewer = viewer;
        this.make = BioSync.Common.makeEl;
        this.triggerHandling.addTriggerHandlers(); 
        
        return this;
    },

    triggerHandling: {
    
        addTriggerHandlers: function() {

            $(document).bind( 'editNode', this.editNode );
        },

        editNode: function( p, q ) {
    
            //p = jq event
            //q = { column: , nodeId: , optionDef: , renderObj: }

            q.renderObj.refreshColumn( { column: q.column, nodeId: q.nodeId } );
        }
    },
            
    eventHandlers: {
    
        collapseClade: function( p, q ) {
                    
            var clickedColumn = p.data.column;
            var renderObj = p.data.renderObj;
            var nodeId = p.data.nodeId;
                    
            var collapsingNode = clickedColumn.nodeInfo[ nodeId ];

            var successHandlers = new Array( renderObj.viewer.handleReceivedTree, renderObj.successfulCladeCollapse );
            if( clickedColumn.index != 0 ) { successHandlers.push( renderObj.updateAncestorConnection ); }

            var wasRightmostColumnClicked = ( clickedColumn.index == ( renderObj.columns.length - 1 ) ) ? true : false;

            if( wasRightmostColumnClicked ) {

                renderObj.removeColumn( { index: clickedColumn.index } );
                renderObj.addNewColumn();
                renderObj.currentColumn.recentlyCollapsedNodeId = nodeId;

            } else {

                var expandedNodeId = clickedColumn.container.find('.expanded').attr('nodeId');
                var expandedNode = clickedColumn.nodeInfo[ expandedNodeId ];

                if( renderObj.viewer.isAncestor( { ancestor: collapsingNode, descendant: expandedNode } ) ) {
                
                    renderObj.removeColumns( { start: clickedColumn.index, end: renderObj.columns.length - 1 } );
                    renderObj.addNewColumn();
                    renderObj.currentColumn.recentlyCollapsedNodeId = nodeId;

                } else {

                    var index = clickedColumn.index;
                    renderObj.removeColumn( { index: index } );
                    renderObj.insertNewColumn( { index: index } );
                    renderObj.currentColumn.expandedNodeId = expandedNodeId;
                    renderObj.currentColumn.recentlyCollapsedNodeId = nodeId;
                    successHandlers = successHandlers.concat( [ renderObj.showExpandedNodeUI, renderObj.updateDescendantConnection, renderObj.resetCurrentColumn ] );
                }
            }

            for( var i = 0, ii = clickedColumn.collapsedNodeIds.length; i < ii; i++ ) {
               
                if( clickedColumn.collapsedNodeIds[ i ] == undefined ) { continue; }

                var collapsedNode = clickedColumn.nodeInfo[ clickedColumn.collapsedNodeIds[ i ] ];

                if( renderObj.viewer.isAncestor( { ancestor: collapsingNode, descendant: collapsedNode } ) ) {

                    clickedColumn.collapsedNodeIds.splice( i, 1 );
                    i--;
                }
            }

            $.ajax( { url: BioSync.Common.makeUrl( { controller: 'plugin_treeViewer', argList: [ 'collapseClade' ] } ),
                      type: "GET",
                      context: renderObj.viewer,
                      data: { nodeId: nodeId, rootId: clickedColumn.rootId, collapsedNodeIds: clickedColumn.collapsedNodeIds.join(':') },
                      success: successHandlers } );
        }
    },

    hasVerticalScrollbar: function( p ) {
        
        var columnWrapperHeight = this.columnWrapper.height();

        for( var i = 0, ii = this.columns.length; i < ii; i++ ) {

            if( this.columns[i].svgDiv.height() > columnWrapperHeight ) { return true; }
        }

        return false;
    },


    updateBranchLength: function( value ) {

        this.viewer.updateConfig( { names: [ 'branchLengthStyle' ], values: [ value ], redraw: true } );
    },

    scrollToNode: function( p ) {

        var currentColumn = this.currentColumn;

        var columnWrapperHeight = this.columnWrapper.height();

        if( currentColumn.svgDiv.height() > columnWrapperHeight ) {

            var node = currentColumn.nodeInfo[ p.nodeId ];

            this.viewPanel.animate( { scrollTop: node.y - ( columnWrapperHeight / 2 ) }, 1000, function() { $(this).removeClass('scrolling'); } ).addClass('scrolling');
        }
    },

    resetCurrentColumn: function() {

        this.renderObj.currentColumn = this.renderObj.columns[ this.renderObj.columns.length - 1];
    },

    successfulCladeCollapse: function() {

        var renderObj = this.renderObj;
        var currentColumn = renderObj.currentColumn;
        var canvas = currentColumn.canvas;
        var node = currentColumn.nodeInfo[ currentColumn.recentlyCollapsedNodeId ];

        renderObj.scrollToNode( { nodeId: currentColumn.recentlyCollapsedNodeId } );

        renderObj.spinAroundNode( { node: node, canvas: canvas } );

        setTimeout( function() { BioSync.Common.notify( { text: 'Collapsed Node',
                                     timeout: 2000,
                                     x: parseFloat( currentColumn.myOffset.left ) + parseFloat( node.x ),
                                     y: parseFloat( currentColumn.myOffset.top ) + parseFloat( node.y ) + 30 - renderObj.viewPanel.scrollTop()} ); }, 1000 );

    },

    afterVerticalExpand: function() {

        var renderObj = this.renderObj;
        var currentColumn = renderObj.currentColumn;
        var canvas = currentColumn.canvas;
        var node = currentColumn.nodeInfo[ currentColumn.recentlyExpandedNodeId ];

        renderObj.scrollToNode( { nodeId: currentColumn.recentlyExpandedNodeId } );

        renderObj.spinAroundNode( { node: node, canvas: canvas } );

        setTimeout( function() { BioSync.Common.notify( { text: 'Expanded Node',
                                     timeout: 2000,
                                     x: parseFloat( currentColumn.myOffset.left ) + parseFloat( node.x ),
                                     y: parseFloat( currentColumn.myOffset.top ) + parseFloat( node.y ) + 30 - renderObj.viewPanel.scrollTop()} ); }, 1000 );
    },

    spinAroundNode: function( p ) {

        var canvas = this.currentColumn.canvas;
        var node = p.node;

        var r1 = 10;
        var r2 = 10;
        var strokeWidth = 7;
        var strokeColor = 'red';
        var sectorsCount = 7;
        var cx = node.x;
        var cy = node.y;

        var opacity = [ ]; 
        var sectors = [ ];

        var beta = 2 * Math.PI / sectorsCount;
        var pathParams = { 'stroke': strokeColor, "stroke-width": strokeWidth, "stroke-linecap": "round" };

        for( var i = 0; i < sectorsCount; i++ ) {
        
            var alpha = beta * i - Math.PI / 2;
            var cos = Math.cos( alpha );
            var sin = Math.sin( alpha );
            opacity[i] = 1 / sectorsCount * i;
           
            sectors[i] = canvas.path([["M", cx + r1 * cos, cy + r1 * sin], ["L", cx + r2 * cos, cy + r2 * sin]]).attr(pathParams);
        }

        var tick;
        ( function ticker() {
              opacity.unshift( opacity.pop() );
              
              for( var i = 0; i < sectorsCount; i++ ) {
                  sectors[i].attr("opacity", opacity[i]);
              }
              
              canvas.safari();
              
              tick = setTimeout(ticker, 1000 / sectorsCount);
        } )();

        setTimeout( function() { clearTimeout( tick ); for( var i = 0; i < sectorsCount; i++ ) { sectors[i].remove(); } }, 4000 );
    },

    collapseExpandedNode: function( p ) {

        var renderObj = p.data.renderObj;
        var clickedColumn = renderObj.columns[ p.data.columnIndex ];

        var divOption = $( this );

        renderObj.removeColumns( { start: p.data.columnIndex + 1, end: renderObj.columns.length - 1 } );

        divOption.find( '.collapseUI' ).removeClass( 'collapseUI' ).addClass( 'horiExpandUI' );
        divOption.find( '.optionText' ).text( 'Expand Horizontally' );
        divOption.unbind( 'click' ).bind( 'click', p.data, renderObj.horizontallyExpandNode )
                                   .bind( 'click', { }, BioSync.OptionsMenu.hideContextMenu );

        clickedColumn.nodeInfo[ p.data.nodeId ].hiddenHover.el.removeClass('expanded');
    },
     
    horizontallyExpandNode: function( p ) {
        
        var renderObj = p.data.renderObj;
        var clickedColumn = renderObj.columns[ p.data.columnIndex ];

        var divOption = $( this );

        divOption.find( '.horiExpandUI' ).removeClass( 'horiExpandUI' ).addClass( 'collapseUI' );
        divOption.find( '.optionText' ).text( 'Collapse Clade' );
        divOption.unbind( 'click' ).bind( 'click', p.data, renderObj.collapseExpandedNode )
                                   .bind( 'click', { }, BioSync.OptionsMenu.hideContextMenu );

        if( clickedColumn.index != ( renderObj.columns.length - 1 ) ) {
            renderObj.removeColumns( { start: clickedColumn.index + 1, end: renderObj.columns.length - 1 } );
            clickedColumn.container.find('.expanded').removeClass('expanded');
        }
        
        clickedColumn.nodeInfo[ p.data.nodeId ].hiddenHover.el.addClass('expanded');

        renderObj.addNewColumn();

        //$.ajax( { url: BioSync.Common.makeUrl( { controller: 'plugin_treeViewer', argList: [ 'horizontallyExpandNode' ] } ),
        $.ajax( { url: BioSync.Common.makeUrl( { controller: 'plugin_treeViewer', argList: [ 'getClade' ] } ),
                  type: "GET",
                  context: renderObj.viewer,
                  data: { treeId: renderObj.viewer.treeId, nodeId: p.data.nodeId },
                  success: new Array( renderObj.viewer.handleReceivedTree, renderObj.updateAncestorConnection, renderObj.scrollToCurrentColumn ) } );
    },

    scrollToCurrentColumn: function( response ) {

        var renderObj = this.renderObj;
        var viewPanel = renderObj.viewPanel;

        var curColumnRight = renderObj.currentColumn.myPosition.left + renderObj.currentColumn.myWidth;
        var viewPanelWidth = viewPanel.width();
        var viewPanelScroll = viewPanel.scrollLeft();

        var difference = curColumnRight - ( viewPanelWidth + viewPanelScroll );

        if( difference > 0 ) { viewPanel.animate( { scrollLeft: '+=' + difference }, 1000 ); }
    },

    showExpandedNodeUI: function( p ) {

        var renderObj = this.renderObj;
        var currentColumn = renderObj.currentColumn;
         
        currentColumn.nodeInfo[ currentColumn.expandedNodeId ].hiddenHover.el.addClass('expanded');
    },

    verticallyExpandNode: function( p ) { 

        var renderObj = p.data.renderObj;
        var clickedColumn = renderObj.columns[ p.data.columnIndex ];

        var rootId = clickedColumn.rootId;
        var nodeInfo = clickedColumn.nodeInfo;

        var successHandlers = new Array( renderObj.viewer.handleReceivedTree, renderObj.afterVerticalExpand );
        if( clickedColumn.index != 0 ) { successHandlers.push( renderObj.updateAncestorConnection ); }
        
        if( clickedColumn.index == ( renderObj.columns.length - 1 ) ) {

            renderObj.removeColumn( { index: clickedColumn.index } );
            renderObj.addNewColumn();

        } else {

            var expandedNodeDOM = $( clickedColumn.container.find('div.expanded')[0] );

            if( expandedNodeDOM.attr('nodeId') == p.data.nodeId ) {
                renderObj.removeColumns( { start: clickedColumn.index, end: renderObj.columns.length - 1 } );
                renderObj.addNewColumn();

            } else {
                
                renderObj.removeColumn( { index: clickedColumn.index } );
                renderObj.insertNewColumn( { index: clickedColumn.index } );
                renderObj.columns[ clickedColumn.index ].expandedNodeId = expandedNodeDOM.attr('nodeId');
                successHandlers.push( renderObj.showExpandedNodeUI );
                successHandlers.push( renderObj.updateDescendantConnection );
            }
        }

        renderObj.currentColumn.recentlyExpandedNodeId = p.data.nodeId;

        $.ajax( { url: BioSync.Common.makeUrl( { controller: 'plugin_treeViewer', argList: [ 'verticallyExpandNode' ] } ),
                  type: "GET",
                  context: renderObj.viewer,
                  data: { keepVisible: [ renderObj.getColumnAncestorIds( { nodeInfo: nodeInfo, nodeId: p.data.nodeId } ) ].join(','),
                          nodeId: p.data.nodeId, rootId: rootId, collapsedNodeIds: clickedColumn.collapsedNodeIds.join(',') },
                  success: successHandlers } );
    },

    getColumnAncestorIds: function( p ) {

        var ancestorIds = [ ];

        var nodeId = p.nodeId;

        while( p.nodeInfo[ nodeId ].parent ) {

            ancestorIds.push( p.nodeInfo[ nodeId ].parent );
            nodeId = p.nodeInfo[ nodeId ].parent;
        }

        return ancestorIds;
    },

    //not being used (zoom)
    changeTreeSize: function( p ) {

        for( var i = 0, ii = this.columns.length; i < ii; i++ ) {

            var center = { x: this.columns[i].canvas.width / 2, y: this.columns[i].canvas.height / 2 };

            var newCanvasSize = { x: this.columns[i].canvas.width * p.ratio,
                                  y: this.columns[i].canvas.height * p.ratio };

            var oldPathBBox = this.columns[i].path.getBBox();

            this.columns[i].path.scale( p.ratio, p.ratio, center.x, center.y );

            var newPathBBox = this.columns[i].path.getBBox();

            var newPathCoords = { x: ( oldPathBBox.x / this.columns[i].canvas.width ) * newCanvasSize.x,
                                  y: ( oldPathBBox.y / this.columns[i].canvas.height ) * newCanvasSize.y };
            
            var translate = { x: newPathCoords.x - newPathBBox.x,
                              y: newPathCoords.y - newPathBBox.y };
            
            this.columns[i].path.translate( translate.x, translate.y );
            var newPathBBox = this.columns[i].path.getBBox();

            for( var j = 0, jj = this.columns[i].labels.length; j < jj; j++ ) {

                var labelInfo = this.columns[ i ].labels[ j ];
                var label = labelInfo.raphaelLabel;
            
                var x = ( ( label.attr('x') - oldPathBBox.x ) * p.ratio ) + newPathBBox.x;
                var y = ( ( label.attr('y') - oldPathBBox.y ) * p.ratio ) + newPathBBox.y;

                label.attr( { 'x': x, 'y': y,
                              'font-size': label.attr('font-size') * p.ratio,
                              'stroke-width': label.attr('stroke-width') * p.ratio } );
            }

            for( var j = 0, jj = this.columns[i].collapsedNodeIds.length; j < jj; j++ ) {

                var info = this.columns[i].nodeInfo[ this.columns[i].collapsedNodeIds[j] ].hiddenHover;

                info.path.scale( p.ratio, p.ratio, center.x, center.y );
                info.path.translate( translate.x, translate.y );
                
                info.label.attr( { 'x': ( ( info.label.attr('x') - oldPathBBox.x ) * p.ratio ) + newPathBBox.x,
                                   'y': ( ( info.label.attr('y') - oldPathBBox.y ) * p.ratio ) + newPathBBox.y,
                                   'font-size': info.label.attr('font-size') * p.ratio,
                                   'stroke-width': info.label.attr('stroke-width') * p.ratio } );

                info.el.css( { left: ( ( parseFloat( info.el.css('left') ) - oldPathBBox.x ) * p.ratio ) + newPathBBox.x,
                               top: ( ( parseFloat( info.el.css('top') ) - oldPathBBox.y ) * p.ratio ) + newPathBBox.y } )
                       .width( info.el.width() * p.ratio )
                       .height( info.el.height() * p.ratio );
            }

            this.setCanvasSize( this.columns[i], newCanvasSize.x, newCanvasSize.y );
            this.alignColumns( { index: i } );
            this.centerColumn( { index: i } );

            if( this.columns[ i+1 ] ) {
                this.columnConnections[i][0].scale( p.ratio, p.ratio, center.x, center.y );
                this.columnConnections[i][0].translate( translate.x, translate.y );
            }

            if( this.columns[ i - 1 ] ) {
                var canvas = this.columns[ i ].canvas;
                this.columnConnections[ i - 1 ][1].scale( p.ratio, p.ratio, center.x, center.y );
                this.columnConnections[ i - 1 ][1].translate( translate.x, translate.y );
            }

        }
    },

    refreshColumn: function( p ) {

        var renderObj = this;
        var column = p.column;
        
        var columnIndex = column.index;
        var successHandlers = new Array( renderObj.viewer.handleReceivedTree );
        if( columnIndex != 0 ) { successHandlers.push( renderObj.updateAncestorConnection ); }
  
        var expandedNodeId = column.container.find( '.expanded' ).attr('nodeId');
        var collapsedNodeIds = column.collapsedNodeIds.join(':'); 

        renderObj.removeColumn( { index: columnIndex } );
        
        renderObj.insertNewColumn( { index: columnIndex } );

        if( expandedNodeId ) {

            renderObj.columns[ columnIndex ].expandedNodeId = expandedNodeId;
            successHandlers.push( renderObj.showExpandedNodeUI );
            successHandlers.push( renderObj.updateDescendantConnection );
        }

        $.ajax( { url: BioSync.Common.makeUrl( { controller: 'plugin_treeViewer', argList: [ 'refreshColumn' ] } ),
                  type: "GET", context: renderObj.viewer, async: false, data: { rootId: column.rootId, collapsedNodeIds: collapsedNodeIds },
                  success: successHandlers } );
    },

    updateAncestorConnection: function() {

        var renderObj = this.renderObj;

        renderObj.updateConnection( { columnConnection: renderObj.columnConnections[ renderObj.currentColumn.index - 1 ],
                                      ancestorColumn: renderObj.columns[ renderObj.currentColumn.index - 1 ],
                                      descendantColumn: renderObj.currentColumn,
                                      animate: false } );
    },

    updateDescendantConnection: function() {

        var renderObj = this.renderObj;

        renderObj.updateConnection( { columnConnection: renderObj.columnConnections[ renderObj.currentColumn.index ],
                                      ancestorColumn: renderObj.currentColumn,
                                      descendantColumn: renderObj.columns[ renderObj.currentColumn.index + 1 ],
                                      animate: true } );
    },

    updateConnection: function( p ) {

        var columnConnection = p.columnConnection;
        var ancestorColumn = p.ancestorColumn;
        var descendantColumn = p.descendantColumn;

        var expandedNodeDOM = $( ancestorColumn.container.find('div.expanded')[0] );
        var descendantRootNode = descendantColumn.nodeInfo[ descendantColumn.rootId ];

        var ancestorConnection = new Object();
        BioSync.Common.storeObjPosition( expandedNodeDOM, ancestorConnection );

        var ancestorColumnCoords = { x1: ancestorConnection.myPosition.left + ancestorConnection.myWidth,
                                     y1: ancestorConnection.myPosition.top + ( ancestorConnection.myHeight / 2 ) }
                        
        ancestorColumnCoords.x2 = ancestorColumn.myWidth;
        ancestorColumnCoords.y2 = ancestorColumnCoords.y1;

        var descendantColumnCoords = { x1: descendantRootNode.x,
                                       y1: descendantRootNode.y };

        descendantColumnCoords.x2 = this.viewer.config.horizontalPadding / 2;
        descendantColumnCoords.y2 = descendantColumnCoords.y1;
        
        descendantColumnCoords.x3 = descendantColumnCoords.x2;
        descendantColumnCoords.y3 = ancestorColumnCoords.y1 - ( descendantColumn.centerOffset - ancestorColumn.centerOffset );
        
        descendantColumnCoords.x4 = 0;
        descendantColumnCoords.y4 = descendantColumnCoords.y3;

        if( descendantColumnCoords.y3 > descendantColumn.svgDiv.height() ) {
            this.setCanvasSize( descendantColumn, descendantColumn.svgDiv.width(), descendantColumnCoords.y3 + this.viewer.config.verticalPadding );
        }
        
        if( descendantColumnCoords.y3 < 0 ) {

            descendantColumn.centerOffset = descendantColumn.centerOffset + descendantColumnCoords.y3;
            descendantColumn.svgDiv.css( { top: descendantColumn.centerOffset } );
            this.setCanvasSize( descendantColumn, descendantColumn.svgDiv.width(), descendantColumn.svgDiv.height() - descendantColumnCoords.y3 );
            descendantColumnCoords.y3 = 0;
            descendantColumnCoords.y4 = 0;
        }
   
        columnConnection[ 0 ] =
            ancestorColumn.canvas.path( [ "M", ancestorColumnCoords.x1, " ", ancestorColumnCoords.y1, "L" ].join("") )
                                     .attr( { stroke: this.config.columnConnectionColor, "stroke-width": this.config.columnConnectionWidth } );

        columnConnection[ 1 ] = descendantColumn.canvas.path( [ "M", descendantRootNode.x, " ", descendantRootNode.y, "L" ].join("") )
                                     .attr( { stroke: this.config.columnConnectionColor, "stroke-width": this.config.columnConnectionWidth } );

        if( p.animate ) {
            
            columnConnection[ 0 ].animate( { path: [ "M", ancestorColumnCoords.x1, " ", ancestorColumnCoords.y1,
                                                     "L", ancestorColumnCoords.x2, " ", ancestorColumnCoords.y2 ].join("") }, this.config.animateColumnConnectionTime );
            
            columnConnection[ 1 ].animate( { path: [ "M", descendantColumnCoords.x1, " ", descendantColumnCoords.y1,
                                                     "L", descendantColumnCoords.x2, " ", descendantColumnCoords.y2,
                                                     "L", descendantColumnCoords.x3, " ", descendantColumnCoords.y3,
                                                     "L", descendantColumnCoords.x4, " ", descendantColumnCoords.y4 ].join("") }, this.config.animateColumnConnectionTime );

            var renderObj = this;

            setTimeout( function() { columnConnection[0].animate( { opacity: 0.1 }, 200 ); }, renderObj.config.animateColumnConnectionTime );
            setTimeout( function() { columnConnection[1].animate( { opacity: 0.1 }, 200 ); }, renderObj.config.animateColumnConnectionTime );

        } else {

            columnConnection[ 0 ].attr( { path: [ "M", ancestorColumnCoords.x1, " ", ancestorColumnCoords.y1,
                                                  "L", ancestorColumnCoords.x2, " ", ancestorColumnCoords.y2 ].join(""),
                                          opacity: 0.1 } );
            
            columnConnection[ 1 ].attr( { path: [ "M", descendantColumnCoords.x1, " ", descendantColumnCoords.y1,
                                                  "L", descendantColumnCoords.x2, " ", descendantColumnCoords.y2,
                                                  "L", descendantColumnCoords.x3, " ", descendantColumnCoords.y3,
                                                  "L", descendantColumnCoords.x4, " ", descendantColumnCoords.y4 ].join(""),
                                          opacity: 0.1 } );
        }
    },

    setCanvasSize: function( column, width, height ) {
        column.canvas.setSize( width, height );
        column.svgDiv.width( width ).height( height );
        column.container.width( width );
        BioSync.Common.storeObjPosition( column.container, column );
    },

    config: {

        animateColumnConnectionTime: 2000,
        columnConnectionColor: 'blue',
        columnConnectionWidth: 2
    },

    removeColumns: function( p ) {

        for( var i = p.end, ii = p.start; i >= ii; i-- ) {
            
            this.removeColumn( { index: i } );
        }

        this.updateColumnWrapper();
    },

    removeColumn: function( p ) {

        var column = this.columns[ p.index ];

        column.container.hide( 'slow', this.emptyColumn );

        this.columns.splice( p.index, 1 );

        var ancestorColumnConnectionIndex = p.index - 1;

        //ancestor
        if( this.columnConnections[ ancestorColumnConnectionIndex ] &&
            this.columnConnections[ ancestorColumnConnectionIndex ].length ) {
            this.columnConnections[ ancestorColumnConnectionIndex ][0].remove();
            this.columnConnections[ ancestorColumnConnectionIndex ][1].remove();
        }

        //descendant
        if( this.columnConnections[ p.index ] &&
            this.columnConnections[ p.index ].length ) {
            this.columnConnections[ p.index ][0].remove();
            this.columnConnections[ p.index ][1].remove();
            this.columnConnections.splice( p.index, 1 );
        }
    },

    emptyColumn: function() { $( this ).empty().remove(); },

    initialize: function() {

        var viewer = this.viewer;

        this.viewPanel = this.make('div').attr( { 'class': 'viewPanel' } )
                                         .height( '100%' )
                                         .width( viewer.myWidth );

        this.columnWrapper =
            this.make('div').attr( { 'class': 'columnWrapper' } ).height( viewer.myHeight - BioSync.Common.scrollbarWidth );

        viewer.container.append( this.viewPanel.append( this.columnWrapper ) );

        this.columns = [ ];
        this.columnConnections = [];

        this.addNewColumn();

        BioSync.Common.storeObjPosition( this.viewPanel, this.viewPanel );
    },

    makeColumn: function() {

        var column =  { svgDiv: this.make('div').attr( { 'class': 'navigateSvgDiv' } ),
                        svgWrapper: this.make('div').attr( { 'class': 'svgWrapper' } ).height( '100%' ),
                        container: this.make('div').attr( { 'class': 'columnContainer' } ).height( '100%' ) };

        column.container.append( column.svgWrapper.append( column.svgDiv ) );

        return column;
    },
                    
    insertNewColumn: function( p ) {

        if( p.index > this.columns.length - 1 ) { this.addNewColumn(); return; }

        var column = this.makeColumn();
        
        column.index = p.index;

        this.columns.splice( p.index, 0,  column );

        this.currentColumn = column;

        column.container.insertBefore( this.columns[ p.index + 1 ].container );
        BioSync.Common.storeObjPosition( column.container, column );
        
        this.columnConnections.splice( p.index, 0, [] );
        
        this.addCanvas();
    },

    alignColumns: function( p ) {

        for( var i = p.index, ii = this.columns.length; i < ii; i++ ) {
            this.alignColumn( { index: i } );
        }
    },

    alignColumn: function( p ) {
    
        if( p.index == 0 ) {
            this.columns[ p.index ].container.css( { left: 0 } );
        } else {
            var prevColumn = this.columns[ p.index - 1 ];
            this.columns[ p.index ].container.css( { left: prevColumn.myPosition.left + prevColumn.myWidth } );
            BioSync.Common.storeObjPosition( this.columns[ p.index ].container, this.columns[ p.index ] );
        }
    },

    addCanvas: function( p ) {

        this.currentColumn.canvas = Raphael( this.currentColumn.svgDiv.get(0), 300, 100 );
    },

    addNewColumn: function() {

        var column = this.makeColumn();
        
        column.index = this.columns.length;

        this.columns.push( column );

        this.columnWrapper.append( column.container );
        BioSync.Common.storeObjPosition( column.container, column );

        this.currentColumn = column;

        this.addCanvas();

        this.columnConnections.push( [] );

        this.alignColumn( { index: column.index } );
        
        this.updateColumnWrapper();
    },

    renderReceivedTree: function() {

        var viewer = this.viewer;
        var currentColumn = this.currentColumn;

        var response = viewer.renderResponse;

        currentColumn.container.width( response.canvas.x );
        this.setCanvasSize( currentColumn, response.canvas.x, response.canvas.y );

        currentColumn.rootId = response.rootId;
        currentColumn.nodeInfo = response.nodeInfo;

        BioSync.Common.storeObjPosition( currentColumn.container, currentColumn );
        
        currentColumn.path =
            currentColumn.canvas.path( response.pathString )
                                .attr( { stroke: viewer.config.treeColor,
                                         "stroke-linecap": 'square',
                                         "stroke-width": viewer.config.pathWidth } );

        this.renderLabels();
        
        this.renderCollapsedNodeUI();
       
        var rootNode = currentColumn.nodeInfo[ response.rootId ];
        currentColumn.rootLocation = { x: rootNode.x, y: rootNode.y };

        if( viewer.events.nodeClick || viewer.events.nodeRightClick ) { this.addNodeSelector(); }
        
        this.centerColumn( { index: currentColumn.index } );
        
        this.alignColumns( { index: currentColumn.index } );
         
        this.updateColumnWrapper();
    },

    redrawTree: function() {

        this.removeColumns( { start: 0, end: this.columns.length - 1 } );
        this.addNewColumn();
        this.viewer.getTree();
    },

    updateColumnWrapper: function() {

        if( this.columns.length ) {
            var rightmostColumn = this.columns[ this.columns.length - 1 ];
            var wrapperWidth = rightmostColumn.myPosition.left + rightmostColumn.myWidth;
            this.columnWrapper.animate( { 'width': wrapperWidth } );
        }
    },

    centerColumn: function( p ) {

        var currentColumn = this.columns[ p.index ];
        
        if( currentColumn.myHeight > currentColumn.svgDiv.height() )  {
            
            currentColumn.centerOffset = ( currentColumn.myHeight / 2 ) - ( currentColumn.svgDiv.height() / 2 );
            currentColumn.svgDiv.css( { top: currentColumn.centerOffset } );

        } else {

            currentColumn.centerOffset = 0;
        }

    },


    renderLabels: function() {

        var currentColumn = this.currentColumn;
        var nodeInfo = currentColumn.nodeInfo;
        var viewer = this.viewer;

        currentColumn.labels = [ ];
         
        for( var nodeId in nodeInfo ) {

            var node = nodeInfo[ nodeId ];

            if( node.label ) {

                var label = 
                    currentColumn.canvas.text( node.x + viewer.config.tipLabelBuffer, node.y, node.label )
                                        .attr( { stroke: 'none',
                                                 fill: viewer.config.treeColor,
                                                 "font-family": viewer.config.fontFamily,
                                                 "font-size": viewer.config.fontSize,
                                                 "text-anchor": "start" } );

                var eventObj = viewer.events;

                if( eventObj.labelClick || eventObj.labelRightClick ) {

                    var bindInfo = { left: { func: function() { }, params: { } }, right: { func: function() { }, params: { } } }

                    if( eventObj.labelClick ) {

                        if( eventObj.labelClick.type == 'getUrlForm' ) {
                           
                           bindInfo.left = { func: BioSync.ModalBox.getUrlForm,
                                             params: { url: [ eventObj.labelClick.url, nodeId ].join('/'),
                                                       title: eventObj.labelClick.title,
                                                       successTrigger: eventObj.labelClick.successTrigger,
                                                       successData: { renderObj: viewer.renderObj, column: viewer.renderObj.columns[ currentColumn.index ] } } };
                        }
                    }

                    $( label.node ).bind( 'click', bindInfo, BioSync.Common.handleBothClicks );
                    
                    $( label.node )
                        .bind( 'mouseover', { el: $(viewer.container) }, BioSync.Common.addHoverPointer )
                        .bind( 'mouseout', { el: $(viewer.container) }, BioSync.Common.removeHoverPointer );
                }

                var internalNodeThing;

                if( node.children.length ) {

                    var boundingBox = label.getBBox();

                    var top = node.y - ( boundingBox.height / 2 );
                    var left = node.x - boundingBox.width;
                     
                    label.attr( { x: left + viewer.config.nonTipLabelBuffer, y: top } );

                    internalNodeThing =
                        currentColumn.canvas.rect( left + viewer.config.nonTipLabelBuffer, top - ( boundingBox.height / 2 ), boundingBox.width, boundingBox.height )
                            .attr( { 'fill': 'yellow', 'fill-opacity': '.5', 'stroke': '' } );
                }

                node.raphaelLabel = label;
                node.internalNodeThing = internalNodeThing;

                currentColumn.labels.push( { raphaelLabel: label, nodeId: nodeId, internalNodeThing: internalNodeThing } );
            }
        }
    },

    getHorizontalOption: function( p ) {

        var make = this.make;

        var data = ( p.nodeId != this.columns[ p.columnIndex ].expandedNodeId ) ?
            { class: 'horiExpandUI', text: 'Expand Horizontally', handler: this.horizontallyExpandNode } :
            { class: 'collapseUI', text: 'Collapse Clade', handler: this.collapseExpandedNode };

        return make('div').attr( { 'class': 'expandOption menuOptionItem' } ).append(
            make('div').attr( { 'class': 'fLeft' } ).height( 20 ).width( 20 ).append(
                make('div').attr( { 'class': data.class } ) ),
            make('div').attr( { 'class': 'fLeft optionText' } ).css( { 'padding-left': '5px' } ).text( data.text ),
            make('div').attr( { 'class': 'clear' } ) )
          .bind( 'click', { renderObj: this, columnIndex: p.columnIndex, nodeId: p.nodeId }, data.handler )
          .bind( 'click', { }, BioSync.OptionsMenu.hideContextMenu );
    },

    navigateToNode: function( p ) {

        var successArray = new Array( this.viewer.handleReceivedTree, $.proxy( this.nodeFocus, this ) );
        if( p.onSuccess ) { successArray.push( p.onSuccess ); }

        this.removeColumns( { start: 0, end: this.columns.length - 1 } );
        this.addNewColumn();

        this.nodeFocusId = p.nodeId;

        $.ajax( { url: BioSync.Common.makeUrl( { controller: 'plugin_treeViewer', argList: [ 'navigateToNode' ] } ),
                  type: "GET", async: ( p.async != undefined ) ? p.async : true,
                  context: this.viewer,
                  data: { treeId: this.viewer.treeId, nodeId: p.nodeId },
                  success: successArray } );
    },

    nodeFocus: function( p ) {

        var column;

        for( var i = 0, ii = this.columns.length; i < ii; i++ ) {

            if( this.columns[i].nodeInfo[ this.nodeFocusId ] ) { column = this.columns[i]; break; }
        }

        var node = column.nodeInfo[ this.nodeFocusId ];

        this.spinAroundNode( { node: node, canvas: column.canvas } );
    },

    renderCollapsedNodeUI: function() {

        var viewer = this.viewer;
        var currentColumn = this.currentColumn;
        var make = this.make;

        currentColumn.collapsedNodeIds = viewer.renderResponse.collapsedNodeIds;

        for( var i = 0, ii = currentColumn.collapsedNodeIds.length; i < ii; i++ ) {

            var nodeId = currentColumn.collapsedNodeIds[ i ];
            var nodeInfo = currentColumn.nodeInfo[ nodeId ];
       
            var hoverPath = currentColumn.canvas.path( nodeInfo.collapsed.pathString ).attr( {
                stroke: viewer.config.collapsedCladeColor,
                'stroke-width': 1,
                fill: viewer.config.collapsedCladeColor } );

            var hiddenHover =
                make('div').attr( { 'class': 'hiddenHover', nodeId: nodeId } )
                                .height( ( nodeInfo.collapsed.collapseUIHeightByTwo * 2 ) )
                                .width( - nodeInfo.dx )
                                .css( { top: nodeInfo.y - nodeInfo.collapsed.collapseUIHeightByTwo,
                                        left: nodeInfo.x + nodeInfo.dx } )
                                .bind( 'mouseenter', { }, $.proxy( this.showCollapseDetail, this ) )
                                .bind( 'mouseleave', { renderObj: this }, this.hideCollapseDetail ).appendTo( currentColumn.svgDiv );
    
    
            var label = currentColumn.canvas.text( nodeInfo.x + viewer.config.tipLabelBuffer, nodeInfo.y, nodeInfo.collapsed.text )
                                        .attr( { stroke: 'none',
                                                 fill: viewer.config.treeColor,
                                                 "font-family": viewer.config.fontFamily,
                                                 "font-size": viewer.config.fontSize,
                                                 "text-anchor": "start" } );

            if( nodeInfo.label ) {
                label.attr( { x: nodeInfo.raphaelLabel.getBBox().x + nodeInfo.raphaelLabel.getBBox().width + viewer.config.tipLabelBuffer } );
            }

            nodeInfo.hiddenHover = { el: hiddenHover, path: hoverPath, label: label };

            var collapseDetail = make('div').attr( { 'class': 'expandOptionContainer contextMenu' } )
                                                 .css( { top: - nodeInfo.collapsed.collapseUIHeightByTwo, left: - nodeInfo.dx } ).appendTo( hiddenHover )
                                                 .bind( 'mouseenter', { renderObj: this }, this.vertScrollCheck )
                                                 .bind( 'mouseleave', { renderObj: this }, this.vertUnScrollCheck );
        
            collapseDetail.attr( { 'topPos': collapseDetail.css('top'), 'leftPos': collapseDetail.css('left') } );
            collapseDetail.css( { top: -1000, left: -1000 } );

            /*
            var text = ( nodeInfo.label )
                ? [ nodeInfo.label, " (", nodeInfo.collapsed.descendantCount, " nodes)" ].join("")
                : [ '(', nodeInfo.collapsed.descendantCount, ' nodes)' ].join("");
            */

            var text = nodeInfo.collapsed.text;

            var nodeCountRow = make('div').attr( { 'class': 'centerText' } ).text( text ).appendTo( collapseDetail );

            var verticalExpandOption = make('div').attr( { 'class': 'expandOption menuOptionItem' } ).append(
                make('div').attr( { 'class': 'fLeft' } ).height( 20 ).width( 20 ).append(
                    make('div').attr( { 'class': 'vertExpandUI' } ) ),
                make('div').attr( { 'class': 'fLeft' } ).css( { 'padding-left': '5px' } ).text( 'Expand Vertically' ),
                make('div').attr( { 'class': 'clear' } ) ).appendTo( collapseDetail )
              .bind( 'click', { renderObj: this, columnIndex: currentColumn.index, nodeId: nodeId }, this.verticallyExpandNode )
              .bind( 'click', { }, BioSync.OptionsMenu.hideContextMenu );

            collapseDetail.append( this.getHorizontalOption( { columnIndex: currentColumn.index, nodeId: nodeId } ) );

            collapseDetail.width( collapseDetail.outerWidth( true ) + 25 ); 

            var descendantLabelInfo = 
                    make('div').attr( { 'class': 'descendantLabelContainer' } ).text('View Descendant Labels')
                               .bind( 'mouseenter', { }, this.showDescendantLabels )
                               .bind( 'mouseleave', { }, this.hideDescendantLabels ).appendTo( collapseDetail );


            var labelListWrapper = make('div').attr( { 'class': 'labelListWrapper' } ).appendTo( descendantLabelInfo ).width( '100%' );

            var labelList = make('div').attr( { 'class': 'descendantList', 'nodeId': nodeInfo.id } ).appendTo( labelListWrapper ).width( '100%' ).height( '100%' );

            $.ajax( { url: BioSync.Common.makeUrl( { controller: 'plugin_treeViewer', argList: [ 'getDescendantLabels' ] } ),
                      type: "GET", context: this, data: { nodeId: nodeInfo.id }, success: this.handleDescendantLabels } );

            /*
            for( var j = 0, jj = nodeInfo.collapsed.descendantLabels.length; j < jj; j++ ) {
                 labelList.append( make('div').attr( { 'class': 'descendantLabel' } ).text( nodeInfo.collapsed.descendantLabels[j] )
                                              .bind( 'click', { viewer: viewer,
                                                                columnIndex: viewer.currentColumnIndex,
                                                                label: nodeInfo.collapsed.descendantLabels[j] }, this.horizontallyExpandNode ) );
             }

             if( labelListWrapper.height() > 150 ) { labelListWrapper.height( 150 ); }

             var collapseDetailOffset = collapseDetail.offset();
             var descendantLabelOffset = descendantLabelInfo.offset();

            var collapseDetailHeight = collapseDetail.outerHeight( { margin: true } );
            var collapseDetailWidth = collapseDetail.outerWidth( { margin: true } );

            if( collapseDetailOffset.top > ( ( currentColumn.myBottom - currentColumn.myOffset.top ) / 2 ) ) {
                labelListWrapper.css( { top: collapseDetailHeight - labelListWrapper.outerHeight( { margin: true } ), left: collapseDetailWidth } );
            } else {
                labelListWrapper.css( { top: 0, left: collapseDetailWidth } );
            }

             make('div').attr( { 'class': 'hoverBridge' } )
                        .css( { top: 0, left: descendantLabelInfo.width() } )
                        .height( collapseDetailHeight ).width( 25 ).appendTo( descendantLabelInfo );

             collapseDetail.hide();
             labelListWrapper.hide();
             */
        }
    },

    handleDescendantLabels: function( response ) {

        var response = eval( "(" + response + ")" );

        var labelList = $( [ '.descendantList[nodeId="', response.nodeId, '"]' ].join('') );
        var labelListWrapper = $( labelList.parent() );
        var descendantLabelInfo = $( labelListWrapper.parent() );
        var collapseDetail = $( descendantLabelInfo.parent() );
        var currentColumn = this.currentColumn;


        for( var i = 0, ii = response.labels.length; i < ii; i++ ) {

            var label = response.labels[i];

            labelList.append( this.make('div').attr( { 'class': 'descendantLabel' } ).text( label.text )
                                              .bind( 'click', { viewer: this.viewer,
                                                                columnIndex: this.viewer.currentColumnIndex,
                                                                label: label.text }, this.horizontallyExpandNode ) );
        }

        if( labelListWrapper.height() > 150 ) { labelListWrapper.height( 150 ); }

        var collapseDetailOffset = collapseDetail.offset();
        var descendantLabelOffset = descendantLabelInfo.offset();

        var collapseDetailHeight = collapseDetail.outerHeight( { margin: true } );
        var collapseDetailWidth = collapseDetail.outerWidth( { margin: true } );

        if( collapseDetailOffset.top > ( ( currentColumn.myBottom - currentColumn.myOffset.top ) / 2 ) ) {
            labelListWrapper.css( { top: collapseDetailHeight - labelListWrapper.outerHeight( { margin: true } ), left: collapseDetailWidth } );
        } else {
            labelListWrapper.css( { top: 0, left: collapseDetailWidth } );
        }
        
        this.make('div').attr( { 'class': 'hoverBridge' } )
                        .css( { top: 0, left: descendantLabelInfo.width() } )
                        .height( collapseDetailHeight ).width( 25 ).appendTo( descendantLabelInfo );

        collapseDetail.hide().css( { top: collapseDetail.attr('topPos'), left: collapseDetail.attr('leftPos') } );
        labelListWrapper.hide();

    },

    showCollapseDetail: function( e ) {

        var renderObj = this;

        if( ( BioSync.Common.isContextMenuVisible() ) || ( renderObj.viewPanel.hasClass('scrolling') ) ) { return; }

        if( renderObj.vertScroll == true ) { renderObj.vertScroll = false; return; }

        var hiddenHover = $(e.target).addClass('dragHighlight');
        var expandOptionBox = $( hiddenHover.children('div.expandOptionContainer')[0] ).show();

        var expandBoxOffset = expandOptionBox.offset();
        var viewPanelOffset = renderObj.viewPanel.offset();

        var horiDifference = ( expandBoxOffset.left + expandOptionBox.outerWidth( true ) ) -
                             ( viewPanelOffset.left + renderObj.viewPanel.outerWidth( true ) );

        if( horiDifference > 0 ) {
            renderObj.viewPanel.animate( { scrollLeft: '+=' + horiDifference }, 1000 );
        }
    },

    hideCollapseDetail: function( p ) {

        $(this).children('div.expandOptionContainer').hide(); $(this).removeClass('dragHighlight');
    },

    vertScrollCheck: function( p ) {

        if( BioSync.Common.isContextMenuVisible() ) { return; }

        var renderObj = p.data.renderObj;

        var collapseDetailEl = $( this );
        var viewPanel = renderObj.viewPanel;

        var collapseDetailOffset = collapseDetailEl.offset();
        var viewPanelOffset = viewPanel.offset();

        var vertDifference = ( collapseDetailOffset.top + collapseDetailEl.outerHeight( true ) ) -
                             ( viewPanelOffset.top + viewPanel.outerHeight( true ) ); 
    
        if( vertDifference > 0 ) {
            viewPanel.animate( { scrollTop: '+=' + vertDifference }, 1000 );
            renderObj.vertScroll = true;
        }
    },

    vertUnScrollCheck: function( p ) {

        var renderObj = p.data.renderObj;

        if( renderObj.vertScroll == true ) {

            setTimeout( function() { viewer.vertScroll = false; }, 500 );
        }
    },

    showDescendantLabels: function( p ) {
        $(this).children('div.labelListWrapper').show();
    },

    hideDescendantLabels: function( p ) {
        $(this).children('div.labelListWrapper').hide();
    },

    addNodeSelector: function( p ) {

        var viewer = this.viewer;
        var eventObj = viewer.events;

        this.currentColumn.nodeSelector =
            this.currentColumn.canvas.circle( 0, 0, viewer.config.nodeSelectorRadius )
                .attr( { fill: viewer.config.nodeSelectorColor,
                         stroke: viewer.config.nodeSelectorColor,
                         "fill-opacity": .7,
                         "stroke-width": viewer.config.pathWidth } ).hide();
                        
        $( this.currentColumn.nodeSelector.node ).bind( 'mousedown', { renderObj: this, column: this.currentColumn }, this.handleNodeClick );

        this.currentColumn.container.bind( 'mousemove', { renderObj: this, column: this.currentColumn }, this.updateNodeSelector );
    },

    getNodePathString: function( p ) {

        if( p.nodeInfo.isCollapsed ) { return ''; }

        var pathString = new BioSync.Common.StringBuffer();

        var childCount = p.nodeInfo.children.length;

        pathString.append( [ "M", p.nodeInfo.x, " ", p.nodeInfo.y, "l", p.nodeInfo.dx, " 0" ].join("") );

        if( childCount ) {

            if( childCount == 1 ) {

                var tipSep = this.viewer.config.verticalTipBuffer;

                var childY = p.column.nodeInfo[ p.nodeInfo.children[0] ].y;
                var lastChildY = p.column.nodeInfo[ p.nodeInfo.children[ childCount-1 ] ].y;

                pathString.append( [ "M", p.nodeInfo.x, " ", childY - ( tipSep / 4 ) , "l0 ", ( tipSep / 2 ) ].join("") );

            } else {
                
                var firstChildY = p.column.nodeInfo[ p.nodeInfo.children[0] ].y;
                var lastChildY = p.column.nodeInfo[ p.nodeInfo.children[ childCount-1 ] ].y;

                pathString.append( [ "M", p.nodeInfo.x, " ", firstChildY, "L", p.nodeInfo.x, " ", lastChildY ].join("") );
            }
        }

        return pathString.toString();
    },

    getCladePathString: function( p ) {

        var pathString = new BioSync.Common.StringBuffer();

        pathString.append( this.getNodePathString( p ) );

        if( ! p.nodeOnly ) {

            for( var i = 0, ii = p.nodeInfo.children.length; i < ii; i++ ) {
                pathString.append( this.getCladePathString( { column: p.column, nodeInfo: p.column.nodeInfo[ p.nodeInfo.children[i] ] } ) );    
            }
        }

        return pathString.toString();

    },

    unHighlightClade: function( p ) {

        for( var i = 0, ii = this.columns.length; i < ii; i++ ) {

            if( this.columns[i].currentHighlight ) {

                for( var j = 0, jj = this.columns[i].currentHighlight.length; j < jj; j++ ) {
                    this.columns[i].currentHighlight[j].remove();
                }
            }
        }
    },

    highlightClade: function( p ) {

        var nodeInfo = p.column.nodeInfo[ p.nodeId ];

        var selectionPath = this.getCladePathString( { column: p.column, nodeInfo: nodeInfo, nodeOnly: p.nodeOnly } );

        var canvasObj = p.column.canvas.path( selectionPath ).attr( {
            stroke: ( p.color ) ? p.color : 'red',
            "stroke-linecap": 'square',
            "stroke-width": this.viewer.config.pathWidth } );

        if( ! p.column.currentHighlight ) { p.column.currentHighlight = new Array(); }

        p.column.currentHighlight.push( canvasObj );

        if( p.column.index < this.columns.length - 1 ) {

            var expandedNodeId = p.column.container.find('.expanded').attr('nodeId');
            var expandedNode = p.column.nodeInfo[ expandedNodeId ];

            if( this.viewer.isAncestor( { ancestor: nodeInfo, descendant: expandedNode } ) ) {

                for( var i = p.column.index + 1, ii = this.columns.length; i < ii; i++ ) {
                
                    this.highlightClade( { column: this.columns[i], nodeId: this.columns[i].rootId, color: p.color } );
                }
            }
        }
    },

    handleNodeClick: function( p ) {

        var renderObj = p.data.renderObj;
        var viewer = renderObj.viewer;
        var eventObj = viewer.events;

        if( p.which == 3 && viewer.events.nodeRightClick ) {

            var eventObj = viewer.events.nodeRightClick;

            if( eventObj.type == 'contextMenu' ) {

                var options = [];

                for( var i = 0, ii = eventObj.options.length; i < ii; i++ ) {

                    var option = eventObj.options[ i ];

                    var handler = ( option.external )
                        ? viewer.externalHandlers[ option.handler ]
                        : renderObj.eventHandlers[ option.handler ];

                    options.push( { text: option.text,
                                    action: handler,
                                    params: { optionDef: option,
                                              column: p.data.column,
                                              renderObj: renderObj,
                                              nodeId: $( this ).attr('nodeId') } } );
                }
                    
                BioSync.OptionsMenu.makeContextMenu( { coords: { x: p.pageX, y: p.pageY }, options: options } );
            }
        }
    },

    updateNodeSelector: function( p ) {

        var renderObj = p.data.renderObj;
        var column = p.data.column;
        var nodeSelector = column.nodeSelector;

        if( $('#modalBoxContainer' ).is(':visible') ) { return true; }

        if( BioSync.Common.isContextMenuVisible() || BioSync.Common.symbolDragInfo || renderObj.viewPanel.hasClass('scrolling') ) { nodeSelector.hide(); return true; }

        var closestNodeInfo = renderObj.getClosestNode( {
            coords: renderObj.translateDOMToCanvas( { x: p.pageX, y: p.pageY, column: column } ),
            currentNodeId: column.rootId,
            column: column } );

        if( ( closestNodeInfo.distance < 50 ) && ( column.collapsedNodeIds.indexOf( closestNodeInfo.id ) == -1 ) ) {

            nodeSelector.attr( { cx: column.nodeInfo[ closestNodeInfo.id ].x, cy: column.nodeInfo[ closestNodeInfo.id ].y } ).show().toFront();
            $( nodeSelector.node ).attr( { 'nodeId': closestNodeInfo.id } );

        } else {

            nodeSelector.hide();
        }
    },

    getClosestNode: function( p ) {

        var nodeDict = p.column.nodeInfo;
        var currentNode = nodeDict[ p.currentNodeId ];

        var distance = Math.sqrt( Math.pow( p.coords.x - currentNode.x, 2) + Math.pow( p.coords.y - currentNode.y, 2) );

        if( !p.currentDistance || ( distance < p.currentDistance ) ) { p.currentDistance = distance; p.closestId = p.currentNodeId; }

        var childCount = currentNode.children.length;
        
        if( childCount ) {

            var recursiveParams =
                { coords: p.coords,
                  column: p.column,
                  closestId: p.closestId,
                  currentDistance: p.currentDistance };

            if( p.coords.y < nodeDict[ currentNode.children[0] ].y ) {
                recursiveParams.currentNodeId = currentNode.children[0];
                var result = this.getClosestNode( recursiveParams );
                if( result.id != p.closestId ) { return { distance: result.distance, id: result.id }; }
            }

            else if( p.coords.y > nodeDict[ currentNode.children[ childCount - 1] ].y ) {
                recursiveParams.currentNodeId = currentNode.children[ childCount - 1];
                var result = this.getClosestNode( recursiveParams );
                if( result.id != p.closestId ) { return { distance: result.distance, id: result.id }; }
            }

            else {
                for( var i = 0, ii = childCount; i < ii; i++ ) {
                   recursiveParams.currentNodeId = currentNode.children[ i ];
                   var result = this.getClosestNode( recursiveParams );
                   if( result.id != p.closestId ) {
                       recursiveParams.closestId = p.closestId = result.id;
                       recursiveParams.currentDistance = p.currentDistance = result.distance;
                   }
                }
            }
        }

        return { id: p.closestId, distance: p.currentDistance };
    },

    translateDOMToCanvas: function( p ) {
    
        var column = p.column;

        return { x: p.x - ( column.myPosition.left + this.viewPanel.myOffset.left - this.viewPanel.scrollLeft() ),
                 y: p.y - ( column.myPosition.top + this.viewPanel.myOffset.top + column.centerOffset - this.viewPanel.scrollTop() ) }
    }
};
