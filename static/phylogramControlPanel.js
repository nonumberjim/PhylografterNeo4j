BioSync.TreeViewer.Menu.phylogram.navigate.prototype = {

    config: { leftBuffer: 10,
              rightBuffer: 20,
              bottomBuffer: 10,
              sliderSize: 100 },

    search: function( controlPanel ) {

            this.controlPanel = controlPanel; this.make = BioSync.Common.makeEl;
            BioSync.Common.loadCSS( { name: 'treeViewerSearch' } );
            return this;
    },

    initialize: function() {

         this.panelButton =
            this.make('div').attr( { 'class': 'controlPanelButton' } )
                            .hoverIntent( $.proxy( this.showControlPanel, this ), $.proxy( this.hideControlPanel, this ) )
                            .appendTo( this.viewer.container ).append(
                                this.make( 'span' ).text( 'control panel' ).attr( { 'class': 'controlPanelText' } ) );

        this.createMenuOptions();

        return this;
    },

    addViewOption: function( p ) {

        var viewOption;

        if( ! this.panelContent.find(".controlPanelItemLabel:contains('view >')").length ) {

            viewOption =
                this.make('div').attr( { 'class': 'controlPanelItem' } ).append(
                    this.make('span').attr( { 'class': 'controlPanelItemLabel' } ).text( 'view > ' ) )
                        .hoverIntent( $.proxy( this.showChildHoverMenu, this ), $.proxy( this.hideChildHoverMenu, this ) );

            this.panelContent.append( viewOption );

        } else {

            viewOption = $( this.panelContent.children(":contains('view')") );
        }

        viewOption.append(
            this.make( 'div' ).attr( { 'class': 'controlPanelItem', 'check': 'true' } ).append(
                this.make( 'span' ).attr( { 'class': 'controlPanelItemLabel', 'name': p.name } ).html( [ p.name, ' ', BioSync.Common.htmlCodes.check ].join(' ') ) )
            .bind( 'click', { }, this.toggleCheck )
            .bind( 'click', { }, $.proxy( this.viewer.togglePanel, this.viewer ) ) );
    },

    toggleCheck: function() {

        var that = $(this);
        var label = $( that.children()[0] );

        if( that.attr('check') == 'true' ) {

            that.attr( { 'check': 'false' } );
            label.html( label.html().substring( 0, label.html().indexOf(' ') ) );

        } else { 
            
            that.attr( { 'check': 'true' } );
            label.html( [ label.html(), BioSync.Common.htmlCodes.check ].join(' ') );
        } 
    },

    showControlPanel: function() {

        this.panelButton.attr( { 'oldHeight': this.panelButton.height(),
                                 'oldWidth': this.panelButton.width() } );

        $( this.panelButton.children()[0] ).addClass('showContent');

        this.panelContent.css( { 'padding-top': '10px',
                                 'position': 'relative',
                                 'left': '10px',
                                 'white-space': 'nowrap',
                                 'padding-right': '5px' } ).children().show();


        this.panelButton.height( ( ( this.panelContent.offset().top + this.panelContent.outerHeight( true ) ) - this.panelButton.offset().top ) + this.config.bottomBuffer )
                        .width( ( ( this.panelContent.offset().left + this.panelContent.outerWidth( true ) ) - this.panelButton.offset().left ) + this.config.rightBuffer );
    },
    
    hideControlPanel: function( ) {

        if( ! this.panelButton.attr('oldWidth') ) { return; }

        var that = this;

        $('.controlPanelItem').each( function( i ) {

            var el = $(this);

            if( el.children().is(':visible') ) {

                that.hideChildHoverMenu( { target: el } );
            }
        } );

        that.panelButton.width( that.panelButton.attr('oldWidth') ).removeAttr('oldWidth');

        that.panelButton.height( that.panelButton.attr('oldHeight') ).removeAttr('oldHeight');
        
        $( that.panelButton.children()[0] ).removeClass('showContent');

        that.panelContent.css( { 'padding-top': '0px',
                                 'position': 'static',
                                 'left': '0px',
                                 'padding-right': '0px' } ).children().hide();
    },

    createMenuOptions: function() {
                
        this.panelContent = this.make('div').attr( { 'class': 'controlPanelContent' } ).appendTo( this.panelButton );

        for( var i = 0, ii = this.viewer.menuInfo.options.length; i < ii; i++ ) {
            
            var name = this.viewer.menuInfo.options[ i ].name;
            this[ [ 'get', BioSync.Common.capitalizeFirstLetter( name ), 'Option' ].join('') ]();
        }
    },

    getTreeSizeOption: function() {

        //cb-i don't like this:
        var label1 = this.make('span').attr( { 'class': 'sliderLabel' } ).text( 'branch length :' ).appendTo( this.viewer.container );
        var label1Width = label1.outerWidth( true );
        var value1 = this.make('span').attr( { 'class': 'sliderValue' } ).text( this.viewer.config.branchLength ).appendTo( this.viewer.container );
        var value1Width = value1.outerWidth( 'true' );

        var label2 = this.make('span').attr( { 'class': 'sliderLabel' } ).text( 'leaf buffer :' ).appendTo( this.viewer.container );
        var label2Width = label2.outerWidth( true );
        var value2 = this.make('span').attr( { 'class': 'sliderValue' } ).text( this.viewer.config.verticalTipBuffer ).appendTo( this.viewer.container );
        var value2Width = value2.outerWidth( 'true' );

        var label3 = this.make('span').attr( { 'class': 'sliderLabel' } ).text( 'font size :' ).appendTo( this.viewer.container );
        var label3Width = label3.outerWidth( true );
        var value3 = this.make('span').attr( { 'class': 'sliderValue' } ).text( this.viewer.config.fontSize ).appendTo( this.viewer.container );
        var value3Width = value3.outerWidth( 'true' );

        var label4 = this.make('span').attr( { 'class': 'sliderLabel' } ).text( 'max tips :' ).appendTo( this.viewer.container );
        var label4Width = label4.outerWidth( true );
        var value4 = this.make('span').attr( { 'class': 'sliderValue' } ).text( this.viewer.config.maxTips ).appendTo( this.viewer.container );
        var value4Width = value4.outerWidth( 'true' );

        this.panelContent.append(
            this.make('div').attr( { 'class': 'controlPanelItem' } ).append(
                this.make('span').attr( { 'class': 'controlPanelItemLabel' } ).text( 'tree size >' ) )
                            .hoverIntent( $.proxy( this.showChildHoverMenu, this ), $.proxy( this.hideChildHoverMenu, this ) ).append(
                    this.make('div').attr( { 'class': 'controlPanelItem' } ).append(
                        this.make('div').attr( { 'class': 'sliderContainer' } ).css( { 'width': this.config.sliderSize + label1Width + value1Width + 10 } ).append(
                            label1,
                            this.make('div').attr( { 'class': 'treeSizeSlider' } ).css( { 'width': this.config.sliderSize } ).append(
                                this.make('div').slider( { max: 100, min: 1,
                                                           value: this.viewer.config.branchLength,
                                                           slide: function( e, ui ) { value1.text( ui.value ); },
                                                           change: $.proxy( this.changeBranchLength, this ) } ) ),
                            value1,
                            this.make('div').attr( { 'class': 'clear' } ) ) ),
                    this.make('div').attr( { 'class': 'controlPanelItem' } ).append(
                        this.make('div').attr( { 'class': 'sliderContainer' } ).css( { 'width': this.config.sliderSize + label2Width + value2Width + 10 } ).append(
                            label2,
                            this.make('div').attr( { 'class': 'treeSizeSlider' } ).css( { 'width': this.config.sliderSize } ).append(
                                this.make('div').slider( { max: 100, min: 1,
                                                           value: this.viewer.config.verticalTipBuffer,
                                                           slide: function( e, ui ) { value2.text( ui.value ); },
                                                           change: $.proxy( this.changeVerticalTipBuffer, this ) } ) ),
                            value2,
                            this.make('div').attr( { 'class': 'clear' } ) ) ),
                    this.make('div').attr( { 'class': 'controlPanelItem' } ).append(
                        this.make('div').attr( { 'class': 'sliderContainer' } ).css( { 'width': this.config.sliderSize + label4Width + value4Width + 10 } ).append(
                            label4,
                            this.make('div').attr( { 'class': 'treeSizeSlider' } ).css( { 'width': this.config.sliderSize } ).append(
                                this.make('div').slider( { max: 500, min: 50,
                                                           step: 50,
                                                           value: this.viewer.config.maxTips,
                                                           slide: function( e, ui ) { value4.text( ui.value ); },
                                                           change: $.proxy( this.changeMaxTips, this ) } ) ),
                            value4,
                            this.make('div').attr( { 'class': 'clear' } ) ) ),
                    this.make('div').attr( { 'class': 'controlPanelItem' } ).append(
                        this.make('div').attr( { 'class': 'sliderContainer' } ).css( { 'width': this.config.sliderSize + label3Width + value3Width + 10 } ).append(
                            label3,
                            this.make('div').attr( { 'class': 'treeSizeSlider' } ).css( { 'width': this.config.sliderSize } ).append(
                            this.make('div').slider( { max: 50, min: 1,
                                                       value: this.viewer.config.fontSize,
                                                       slide: function( e, ui ) { value3.text( ui.value ); },
                                                       change: $.proxy( this.changeFontSize, this ) } ) ),
                            value3,
                            this.make('div').attr( { 'class': 'clear' } ) ) ) ) );

        $('.ui-slider').css( { 'top': '7px' } );
    },

    changeMaxTips: function( e, ui ) {

        this.hideControlPanel();

        this.viewer.updateConfig( { names: [ 'maxTips' ], values: [ ui.value ], redraw: true } );
    },

    changeFontSize: function( e, ui ) {

        this.hideControlPanel();

        BioSync.Common.style.fontSize = ui.value;
        BioSync.Common.setTextWidthMetric();

        this.viewer.updateConfig( { names: [ 'fontSize' ], values: [ ui.value ], redraw: true } );
    },

    changeVerticalTipBuffer: function( e, ui ) {
        
        this.hideControlPanel();

        this.viewer.updateConfig( { names: [ 'verticalTipBuffer' ], values: [ ui.value ], redraw: true } );
    },

    changeBranchLength: function( e, ui ) {

        this.hideControlPanel();

        this.viewer.updateConfig( { names: [ 'branchLength' ], values: [ ui.value ], redraw: true } );
    },

    //not being used (zoom)
    ratioChange: function( e, ui ) {

        var scaleRatio = ui.value / this.baseRatio;
        this.baseRatio = ui.value;

        //this.viewer.renderObj.changeTreeSize( { ratio: this.viewer.renderObj.scaleRatio } );

        var config = this.viewer.config;

        var ajaxNames = [ 'fontSize', 'scaleRatio', 'branchLength', 'horizontalPadding', 'verticalPadding', 'tipLabelBuffer', 'verticalTipBuffer' ];
        var ajaxValues = [  ];

        for( var i = 0, ii = ajaxNames.length; i < ii; i++ ) {

            var name = ajaxNames[i];
            config[ name ] = config[ name ] * scaleRatio;
            ajaxValues.push( config[ name ] );
        }

        BioSync.Common.style.fontSize = config.fontSize;
        BioSync.Common.setTextWidthMetric();

        this.viewer.updateConfig( { names: ajaxNames, values: ajaxValues, redraw: true } );
    },

    getSearchOption: function() {

        this.panelContent.append(
            this.make('div').attr( { 'class': 'controlPanelItem' } ).append(
                            this.make('span').attr( { 'class': 'controlPanelItemLabel' } ).text( 'search >' ) )
                                .hoverIntent( $.proxy( this.showChildHoverMenu, this ), $.proxy( this.hideChildHoverMenu, this ) ).append(
               this.make('div').attr( { 'class': 'controlPanelItem' } ).append(
                   new this.search( this ).initialize() ) ) );
    },

    getBranchLengthOption: function() {

        var viewer = this.viewer;
        
        //#$.ajax( { url: BioSync.Common.makeUrl( { controller: 'plugin_treeViewer', argList: [ 'areThereBranchLengths' ] } ),
                  //#async: false, type: "GET", data: { treeId: viewer.treeId }, success: function( r ) { viewer.areThereBranchLengths = eval( "(" + r + ")" ); } } );

         if( this.viewer.allNodesHaveLength ) {

            this.panelContent.append(
                this.make('div').attr( { 'class': 'controlPanelItem branchLengthOption' } ).append( 
                                this.make('span').attr( { 'class': 'controlPanelItemLabel' } ).text( 'branch style >' ) )
                                .hoverIntent( $.proxy( this.showChildHoverMenu, this ), $.proxy( this.hideChildHoverMenu, this ) ).append(
                    this.make('div').attr( { 'class': 'controlPanelItem', value: 'scale' } ).append(
                        this.make('span').attr( { 'class': 'controlPanelItemLabel' } ).text( "Scale" ) ),
                    this.make('div').attr( { 'class': 'controlPanelItem', value: 'smooth', check: 'true' } ).append(
                       this.make('span').attr( { 'class': 'controlPanelItemLabel' } ).html( [ "Smooth", BioSync.Common.htmlCodes.check ].join(' ' ) ) ) ) );
            
            $('.branchLengthOption').children().click( $.proxy( this.updateBranchLength, this ) );
        }
    },

    updateBranchLength: function( e ) {

        this.hideControlPanel();

        var clickedItem;
        var clickedItemLabel;

        if( $(e.target).hasClass('controlPanelItemLabel') ) {

            clickedItemLabel = $( e.target );
            clickedItem = $( clickedItemLabel.parent() );

        } else { 
            
            clickedItemLabel = $( $( e.target ).find('.controlPanelItemLabel')[0] );
            clickedItem = $( e.target );
        }

        if( clickedItem.attr('check') != 'true' ) {
     
            var formerlySelected = $( clickedItem.siblings('div[check="true"]') );
            var formerlySelectedLabel = $( formerlySelected.find('.controlPanelItemLabel')[0] );
            var html = formerlySelectedLabel.html();

            formerlySelectedLabel.html( html.substring( 0, html.indexOf(' ') ) );
            formerlySelected.attr( { check: 'false' } );

            //clickedItemLabel.html( [ clickedItemLabel.html(), '&#x2713;' ].join(' ') ).attr( { check: 'true' } );
            clickedItemLabel.html( [ clickedItemLabel.html(), BioSync.Common.htmlCodes.check ].join(' ') ).attr( { check: 'true' } );
            clickedItem.attr( { check: 'true' } );
            this.viewer.renderObj.updateBranchLength( clickedItem.attr('value') );
        }
    },

    showChildHoverMenu: function( e ) {

        var that = this;

        var parent = $( e.target );

        if( ! parent.attr('inUse') ) {
            if( parent.hasClass('controlPanelItemLabel') ) { parent = $( parent.parent() ); }
            if( ! parent.children('.controlPanelItem').length ) {
                parent = $( parent.closest('.controlPanelItem[inUse]') );
            }
        } else if( parent.attr('inUse') == 'true' ) { return; }
        
        var parentSibs = parent.siblings();
        if( parentSibs.filter( '.controlPanelItem[inUse="true"]' ).length ) {

            var inUse =  $( parentSibs.filter( '.controlPanelItem[inUse="true"]' )[0] );
            var shouldReturn = false;

            inUse.children('.controlPanelItem').each( function() {
                
                if( BioSync.Common.isMouseOnElement( { x: e.x, y: e.y, el: $( this ) } ) ) { shouldReturn = true; } } );
            
            if( shouldReturn ) { return; }
        }
        
        parent.css( { position: 'relative' } );

        parent.attr( { 'oldWidth': parent.width(), 'oldHeight': parent.height(), 'inUse': 'true' } ).children().show();

        var rightEdge = 0;
        var widestChild = 0;

        var label = parent.children('.controlPanelItemLabel').addClass('parentHover');
        var labelWidth = label.outerWidth( true );

        parent.children('.controlPanelItem').each( function( i ) {

            var el = $(this); 
            var top = ( i == 0 ) ? 0 : ( parseInt( $( el.prev() ).css('top') ) + $( el.prev() ).outerHeight( true ) );

            el.css( { 'position': 'absolute',
                      'z-index': 500,
                      'top': top,
                      'left': labelWidth + that.config.leftBuffer } );

            if( el.outerWidth( true ) + labelWidth + that.config.leftBuffer > rightEdge ) { rightEdge = el.outerWidth( true ) + labelWidth + that.config.leftBuffer; }
            if( el.outerWidth( true ) > widestChild ) { widestChild = el.outerWidth( true ); }

        } );

        parent.children('.controlPanelItem').width( widestChild );

        var parentsLastSibling = $( parent.parent().children().filter(':last') );
        var lastChild = $( parent.children().filter(':last') );
               
        var bottomEdge = parentsLastSibling.offset().top + parentsLastSibling.outerHeight( true );

        if( bottomEdge < lastChild.offset().top + lastChild.outerHeight( true ) ) {
            bottomEdge = lastChild.offset().top + lastChild.outerHeight( true );
        }

        parent.width( rightEdge + that.config.rightBuffer );

        this.panelButton.height( bottomEdge - this.panelButton.offset().top )
                        .width( ( parent.offset().left + rightEdge + that.config.rightBuffer ) - this.panelButton.offset().left );
    },
    
    hideChildHoverMenu: function( e ) {

        var parent = $( e.target );
        
        if( ! parent.attr( 'inUse' ) ) {
          
            parent = $( parent.closest('.controlPanelItem[inUse="true"]') );
            if( ! parent.length ) { return; }
        }

        parent.attr( { 'inUse': 'false' } );

        parent.children('.controlPanelItem').hide();
        parent.width( parent.attr('oldWidth') );
        parent.children('.controlPanelItemLabel').removeClass('parentHover');
        
        var parentsLastSibling = $( parent.parent().children().filter(':last') );
        var bottomEdge = parentsLastSibling.offset().top + parentsLastSibling.outerHeight( true );
        var rightEdge = parent.offset().left + parent.outerWidth( true );
    }
}


BioSync.TreeViewer.Menu.phylogram.navigate.prototype.search.prototype = {

    initialize: function() {

        var that = this;

        this.container =
            this.make('div').attr( { 'class': 'searchContainer' } )
                            .keyup( $.proxy( this.handleKeyUp, this ) )
                            .mouseout( $.proxy( this.handleMouseOut, this ) );
       
        this.inputDOM =
            this.make('input').attr( { 'id': 'treeViewerSearch',
                                       'type': 'text',
                                       'value': 'label or taxon',
                                       'class': 'labelSearchInput initialLabelInput' } )
                              .focus( $.proxy( this.firstInputFocus, this ) ).
                              appendTo( this.container );

        this.matchingLabelList =
            this.make('div').attr( { 'class': 'searchMatchingLabels' } )
                .hover( function() { that.hoveringResults = true; }, function() { that.hoveringResults = false; } )
                .appendTo( this.container );

        return this.container;
    },

    firstInputFocus: function( e ) {
       
        this.inputDOM.val('').removeClass('initialLabelInput').unbind('focus'); 
    },

    handleMouseOut: function( e ) {

        var that = this;

        setTimeout( function() {
            if( ! that.hoveringResults ) {
                that.matchingLabelList.empty().css( { width: '' } );
                that.inputDOM.val('');
            } }, 250 );

    },

    handleArrowAndMouseSearch: function() {

        var that = this;

        //if there is a mouse cursor visible
        if( ! that.matchingLabelList.hasClass('noCursor') ) {

            this.matchingLabelList.addClass('noCursor');

            //mouseenter happens with invisible mouse
            $('.searchResult').unbind( 'mouseenter mouseleave' );

            //make everything normal when mouse moves again
            $( document ).mousemove( function() {

                that.matchingLabelList.removeClass('noCursor');
                
                that.setSearchHover();
            } );
        }
    },

    setSearchHover: function() {
        
        $('.searchResult').unbind( 'mouseenter mouseleave' ).hover(
            function() { $('.searchSelected').removeClass('searchSelected'); $( this ).addClass('searchSelected'); },
            function() { $( this ).removeClass('searchSelected'); } );
    },

    handleSearchAutoScroll: function( p ) {

        var that = this;

        //scrolling makes the mouse move
        $(document).unbind('mousemove');

        //scroll and on success function
        this.matchingLabelList.animate( { scrollTop: '+=' + p.scroll }, 250, 'linear',

            //on success make things normal agagin
            function() { $( document ).mousemove( function() {

                that.matchingLabelList.removeClass('noCursor');

                that.setSearchHover();
            } );
        } );
    },

    handleKeyUp: function( e ) {

        var that = this;
        //enter
        if( e.keyCode == 13 ) {

            $('.searchSelected').click();

        //down arrow
        } else if( e.keyCode == 40 ) {

            this.handleArrowAndMouseSearch();

            var currentlySelected = $('.searchSelected');

            if( currentlySelected.length ) {

                if( currentlySelected.attr('nodeId') != $('.searchResult').filter(':last').attr('nodeId') ) {

                    var newlySelected = currentlySelected.next().addClass('searchSelected');
                    currentlySelected.removeClass('searchSelected');

                    if( newlySelected.offset().top + newlySelected.outerHeight( true ) >
                        this.matchingLabelList.offset().top + this.matchingLabelList.outerHeight( true ) ) {

                        this.handleSearchAutoScroll( { scroll: newlySelected.outerHeight( true ) } );
                    }
                }

            } else {

                $( $('.searchResult')[0] ).addClass('searchSelected');
            }

        //up arrow
        } else if( e.keyCode == 38 ) {
            
            this.handleArrowAndMouseSearch();

            var currentlySelected = $('.searchSelected');

            if( currentlySelected.length ) {

                if( currentlySelected.attr('nodeId') != $( $('.searchResult')[0] ).attr('nodeId') ) {

                    var newlySelected = currentlySelected.prev().addClass('searchSelected');

                    if( newlySelected.offset().top < this.matchingLabelList.offset().top ) {

                        this.handleSearchAutoScroll( { scroll: -( newlySelected.outerHeight( true ) ) } );
                    }

                } else {

                    $('#treeViewerSearch').focus().select();
                }
                
                currentlySelected.removeClass('searchSelected');

            } else {

                $('#treeViewerSearch').focus().select();
            }
           
        //letter 
        } else if( e.keyCode == 8 || e.keyCode == 46 || String.fromCharCode( e.keyCode ).match( /\w/ ) ) {

            if( this.userInputTimeout ) { clearTimeout( this.userInputTimeout ); }

            this.userInputTimeout = setTimeout( $.proxy( this.getMatchingLabels, this ), 500 );
        }
    },
   
    getMatchingLabels: function() {

        if( this.inputDOM.val() != '' ) {
            $.ajax( { url: BioSync.Common.makeUrl( { controller: 'plugin_treeViewer', argList: [ 'getMatchingLabels' ] } ),
                      type: "GET", context: this, data: { treeId: this.controlPanel.viewer.treeId, value: this.inputDOM.val() }, success: this.handleMatchingLabels } );
        } else {
            this.matchingLabelList.empty();
        }
    },

    labelSelected: function( e ) {

        var el = $( $( e.target ).closest( "[nodeId]" ) );

        this.controlPanel.viewer.renderObj.navigateToNode( { nodeId: el.attr('nodeId') } );
        this.controlPanel.viewer.controlPanel.hideControlPanel();
    },

    handleMatchingLabels: function( response ) {

        var shortResults = true;

        this.matchingLabelList.empty();

        if( this.inputDOM.is(':hidden') ) { return; }
            
        BioSync.Common.storeObjPosition( this.inputDOM, this.inputDOM );
        var longestResult = this.inputDOM.myWidth - 2;

        this.matchingLabelList.css( { 'left': 0,
                                      'top': this.inputDOM.myHeight } ).show();

        var matchingLabels = eval( '(' + response + ')' );
        
        for( var i = 0, ii = matchingLabels.length; i < ii; i++ ) {

            var matchingLabel = matchingLabels[i];

            var text = ( matchingLabel.taxon.name == matchingLabel.snode.label )
                ? this.make('span').text( matchingLabel.snode.label )
                : ( ( matchingLabel.taxon.name ) && ( matchingLabel.snode.label ) )
                    ? this.make('div').append(
                        this.make('span').attr( { 'class': 'searcResultTaxonLabel' } ).text( "Taxon: " ),
                        this.make('span').text( matchingLabel.taxon.name ),
                        this.make('span').attr( { 'class': 'searchResultLabelLabel' } ).text( "Label: " ),
                        this.make('span').text( matchingLabel.snode.label ) )
                    : ( matchingLabel.taxon.name ) ? this.make('span').text( matchingLabel.taxon.name )
                                                   : this.make('span').text( matchingLabel.snode.label );
           
            var result = this.make('div').css( { 'font-weight' : 'bold' } ).attr( { 'class': 'searchResult', 'nodeId': matchingLabel.snode.id } ).append( text )
                                .hover( function() {
                                     $('.searchSelected').removeClass('searchSelected');
                                     $( this ).addClass('searchSelected'); }, function() { $( this ).removeClass('searchSelected'); } )
                                .click( $.proxy( this.labelSelected, this ) );

            this.matchingLabelList.append( result );
            
            var outerWidth = result.outerWidth( true );
            result.css( { 'font-weight': '' } ); 
            if( outerWidth > longestResult ) { longestResult = outerWidth; shortResults = false; }
        }

        // le sigh
        longestResult += BioSync.Common.scrollbarWidth;

        if( ! shortResults ) { longestResult += BioSync.Common.scrollbarWidth; }

        this.matchingLabelList.width( longestResult );

        var controlPanelButton = this.controlPanel.panelButton;
        controlPanelButton.height( this.matchingLabelList.offset().top + this.matchingLabelList.outerHeight( true ) - controlPanelButton.offset().top );

        controlPanelButton.width( this.matchingLabelList.offset().left + this.matchingLabelList.outerWidth( true ) - controlPanelButton.offset().left );
    }
}
