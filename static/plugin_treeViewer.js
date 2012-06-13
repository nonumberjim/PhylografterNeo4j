BioSync.TreeViewer = { 

    instances: { },

    viewer: function() { return this; },
    
    RenderUtil: {

        phylogram: {

            browse: function( ) {
                
                BioSync.Common.loadCSS( { name: 'jquery-ui-1.8.5.custom' } );
 
                return this;
            },

            navigate: function( ) {
                
                BioSync.Common.loadCSS( { name: 'jquery-ui-1.8.5.custom' } );

                return this;
            }
        },

        d3: {

            forceDirected: function( viewer ) {
            
                this.viewer = viewer;
               
                BioSync.Common.loadScript( { name: 'd3/d3' } );
                BioSync.Common.loadScript( { name: 'd3/d3.geom' } );
                BioSync.Common.loadScript( { name: 'd3/d3.layout' } );
                BioSync.Common.loadCSS( { name: 'forceDirected' } );

                if( ! viewer.events.nodeRightClick ) {

                    viewer.events.nodeRightClick = {
                        type: 'action',
                        handler: 'unFixNode' };
                }

                viewer.events.nodeDoubleClick.options.push(
                    { type: 'depends',
                      test: { handler: 'isFixed',
                              fixed: { handler: 'unFixNode', text: 'Unpin' },
                              unFixed: { handler: 'fixNode', text: 'Pin' } } } );

            },

            sunburst: function( viewer ) {
            
                this.viewer = viewer;
              
                BioSync.Common.loadScript( { name: 'd3/d3' } );
                BioSync.Common.loadScript( { name: 'd3/d3.layout' } );
                BioSync.Common.loadCSS( { name: 'sunburst' } );
            }
        }
    },

    Sidebar: {

        phylogram: {

            browse: function( viewer ) { this.viewer = viewer; this.make = BioSync.Common.makeEl; return this; },

            navigate: function( viewer ) {

                this.viewer = viewer;
                this.make = BioSync.Common.makeEl;
                return this;
            }
        }
    },

    Menu: {

        phylogram: {

            browse: function( viewer ) { this.viewer = viewer; this.make = BioSync.Common.makeEl; return this; },

            navigate: function( viewer ) {

                this.viewer = viewer;
                this.make = BioSync.Common.makeEl;
                return this;
            }
        },

        d3: {
            forceDirected: { },
            sunburst: { }
            }
    }
}

BioSync.TreeViewer.viewer.prototype = {

    start: function( p ) {

        this.containerId = p.containerId;
        this.treeType = p.treeType;
        this.menuInfo = p.menuInfo;

        this.events = ( 'eventInfo' in p ) ? p.eventInfo : { };
        
        this.renderType = ( p.viewInfo.renderType ) ? p.viewInfo.renderType : 'phylogram';
        this.viewMode = ( p.viewInfo && p.viewInfo.mode ) ? p.viewInfo.mode : 'browse';
        this.viewInfo = p.viewInfo;
        this.auxPlugins = p.auxPlugins;

        this.allNodesHaveLength = p.allNodesHaveLength;

        this.make = BioSync.Common.makeEl;

        this.isModal = ( p.modal == 'True' ) ? true : false;

        this.renderResponse = p.renderInfo;

        this.renderObj = this.getRenderObj();
        
        this.requestConfig();

        this.container = $('#' + this.containerId).addClass('treeViewerContainer').height( '100%' ).width( '100%' );

        //not sure where this is getting triggered... but its preventing browser context menu
        $(document).bind( 'contextmenu', BioSync.Common.preventDefault );

        if( $('#footer').height() > 0 ) {

            //eh
            //setTimeout( function() { viewer.onWindowLoad( viewer ); }, 2000 );
            this.onWindowLoad();

        } else {

            $(document).bind( 'windowLoaded', { }, $.proxy( viewer.onWindowLoad, this ) );
        }

        return this;
    },

    addPanel: function( p ) {

        if( ! this.sidebar ) {

            BioSync.Common.loadScript( { name: [ this.renderType, 'Sidebar' ].join('') } );
           
            this.sidebar = new BioSync.TreeViewer.Sidebar[ this.renderType ][ this.viewMode ]( this ).initialize();
        }

        this.sidebar.addPanel( p );
    },
    
    togglePanel: function( e ) {

        var target = $( e.target );
        var label;

        if( target.hasClass('controlPanelItemLabel') ) { label = target; }
        else { label = $( target.children()[0] ); }

        var panelContainer = $( $( $( [ ".panelName:contains('", label.attr('name'), "')" ].join('') ).parent() ).parent() );

        if( $( label.parent() ).attr('check') == 'true' )  {

            this.showHeader( panelContainer );

        } else {
            
            panelContainer.hide( 'slide', { direction: 'right' }, 1000 );
        }
    },

    getRenderObj: function( p ) {

        // add error handler for this
        BioSync.Common.loadScript( { name: this.renderType } );

        return new BioSync.TreeViewer.RenderUtil[ this.renderType ][ this.viewMode ]().start( this );
    },

    updateConfig: function( p ) {

        for( var i = 0, ii = p.names.length; i < ii; i++ ) {

            this.config[ p.names[i] ] = p.values[i];
        }

        $.ajax( { url: BioSync.Common.makeUrl( { controller: 'plugin_treeViewer', argList: [ 'updateConfig' ] } ),
                  data: { names: p.names.join(','), vals: p.values.join(',') }, 
                  type: 'GET', async: false, context: this.renderObj, success: ( p.redraw ) ? this.renderObj.redrawTree : function() { } } );
    },

    externalHandlers: {

        getUrlForm: function( p, q ) {

            var option = p.data.optionDef;

            var url = option.url;

            if( option.urlArgs ) {

                for( var i = 0, ii = option.urlArgs.length; i < ii; i++ ) {

                    url += [ '/', p.data[ option.urlArgs[i] ] ].join('');
                }
            }

            BioSync.ModalBox.getUrlForm( { title: option.text, url: url, successTrigger: option.successTrigger, successData: p.data } );
        }
    },

    requestConfig: function() {

        $.ajax( { url: BioSync.Common.makeUrl( { controller: 'plugin_treeViewer', argList: [ 'getConfig' ] } ),
                 type: 'GET', async: false, context: this, success: this.handleConfigResponse } );
    },

    handleConfigResponse: function( response ) { this.config = eval( "(" + response + ")" ); },

    requestAuxilliaryPlugins: function( plugins ) {

        if( !plugins ) { return; }

        for( var i = 0, ii = plugins.length; i < ii; i++ ) {
        
            var plugin = plugins[ i ];
            var id = [ 'pluginContainer' + i ].join('');
        
            this.container.append( this.make('div').attr( { 'id': id  } ) );

            web2py_ajax_page(
                    'get',
                    BioSync.Common.makeUrl( { controller: 'plugin_' + plugin.name, argList: [ [ plugin.use, '.load' ].join('') ] } ),
                    { containerId: this.containerId },
                    id,
                    function() { } );
        }
    },

    postViewerHeight: function() {

        $.ajax( { url: BioSync.Common.makeUrl( { controller: 'plugin_treeViewer', argList: [ 'setTreeViewerHeight', this.myHeight  ] } ),
                 type: "GET", async: false } );
    },

    assignWrapperHeight: function() {

       var footer = $('#footer');
       BioSync.Common.storeObjPosition( footer, footer );
      
       this.container.height( $(window).height() - ( footer.myHeight + footer.myOffset.top ) );
    },

    onWindowLoad: function() { 

        this.assignWrapperHeight();
     
        BioSync.Common.storeObjPosition( this.container, this );

        this.postViewerHeight();

        this.renderObj.initialize();

        if( this.isModal ) {

            this.container.appendTo( $('#modalBoxForm') );

            BioSync.ModalBox.showModalBox( { content: undefined, title: 'Your Tree', height: '75%' } );
        }

        if( this.renderResponse ) { this.renderObj.renderReceivedTree(); }

        else { this.getTree(); }

        if( this.menuInfo ) {

            BioSync.Common.loadScript( { name: [ this.renderType, 'ControlPanel' ].join('') } );
            this.controlPanel = new BioSync.TreeViewer.Menu[ this.renderType ][ this.viewMode ]( this ).initialize();
        }

        this.requestAuxilliaryPlugins( this.auxPlugins );
    },

    getTree: function() {

       $.ajax( { url: BioSync.Common.makeUrl( { controller: 'plugin_treeViewer', argList: [ [ 'isTreePreProcessed' ].join('') ] } ),
                 type: 'GET', success: $.proxy( this.handleIsProcessedResponse, this ) } );

    },

    handleIsProcessedResponse: function( response ) {

        if( eval( "(" + response + ")" ).value == 'true' ) {
          
           this.actuallyGetTree(); 

        } else {

            BioSync.Common.notify( {
                text: 'This tree has not been pre processed.  Doing so now',
                timeoutTrigger: 'preProcessSuccess',
                dotdotdot: true,
                x: this.myOffset.left + ( this.myWidth / 2 ),
                y: this.myOffset.top + 10 } );

           $.ajax( { url: BioSync.Common.makeUrl( { controller: 'plugin_treeViewer', argList: [ [ 'preProcessTree' ].join('') ] } ),
                     type: 'GET', success: $.proxy( this.handlePreProcessResponse, this ) } );
        }

    },

    handlePreProcessResponse: function( response ) {

        $(document).trigger( 'preProcessSuccess' );
        
        this.actuallyGetTree(); 
    },

    actuallyGetTree: function() {
       
       $.ajax( { url: BioSync.Common.makeUrl( { controller: 'plugin_treeViewer', argList: [ [ this.viewMode, 'GetTree' ].join('') ] } ),
                 type: 'GET', success: $.proxy( this.handleReceivedTree, this ) } );
    },

    handleReceivedTree: function( response ) {

        this.renderResponse = eval( "(" + response + ")" );
        this.renderObj.renderReceivedTree();
        if( this.sidebar ) { this.sidebar.updateHeaderCoords(); }
    },

    isAncestor: function( p ) {
                    
        return ( ( p.ancestor.next < p.descendant.next ) &&
                 ( p.ancestor.back > p.descendant.back ) ) ? true : false;
    },

    saveColorConfig: function( p ) {
                                           
        var viewer = p.data.viewer;

        var option = $('#colorOptions option:selected').val()
        var value = $('#configCurrentColor').text();

        viewer.config.colorOptions[ option ].value = value;
        viewer.config.colorOptions[ option ].update( { viewer: viewer, value: value } );
    },

    setPathString: function() { this.pathString = new BioSync.Common.StringBuffer(); },

    vertUnScrollCheck: function( p ) {

        var viewer = p.data.viewer;

        if( viewer.vertScroll == true ) {

            setTimeout( function() { viewer.vertScroll = false; }, 500 );
        }
    },

    vertScrollCheck: function( p ) {

        if( $('#contextMenu').length ) { return; }

        var viewer = p.data.viewer;
        var expandOptionBox = $( this );

        var expandBoxOffset = expandOptionBox.offset();
        var viewPanelOffset = viewer.viewPanel.offset();

        var vertDifference = ( expandBoxOffset.top + expandOptionBox.outerHeight( true ) ) -
                             ( viewPanelOffset.top + viewer.viewPanel.outerHeight( true ) ); 
    
        if( vertDifference > 0 ) {
            viewer.viewPanel.animate( { scrollTop: '+=' + vertDifference }, 1000 );
            viewer.vertScroll = true;
        }
    },

    showExpandOptions: function( p ) {

        if( $('#contextMenu').length ) { return; }

        var viewer = p.data.viewer;

        if( viewer.vertScroll == true ) { viewer.vertScroll = false; return; }

        var hiddenHover = $(this).addClass('dragHighlight');
        var expandOptionBox = $( hiddenHover.children('div.expandOptionContainer')[0] ).show();

        var expandBoxOffset = expandOptionBox.offset();
        var viewPanelOffset = viewer.viewPanel.offset();

        var horiDifference = ( expandBoxOffset.left + expandOptionBox.outerWidth( true ) ) -
                             ( viewPanelOffset.left + viewer.viewPanel.outerWidth( true ) );

        if( horiDifference > 0 ) {
            viewer.viewPanel.animate( { scrollLeft: '+=' + horiDifference }, 1000 );
        }
    },

    hideExpandOptions: function( p ) { if( $('#contextMenu').length ) { return; } $(this).children('div.expandOptionContainer').hide(); $(this).removeClass('dragHighlight'); },

    getNodeIdString: function( p ) {
        
        p.nodeList.push( p.node.id );

        for( var i = 0, ii = p.node.children.length; i < ii; i++ ) {
            p.nodeList.concat( this.getNodeIdString( { node: p.node.children[i], nodeList: p.nodeList } ) );
        }

        return p.nodeList;
    },

    handleNodeClick: function( p ) {

        var viewer = p.data.viewer;

        if( p.which == 1 && viewer.events.nodeClick ) {
            
        } else if( p.which == 3 && viewer.events.nodeRightClick ) {

            var eventObj = viewer.events.nodeRightClick;

            if( eventObj.type == 'contextMenu' ) {

                var options = [];

                for( var i = 0, ii = eventObj.options.length; i < ii; i++ ) {

                    var option = eventObj.options[ i ];

                    var handler = ( option.external )
                        ? viewer.externalHandlers[ option.handler ]
                        : viewer.renderUtil.eventHandlers[ option.handler ];

                    options.push( { text: option.text,
                                    action: handler,
                                    params: { nodeId: $( p.data.nodeSelector.node ).attr('nodeId'),
                                              column: p.data.column,
                                              viewer: viewer } } );
                }
        
                BioSync.OptionsMenu.makeContextMenu( { coords: { x: p.pageX, y: p.pageY }, options: options } );
            }
        }
    },

    getCladePathString: function( p ) {

        var pathString = new BioSync.Common.StringBuffer();

        pathString.append( this.getNodePathString( p ) );

        for( var i = 0, ii = p.node.children.length; i < ii; i++ ) {
            pathString.append( this.getCladePathString( { node: p.node.children[i] } ) );    
        }

        return pathString.toString();
    },

    cladeHighlight: function( p ) {

        var node = this.nodes[ p.nodeId ];

        var selectionPath = this.getCladePathString( { node: node } );

        if( node.isHighlighted ) {

            this.highlightPathString = this.highlightPathString.replace( selectionPath, '' );

            this.highlightPathString = $.trim( this.highlightPathString );

            this.highlightPathSvgObj.attr( { path: this.highlightPathString } );

            node.isHighlighted = false;

        } else {

            if( this.highlightPathSvgObj == undefined ) {
                this.highlightPathString = selectionPath;
                this.highlightPathSvgObj = this.canvas.path( selectionPath ).attr( { stroke: '#CEE8F0', "stroke-width": this.config.pathWidth } );
            } else {
                this.highlightPathString += ' ' + selectionPath;
                this.highlightPathSvgObj.attr( { path: this.highlightPathString } );
            }
            
            node.isHighlighted = true;
        }
    },

    getClosestNode: function( p ) {

        var nodeCoords = { x: p.node.x, y: p.node.y };

        var distance = Math.sqrt( Math.pow( p.coords.x - nodeCoords.x, 2) + Math.pow( p.coords.y - nodeCoords.y, 2) );

        if( !p.currentDistance || distance < p.currentDistance ) { p.currentDistance = distance; p.closestNode = p.node; p.closestId = p.nodeId; }

        var childCount = p.node.children.length;
        
        if( childCount ) {

            var recursiveParams =
                { coords: { x: p.coords.x, y: p.coords.y },
                  nodeInfo: p.nodeInfo,
                  closestNode: p.closestNode,
                  closestId: p.closestId,
                  currentDistance: p.currentDistance };
        
            if( p.coords.y < p.nodeInfo[ p.node.children[0] ].y ) {
                recursiveParams.node = p.nodeInfo[ p.node.children[0] ];
                recursiveParams.nodeId = p.node.children[0];
                var result = this.getClosestNode( recursiveParams );
                if( result.id != p.closestId ) { return { node: result.node, distance: result.distance, id: result.id }; }
            }

            else if( p.coords.y > p.nodeInfo[ p.node.children[ childCount - 1] ].y ) {
                recursiveParams.node = p.nodeInfo[ p.node.children[ childCount - 1] ];
                recursiveParams.nodeId = p.node.children[ childCount - 1];
                var result = this.getClosestNode( recursiveParams );
                if( result.id != p.closestId ) { return { node: result.node, distance: result.distance, id: result.id }; }
            }

            else {
                for( var i = 0, ii = childCount; i < ii; i++ ) {
                   recursiveParams.node = p.nodeInfo[ p.node.children[ i ] ];
                   recursiveParams.nodeId = p.node.children[ i ];
                   var result = this.getClosestNode( recursiveParams );
                   if( result.id != p.closestId ) {
                       recursiveParams.closestNode = p.closestNode = result.node;
                       recursiveParams.closestId = p.closestId = result.id;
                       recursiveParams.currentDistance = p.currentDistance = result.distance;
                   }
                }
            }
        }

        return { node: p.closestNode, id: p.closestId, distance: p.currentDistance };
    },

    getConfigColorDropdownOptions: function( p ) {

        var viewer = this;
        var elList = [];
        var colorOptions = viewer.config.colorOptions;
        var make = BioSync.Common.makeEl;

        for( var value in colorOptions ) {
            elList.push( make('option').attr( { 'value': value } ).text( colorOptions[value].text ).get(0) );
        }

        return elList;
    },

    handleUserSearch: function( p ) {

        var viewer = p.data.viewer;
        
        var listItems = $('#modalBoxForm').find('.userItem')
        
        if( p.keyCode == 8 || p.keyCode == 46 || String.fromCharCode( p.keyCode ).match( /\w/ ) ) {

            listItems.show();

            var regExp = new RegExp( $('#userSearch').val(), 'gi' );

            for( var i = 0, ii = listItems.length; i < ii; i++ ) {

                var listItem = $( listItems[ i ] );

                if( ! listItem.text().match( regExp ) ) {

                    listItem.hide();
                }
                
            }
        }
    },

    removeUserSearchDefaultText: function( p ) {

        $('#userSearch').select().unbind('focus');

    },

    showModalCollaborationOptions: function( p ) {

        var viewer = p.data.viewer;

        var make = BioSync.Common.makeEl;

        $.ajax( { url: BioSync.Common.makeUrl( { controller: 'plugin_treeGrafter', argList: [ 'getCurrentCollaborators', viewer.treeId ] } ),
                          type: "GET",
                          async: false,
                          context: viewer,
                          success: function( response ) { viewer.collabInfo = eval( "(" + response + ")" ); } } );

        var bodyHeight = $('body').height();
        var bodyWidth = $('body').width();
         
        $('#modalBoxForm').append(
            make('div').append(
                BioSync.ModalBox.makeBasicTextRow( { 'text': 'You are the owner of this grafted tree.  Here, you can specify who has the ability to edit this tree.  Click and drag a name to update their permissions.' } ),
                make('div').attr( { 'class': 'autoMargin' } ).width( bodyWidth / 3 ).append(
                    make('div').attr( { 'class': 'fLeft' } ).append(
                        make('div').text('View Only').attr( { 'class': 'centerText bold' } ).css( { 'padding': '5px' } ),
                            make('div').attr( { 'id': 'viewOnlyContainer', 'class': 'userListContainer' } ).height( bodyHeight / 4 ) ),
                    make('div').attr( { 'class': 'fRight' } ).append(
                        make('div').text('View/Edit').attr( { 'class': 'centerText bold' } ).css( { 'padding': '5px' } ),
                            make('div').attr( { 'id': 'viewEditContainer', 'class': 'userListContainer' } ).height( bodyHeight / 4 ) ),
                    make('div').attr( { 'class': 'clear' } ) ),
                make('div').attr( { 'class': 'padding10 autoMargin' } ).width( bodyWidth / 8 ).append(
                        make('input').attr( { 'id': 'userSearch', 'class': 'centerText autoMargin', 'value': 'search for a user here' } ).width( bodyWidth / 8 )
                                     .bind( 'focus', { viewer: viewer }, viewer.removeUserSearchDefaultText )
                                     .bind( 'keyup', { viewer: viewer }, viewer.handleUserSearch ) ) ) );


        

        for( var attr in viewer.collabInfo ) {

            var container = $( [ '#', attr, 'Container' ].join('') );
            var otherContainer = ( attr == 'viewOnly' ) ? $('#viewEditContainer') : $('#viewOnlyContainer' );

            for( var i = 0, ii = viewer.collabInfo[ attr ].length; i < ii; i++ ) {

                var user = viewer.collabInfo[ attr ][ i ];
                var domObj = make('div').attr( { 'userId': user.id, 'class': 'dashedBorderBottom nowrap userItem' } )
                                        .text( user.name )
                                        .css( { 'padding': '10px 10px 10px 10px' } )
                                        .draggable( { receptacle: otherContainer, receptacleFun: viewer.updatePermissions, receptacleFunParams: { userId: user.id, viewer: viewer }  } );

                container.append( domObj );
            }
        }
      
        BioSync.ModalBox.showModalBox( { content: undefined, title: 'Manage Collaboration' } );

        setTimeout(
            function() {
                if( $('#viewEditContainer').width() > $('#viewOnlyContainer').width() ) {
                    $('#viewOnlyContainer').width( $('#viewEditContainer').width() );
                    $('#viewEditContainer').width( $('#viewEditContainer').width() );
                } else {
                    $('#viewEditContainer').width( $('#viewOnlyContainer').width() );
                    $('#viewOnlyContainer').width( $('#viewOnlyContainer').width() );
                }

                /*BioSync.Common.addHoverCloseIcon( {
                    whiteBackground: true,
                    topRight: true,
                    el: $('#modalBoxForm'),
                    func: function() { BioSync.ModalBox.closeBox(); } } );*/

            }, 2000 );
    },

    updatePermissions: function( p ) {

        var viewer = p.viewer;

        $.ajax( { url: BioSync.Common.makeUrl( { controller: 'plugin_collaboration', argList: [ 'updateCollaboration' ] } ),
                  type: "GET",
                   context: viewer,
                   data: { treeId: viewer.treeId, userId: p.userId },
                   success: function() {
        
                       var selector = [ '.userItem[userId="', p.userId, '"]' ].join('');

                       if( $('#viewEditContainer').find( selector )[0] ) {

                            $( selector ).appendTo( $('#viewOnlyContainer' ) ).show('slow')
                                         .draggable( { receptacle: $('#viewEditContainer'),
                                                       receptacleFun: viewer.updatePermissions,
                                                       receptacleFunParams: { userId: p.userId, viewer: viewer }  } );

                        } else {
                            
                            $( selector ).appendTo( $('#viewEditContainer' ) ).show('slow')
                                         .draggable( { receptacle: $('#viewOnlyContainer'),
                                                       receptacleFun: viewer.updatePermissions,
                                                       receptacleFunParams: { userId: p.userId, viewer: viewer }  } );
                        } } } );
    },

    
};




/*
    collaborateMakeOption: function( p ) {

        var viewer = p.viewer;

        if( viewer.treeType == 'grafted' ) {

            $.ajax( { url: BioSync.Common.makeUrl( { controller: 'plugin_treeGrafter', argList: [ 'isTreeOwner', viewer.treeId ] } ),
                      type: "GET",
                      async: false,
                      context: viewer,
                      data: { },
                      success: function( response ) { viewer.isOwner = eval( "(" + response + ")" ); } } );

            if( viewer.isOwner ) {

                return { text: 'Manage Collaborators', funcParams: { viewer: viewer }, func: new Array( viewer.showModalCollaborationOptions, viewer.menuUtil.hideConfigMenu ) };

            } else {

                return { };
            }

        } else { return { }; }
    },
*/

$(window).load( function() { $(document).trigger( 'windowLoaded' ); } );
