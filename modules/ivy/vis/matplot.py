"""
interactive viewers for trees, etc. using matplotlib
"""
import sys, time, bisect, math, types, os, operator
from pprint import pprint
from .. import layout, tree
from ..storage import Storage
import matplotlib, numpy
import matplotlib.pyplot as pyplot
from matplotlib.figure import SubplotParams, Figure
from matplotlib.axes import SubplotBase, Axes, subplot_class_factory
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path
from matplotlib.widgets import RectangleSelector
from matplotlib.transforms import Bbox, offset_copy
from matplotlib import cm as mpl_colormap
from matplotlib import colors as mpl_colors
from matplotlib.colorbar import Colorbar
from matplotlib.collections import RegularPolyCollection
from mpl_toolkits.axes_grid.anchored_artists import AnchoredText
import shapes, colors

matplotlib.rcParams['path.simplify'] = False

_tango = colors.tango()

class TreeFigure:
    """
    Window for showing a single tree, optionally with split overview
    and detail panes.

    The navigation toolbar at the bottom is provided by matplotlib
    (http://matplotlib.sf.net/users/navigation_toolbar.html).  Its
    pan/zoom button and zoom-rectangle button provide different modes
    of mouse interaction with the figure.  When neither of these
    buttons are checked, the default mouse bindings are as follows:

    * button 1 drag: select nodes - retrieve by calling fig.selected_nodes()
    * button 3 drag: pan view
    * scroll up/down: zoom in/out
    * scroll up/down with Control key: zoom y-axis
    * scroll up/down with Shift key: zoom x-axis
    * scroll up/down with 'd' key: pan view up/down
    * click on overview will center the detail pane on that region
    
    Default keybindings:

    * t: zoom out to full extent
    * +/-: zoom in/out

    Useful attributes and methods (assume an instance named *fig*):

    * fig.root - the root node (see [Node methods])
    * fig.highlight(s) - highlight and trace nodes with substring *s*
    * fig.zoom_clade(anc) - zoom to view node *anc* and all its descendants
    * fig.toggle_overview() - toggle visibility of the overview pane
    * fig.toggle_branchlabels() - ditto for branch labels
    * fig.toggle_leaflabels() - ditto for leaf labels
    * fig.div(n) - set the relative width of the overview pane (0 < *n* < 1)
    * fig.decorate(func) - decorate the tree with a function (see
      :ref:`decorating TreeFigures <decorating-trees>`)
    """
    def __init__(self, data, name=None, scaled=True, div=0.25,
                 branchlabels=True, leaflabels=True, overview=True):
        self.name = name
        self.div_value = div
        self.scaled = scaled
        self.branchlabels = branchlabels
        self.leaflabels = leaflabels
        self.highlighted = set()
        if isinstance(data, tree.Node):
            root = data
        else:
            root = tree.read(data)
        self.root = root
        if not self.root:
            raise IOError, "cannot coerce data into tree.Node"
        self.name = self.name or root.treename
        pars = SubplotParams(
            left=0, right=1, bottom=0.05, top=1, wspace=0.01
            )
        fig = pyplot.figure(subplotpars=pars, facecolor="white")
        connect_events(fig.canvas)
        self.figure = fig
        tp = TreePlot(fig, 1, 2, 2, app=self, name=self.name,
                      scaled=self.scaled, branchlabels=self.branchlabels,
                      leaflabels=self.leaflabels)
        ax2 = fig.add_subplot(tp)
        ax2.plot_tree(self.root)
        self.detail = ax2
        ax1 = fig.add_subplot(
            OverviewTreePlot(fig, 121, app=self, snap=False, scaled=scaled,
                             branchlabels=False,
                             leaflabels=False,
                             target=self.detail)
            ).plot_tree(self.root)
        self.overview = ax1
        if not overview:
            self.toggle_overview(False)
        self.set_positions()

        if self.detail.nleaves < 50:
            self.toggle_overview()

        ## self.figure.canvas.mpl_connect("resize_event", self.detail.draw_label
        ## self.figure.canvas.mpl_connect("idle_event", self.detail.unclutter)

    def selected_nodes(self):
        return self.detail.selected_nodes

    def add(self, data, name=None, support=70,
            branchlabels=False, leaflabels=True):
        newfig = MultiTreeFigure()
        ## newfig.add(self.root, name=self.name, support=self.support,
        ##            branchlabels=self.branchlabels)
        newfig.add(data, name=name, support=support,
                   branchlabels=branchlabels,
                   leaflabels=leaflabels)
        return newfig

    def toggle_leaflabels(self):
        self.leaflabels = not self.leaflabels
        self.detail.leaflabels = self.leaflabels
        self.redraw()

    def toggle_branchlabels(self):
        self.branchlabels = not self.branchlabels
        self.detail.branchlabels = self.branchlabels
        self.redraw()

    def toggle_overview(self, val=None):
        if val is None:
            if self.overview.get_visible():
                self.overview.set_visible(False)
                self.div(0.001)
            else:
                self.overview.set_visible(True)
                self.div(0.25)
        elif val:
            self.overview.set_visible(True)
            self.div(0.25)
        else:
            self.overview.set_visible(False)
            self.div(0.001)

    def set_scaled(self, scaled):
        for p in self.overview, self.detail:
            p.redraw(p.set_scaled(scaled))
        self.set_positions()

    def on_nodes_selected(self, treeplot):
        pass

    def picked(self, e):
        try:
            print e.artist.get_text()
            sys.stdout.flush()
        except:
            pass
    
    def ladderize(self, rev=False):
        self.root.ladderize(rev)
        self.redraw()

    def show(self):
        self.figure.show()

    def set_positions(self):
        p = self.overview
        p.set_position([0, p.xoffset(), self.div_value, 1.0-p.xoffset()])
        p = self.detail
        p.set_position(
            [self.div_value, p.xoffset(),
             1.0-self.div_value, 1.0-p.xoffset()]
            )
        self.figure.canvas.draw_idle()

    def div(self, v=0.3):
        assert 0 <= v < 1
        self.div_value = v
        self.set_positions()
        self.figure.canvas.draw_idle()

    def redraw(self):
        self.detail.redraw()
        self.overview.redraw()
        self.highlight()
        self.set_positions()
        self.figure.canvas.draw_idle()
        
    def find(self, x):
        return self.root.findall(x)

    def highlight(self, x=None):
        if x:
            nodes = set()
            if type(x) in types.StringTypes:
                nodes = self.root.findall(x)
            elif isinstance(x, tree.Node):
                nodes = set(x)
            else:
                for n in x:
                    if type(n) in types.StringTypes:
                        found = self.root.findall(n)
                        if found:
                            nodes |= set(found)
                    elif isinstance(n, tree.Node):
                        nodes.add(n)
                
            self.highlighted = nodes
        else:
            self.highlighted = set()
        self.overview.highlight(self.highlighted)
        self.detail.highlight(self.highlighted)
        self.figure.canvas.draw_idle()

    def home(self):
        self.overview.home()
        self.detail.home()

    def zoom_clade(self, x):
        """
        Zoom to fit a node *x* and all its descendants in the view.
        """
        if not isinstance(x, tree.Node):
            x = self.root[x]
        self.detail.zoom_clade(x)

    def zoom(self, factor=0.1):
        "Zoom both axes by *factor* (relative display size)."
        self.detail.zoom(factor, factor)
        self.figure.canvas.draw_idle()

    def zx(self, factor=0.1):
        "Zoom x axis by *factor*."
        self.detail.zoom(factor, 0)
        self.figure.canvas.draw_idle()

    def zy(self, factor=0.1):
        "Zoom y axis by *factor*."
        self.detail.zoom(0, factor)
        self.figure.canvas.draw_idle()

    def decorate(self, func, *args, **kwargs):
        """
        Decorate the tree.

        *func* is a function that takes a TreePlot instance as the
        first parameter, and *args* and *kwargs* as additional
        parameters.  It adds boxes, circles, etc to the TreePlot.

        If *kwargs* contains the key-value pair ('store', *name*),
        then the function is stored as *name* and re-called every time
        the TreePlot is redrawn, i.e., the decoration is persistent.
        Use ``rmdec(name)`` to remove the decorator from the treeplot.
        """
        self.detail.decorate(func, *args, **kwargs)

    def rmdec(self, name):
        "Remove the decoration 'name'."
        if name in self.detail.decorators:
            del self.detail.decorators[name]

    def cbar(self, node, width=6, color='blue'):
        pass

    def unclutter(self, *args):
        self.detail.unclutter()

    def trace_branches(self, nodes, width=4, color="blue"):
        for p in self.overview, self.detail:
            p.trace_branches(nodes, width, color)


class MultiTreeFigure:
    """
    Window for showing multiple trees side-by-side.

    TODO: document this
    """
    def __init__(self, trees=None, name=None, support=70,
                 scaled=True, branchlabels=False):
        """
        *trees* are assumed to be objects suitable for passing to
        ivy.tree.read()
        """
        self.root = []
        self.name = name
        self.name2plot = {}
        self.plots = []
        self.scaled = scaled
        self.branchlabels = branchlabels
        self.highlighted = set()
        self.divs = []
        pars = SubplotParams(
            left=0, right=1, bottom=0.05, top=1, wspace=0.04
            )
        fig = pyplot.figure(subplotpars=pars)
        connect_events(fig.canvas)
        self.figure = fig

        for x in trees or []:
            self.add(x, support=support, scaled=scaled,
                     branchlabels=branchlabels)

    def on_nodes_selected(self, treeplot):
        pass

    def clear(self):
        self.root = []
        self.name2plot = {}
        self.highlighted = set()
        self.divs = []
        self.figure.clf()

    def picked(self, e):
        try:
            print e.artist.get_text()
            sys.stdout.flush()
        except:
            pass

    def getplot(self, x):
        p = None
        try:
            i = self.root.index(x)
            return self.plots[i]
        except ValueError:
            return self.name2plot.get(x)

    def add(self, data, name=None, support=70, scaled=True,
            branchlabels=False, leaflabels=True):
        root = None
        if isinstance(data, tree.Node):
            root = data
        else:
            root = tree.read(data)
        if not root:
            raise IOError, "cannot coerce data into tree.Node"
        
        name = name or root.treename
        self.root.append(root)
            
        fig = self.figure
        N = len(self.plots)+1
        for i, p in enumerate(self.plots):
            p.change_geometry(1, N, i+1)
        p = fig.add_subplot(
            TreePlot(fig, 1, N, N, app=self, name=name, support=support,
                     scaled=scaled, branchlabels=branchlabels,
                     leaflabels=leaflabels)
            ).plot_tree(self.root[-1])
        p.index = N-1
        self.plots.append(p)
        if name:
            assert name not in self.name2plot
            self.name2plot[name] = p

        ## global IP
        ## if IP:
        ##     def f(shell, s):
        ##         self.highlight(s)
        ##         return sorted([ x.label for x in self.highlighted ])
        ##     IP.expose_magic("highlight", f)
        ##     def f(shell, s):
        ##         self.root.ladderize()
        ##         self.redraw()
        ##     IP.expose_magic("ladderize", f)
        ##     def f(shell, s):
        ##         self.show()
        ##     IP.expose_magic("show", f)
        ##     def f(shell, s):
        ##         self.redraw()
        ##     IP.expose_magic("redraw", f)
        return p

    def show(self):
        self.figure.show()

    def redraw(self):
        for p in self.plots:
            p.redraw()
        self.figure.canvas.draw_idle()
        
    def ladderize(self, reverse=False):
        for n in self.root:
            n.ladderize(reverse)
        self.redraw()

    def highlight(self, s=None, add=False):
        if not s:
            self.highlighted = set()
        if not add:
            self.highlighted = set()

        nodesets = [ p.root.findall(s) for p in self.plots ]

        for nodes, p in zip(nodesets, self.plots):
            if nodes:
                p.highlight(nodes)

        self.highlighted = nodesets
        self.figure.canvas.draw_idle()

        ##     for root in self.root:
        ##         for node in root.iternodes():
        ##             if node.label and (s in node.label):
        ##                 self.highlighted.add(node)
        ## self.highlight()
                
def connect_events(canvas):
    mpl_connect = canvas.mpl_connect
    mpl_connect("button_press_event", onclick)
    mpl_connect("button_release_event", onbuttonrelease)
    mpl_connect("scroll_event", onscroll)
    mpl_connect("pick_event", onpick)
    mpl_connect("motion_notify_event", ondrag)
    mpl_connect("key_press_event", onkeypress)
    mpl_connect("axes_enter_event", axes_enter)
    mpl_connect("axes_leave_event", axes_leave)

class UpdatingRect(Rectangle):
    def __call__(self, p):
        self.set_bounds(*p.viewLim.bounds)
        p.figure.canvas.draw_idle()

class Tree(Axes):
    """
    matplotlib.axes.Axes subclass for rendering trees.
    """
    def __init__(self, fig, rect, *args, **kwargs):
        self.app = kwargs.pop("app", None)
        self.support = kwargs.pop("support", 70.0)
        self.snap = kwargs.pop("snap", True)
        self.scaled = kwargs.pop("scaled", True)
        self.leaflabels = kwargs.pop("leaflabels", True)
        self.branchlabels = kwargs.pop("branchlabels", True)
        self._mark_named = kwargs.pop("mark_named", True)
        self.name = None
        Axes.__init__(self, fig, rect, *args, **kwargs)
        self.nleaves = 0
        self.callbacks.connect("ylim_changed", self.draw_labels)
        self.highlighted = None
        self.highlightpatch = None
        self.pan_start = None
        self.decorators = {
            "__selected_nodes__": (Tree.highlight_selected_nodes, [], {})
            }
        self.decorations = Storage()
        self._active = False

        self.selector = RectangleSelector(self, self.rectselect, useblit=True)
        def f(e):
            if e.button != 1: return True
            else: return RectangleSelector.ignore(self.selector, e)
        self.selector.ignore = f
        self.xoffset_value = 0.05
        self.selected_nodes = set()
        self.leaf_offset = 4
        self.leaf_valign = "center"
        self.leaf_halign = "left"
        self.leaf_fontsize = 10
        self.branch_offset = -5
        self.branch_valign = "center"
        self.branch_halign = "right"
        self.branch_fontsize = 10

        self.spines["top"].set_visible(False)
        self.spines["left"].set_visible(False)
        self.spines["right"].set_visible(False)
        self.xaxis.set_ticks_position("bottom")

    def p2y(self):
        "Convert a single display point to y-units"
        transform = self.transData.inverted().transform
        return transform([0,1])[1] - transform([0,0])[1]

    def p2x(self):
        "Convert a single display point to y-units"
        transform = self.transData.inverted().transform
        return transform([0,0])[1] - transform([1,0])[1]
    
    def decorate(self, func, *args, **kwargs):
        """
        Decorate the tree with function *func*.  If *kwargs* contains
        the key-value pair ('store', *name*), the decorator function
        is stored in self.decorators and called upon every redraw.
        """
        name = kwargs.pop("store", None)
        if name:
            v = (func, args, kwargs)
            self.decorators[name] = v
        func(self, *args, **kwargs)

    def flip(self):
        "Reverse the direction of the x-axis."
        self.leaf_offset *= -1
        self.branch_offset *= -1
        ha = self.leaf_halign
        self.leaf_halign = "right" if ha == "left" else "left"
        ha = self.branch_halign
        self.branch_halign = "right" if ha == "left" else "left"
        self.invert_xaxis()
        self.redraw()

    def xoffset(self):
        "Space below x axis to show tick labels."
        if self.scaled:
            return self.xoffset_value
        else:
            return 0
    
    def save_newick(self, filename):
        if os.path.exists(filename):
            s = raw_input("File %s exists, enter 'y' to overwrite ").strip()
            if (s and s.lower() != 'y') or (not s):
                return
        import newick
        f = file(filename, "w")
        f.write(newick.string(self.root))
        f.close()

    def set_scaled(self, scaled):
        flag = self.scaled != scaled
        self.scaled = scaled
        return flag

    def cbar(self, nodes, color=None, label=None, x=None, width=8, xoff=10,
             showlabel=True, mrca=True):
        """
        Draw a 'clade' bar (i.e., along the y-axis) indicating a
        clade.  *nodes* are assumed to be one or more nodes in the
        tree.  If just one, it should be the internal node
        representing the clade of interest; otherwise, the clade of
        interest is the most recent common ancestor of the specified
        nodes.  *label* is an optional string to be drawn next to the
        bar, *offset* by the specified number of display units.  If
        *label* is ``None`` then the clade's label is used instead.
        """
        xlim = self.get_xlim(); ylim = self.get_ylim()
        if color is None: color = _tango.next()
        transform = self.transData.inverted().transform

        if mrca:
            if isinstance(nodes, tree.Node):
                spec = nodes
            elif type(nodes) in types.StringTypes:
                spec = self.root.get(nodes)
            else:
                spec = self.root.mrca(nodes)

            assert spec in self.root
            label = label or spec.label
            leaves = spec.leaves()
            
        else:
            leaves = nodes

        n2c = self.n2c

        y = sorted([ n2c[n].y for n in leaves ])
        ymin = y[0]; ymax = y[-1]; y = (ymax+ymin)*0.5

        if x is None:
            x = max([ n2c[n].x for n in leaves ])
            _x = 0
            for lf in leaves:
                txt = self.node2label.get(lf)
                if txt and txt.get_visible():
                    _x = max(_x, transform(txt.get_window_extent())[1,0])
            if _x > x: x = _x

        v = sorted(list(transform(((0,0),(xoff,0)))[:,0]))
        xoff = v[1]-v[0]
        x += xoff

        self.plot([x,x], [ymin, ymax], '-', linewidth=width, color=color)

        if showlabel and label:
            xo = self.leaf_offset
            if xo > 0:
                xo += width*0.5
            else:
                xo -= width*0.5
            txt = self.annotate(
                label,
                xy=(x, y),
                xytext=(xo, 0),
                textcoords="offset points",
                verticalalignment=self.leaf_valign,
                horizontalalignment=self.leaf_halign,
                fontsize=self.leaf_fontsize,
                clip_on=True,
                picker=False
                )
        
        self.set_xlim(xlim); self.set_ylim(ylim)

    def anctrace(self, anc, descendants=None, width=4, color="blue"):
        if not descendants:
            descendants = anc.leaves()
        else:
            for d in descendants:
                assert d in anc
            
        nodes = []
        for d in descendants:
            v = d.rootpath(anc)
            if v:
                nodes.extend(v)
        nodes = set(nodes)
        nodes.remove(anc)
        self.trace_branches(nodes, width, color)

    def trace_branches(self, nodes, width=4, color="blue"):
        n2c = self.n2c
        M = Path.MOVETO; L = Path.LINETO
        verts = []
        codes = []
        for c, pc in [ (n2c[x], n2c[x.parent]) for x in nodes
                       if (x in n2c) and x.parent ]:
            x = c.x; y = c.y
            px = pc.x; py = pc.y
            verts.append((x, y)); codes.append(M)
            verts.append((px, y)); codes.append(L)
            verts.append((px, py)); codes.append(L)
        px, py = verts[-1]
        verts.append((px, py)); codes.append(M)

        p = PathPatch(Path(verts, codes), fill=False,
                      linewidth=width, edgecolor=color)
        self.add_patch(p)
        self.figure.canvas.draw_idle()

    def highlight_selected_nodes(self):
        get = self.n2c.get
        coords = filter(None, [ get(n) for n in self.selected_nodes ])
        x = [ c.x for c in coords ]
        y = [ c.y for c in coords ]
        if x and y:
            self.decorations.selected_nodes = self.scatter(
                x, y, s=60, c="green"
                )
        self.figure.canvas.draw_idle()

    def select_nodes(self, nodes=None):
        self.selected_nodes = nodes
        if hasattr(self, "app"):
            self.app.on_nodes_selected(self)
        if self.decorations.selected_nodes:
            try:
                self.decorations.selected_nodes.remove()
            except:
                try: [ x.remove() for x in self.decorations.selected_nodes ]
                except: pass
        self.highlight_selected_nodes()

    def rectselect(self, e0, e1):
        xlim = self.get_xlim()
        ylim = self.get_ylim()
        s = set()
        x0, x1 = sorted((e0.xdata, e1.xdata))
        y0, y1 = sorted((e0.ydata, e1.ydata))
        for n, c in self.n2c.items():
            if (x0 < c.x < x1) and (y0 < c.y < y1):
                s.add(n)
        self.select_nodes(s)
        self.set_xlim(xlim)
        self.set_ylim(ylim)
        if s:
            print "Selected:"
            for n in s:
                print " ", n

    def picked(self, e):
        if hasattr(self, "app"):
            self.app.picked(e)

    def visible_nodes(self, labeled_only=False):
        transform = self.transData.inverted().transform
        bb = self.get_window_extent()
        bbx = bb.expanded(1.1,1.1)
        points = transform(bbx.get_points())
        y0, y1 = points[:,1]
        if labeled_only:
            def f(v): return (y0 < v[0] < y1) and (v[2] in self.node2label)
        else:
            def f(v): return (y0 < v[0] < y1)
        for y, x, n in filter(f, self.coords):
            yield (n, x, y)

    def zoom_cxy(self, x=0.1, y=0.1, cx=None, cy=None):
        """
        Zoom the x and y axes in by the specified proportion of the
        current view, with a fixed data point (cx, cy)
        """
        transform = self.transData.inverted().transform
        xlim = self.get_xlim(); xmid = sum(xlim)*0.5
        ylim = self.get_ylim(); ymid = sum(ylim)*0.5
        bb = self.get_window_extent()
        bbx = bb.expanded(1.0-x,1.0-y)
        points = transform(bbx.get_points())
        x0, x1 = points[:,0]; y0, y1 = points[:,1]
        deltax = xmid-x0; deltay = ymid-y0
        cx = cx or xmid; cy = cy or ymid
        xoff = (cx-xmid)*x
        self.set_xlim(xmid-deltax+xoff, xmid+deltax+xoff)
        yoff = (cy-ymid)*y
        self.set_ylim(ymid-deltay+yoff, ymid+deltay+yoff)

    def zoom(self, x=0.1, y=0.1, cx=None, cy=None):
        """
        Zoom the x and y axes in by the specified proportion of the
        current view.
        """
        # get the function to convert display coordinates to data
        # coordinates
        transform = self.transData.inverted().transform
        xlim = self.get_xlim()
        ylim = self.get_ylim()
        bb = self.get_window_extent()
        bbx = bb.expanded(1.0-x,1.0-y)
        points = transform(bbx.get_points())
        x0, x1 = points[:,0]; y0, y1 = points[:,1]
        deltax = x0 - xlim[0]; deltay = y0 - ylim[0]
        self.set_xlim(xlim[0]+deltax, xlim[1]-deltax)
        self.set_ylim(ylim[0]+deltay, ylim[1]-deltay)

    def center_y(self, y):
        ymin, ymax = self.get_ylim()
        yoff = (ymax - ymin) * 0.5
        self.set_ylim(y-yoff, y+yoff)

    def center_x(self, x, offset=0.3):
        xmin, xmax = self.get_xlim()
        xspan = xmax - xmin
        xoff = xspan*0.5 + xspan*offset
        self.set_xlim(x-xoff, x+xoff)

    def center_node(self, node):
        c = self.n2c[node]
        y = c.y
        self.center_y(y)
        x = c.x
        self.center_x(x, 0.2)

    def highlight_support(self):
        """
        TODO: reconfigure this, insert into self.decorators
        """
        if self.support:
            lim = float(self.support)

        M = Path.MOVETO; L = Path.LINETO

        segments = []
        def f(n):
            if n.isleaf or not n.parent: return False
            try: return float(n.label) >= lim
            except:
                try: return float(n.support) >= lim
                except: pass
            return False

        for node, coords in [ x for x in self.n2c.items() if f(x[0]) ]:
            x = coords.x; y = coords.y
            p = node.parent
            pcoords = self.n2c[p]
            px = pcoords.x; py = pcoords.y
            ## segments.append([(x, y),(px, y)])

            self.add_artist(pyplot.Line2D(
                [x,px], [y,y], lw=3, solid_capstyle="butt", color="black"
                ))
                
    def hl(self, s):
        nodes = self.root.findall(s)
        if nodes:
            self.highlight(nodes)

    def highlight(self, nodes=None, width=5, color="red"):
        if self.highlightpatch:
            try:
                self.highlightpatch.remove()
            except:
                pass
        if not nodes:
            return

        if len(nodes)>1:
            mrca = self.root.mrca(nodes)
            if not mrca:
                return
        else:
            mrca = list(nodes)[0]

        M = Path.MOVETO; L = Path.LINETO
        verts = []
        codes = []
        seen = set()
        for node, coords in [ x for x in self.n2c.items() if x[0] in nodes ]:
            x = coords.x; y = coords.y
            p = node.parent
            while p:
                pcoords = self.n2c[p]
                px = pcoords.x; py = pcoords.y
                if node not in seen:
                    verts.append((x, y)); codes.append(M)
                    verts.append((px, y)); codes.append(L)
                    verts.append((px, py)); codes.append(L)
                    seen.add(node)
                if p == mrca or node == mrca:
                    break
                node = p
                coords = self.n2c[node]
                x = coords.x; y = coords.y
                p = node.parent
        px, py = verts[-1]
        verts.append((px, py)); codes.append(M)

        self.highlightpath = Path(verts, codes)
        self.highlightpatch = PathPatch(
            self.highlightpath, fill=False, linewidth=width, edgecolor=color
            )
        return self.add_patch(self.highlightpatch)

    def find(self, s):
        nodes = list(self.root.find(s))
        if nodes:
            self.zoom_nodes(nodes)

    def zoom_nodes(self, nodes, border=1.2):
        y0, y1 = self.get_ylim(); x0, x1 = self.get_xlim()
        y0 = max(0, y0); y1 = min(1, y1)

        n2c = self.n2c
        v = [ n2c[n] for n in nodes ]
        ymin = min([ c.y for c in v ])
        ymax = max([ c.y for c in v ])
        xmin = min([ c.x for c in v ])
        xmax = max([ c.x for c in v ])
        bb = Bbox(((xmin,ymin), (xmax, ymax)))

        # convert data coordinates to display coordinates
        transform = self.transData.transform
        disp_bb = [Bbox(transform(bb))]
        for n in nodes:
            if n.isleaf:
                txt = self.node2label[n]
                if txt.get_visible():
                    disp_bb.append(txt.get_window_extent())

        disp_bb = Bbox.union(disp_bb).expanded(border, border)

        # convert back to data coordinates
        points = self.transData.inverted().transform(disp_bb)
        x0, x1 = points[:,0]
        y0, y1 = points[:,1]
        self.set_xlim(x0, x1)
        self.set_ylim(y0, y1)

    def zoom_clade(self, anc, border=1.2):
        if anc.isleaf:
            self.center_node(anc)

        else:
            self.zoom_nodes(list(anc), border)

    def draw_leaf_labels(self, *args):
        leaves = list(filter(lambda x:x[0].isleaf,
                             self.visible_nodes(labeled_only=True)))
        psep = self.leaf_pixelsep()
        fontsize = min(self.leaf_fontsize, max(psep, 8))
        n2l = self.node2label
        transform = self.transData.transform
        sub = operator.sub

        for n in leaves:
            n2l[n[0]].set_visible(False)

        # draw leaves
        leaves_drawn = []
        for n, x, y in leaves:
            txt = self.node2label[n]
            if not leaves_drawn:
                txt.set_visible(True)
                leaves_drawn.append(txt)
                self.figure.canvas.draw_idle()
                continue

            txt2 = leaves_drawn[-1]
            y0 = y; y1 = txt2.xy[1]
            sep = sub(*transform(([0,y0],[0,y1]))[:,1])
            if sep > fontsize:
                txt.set_visible(True)
                txt.set_size(fontsize)
                leaves_drawn.append(txt)
                self.figure.canvas.draw_idle()

        if leaves_drawn:
            leaves_drawn[0].set_size(fontsize)

        return fontsize

    def draw_labels(self, *args):
        fs = max(10, self.draw_leaf_labels())
        nodes = self.visible_nodes(labeled_only=True)
        branches = list(filter(lambda x:(not x[0].isleaf), nodes))
        n2l = self.node2label
        for n, x, y in branches:
            t = n2l[n]
            t.set_visible(True)
            t.set_size(fs)

    def unclutter(self, *args):
        nodes = self.visible_nodes(labeled_only=True)
        branches = list(filter(lambda x:(not x[0].isleaf), nodes))
        psep = self.leaf_pixelsep()
        n2l = self.node2label
        fontsize = min(self.leaf_fontsize*1.2, max(psep, self.leaf_fontsize))

        drawn = []
        for n, x, y in branches:
            txt = n2l[n]
            try:
                bb = txt.get_window_extent().expanded(2, 2)
                vis = True
                for n2 in reversed(drawn):
                    txt2 = n2l[n2]
                    if bb.overlaps(txt2.get_window_extent()):
                        txt.set_visible(False)
                        vis = False
                        self.figure.canvas.draw_idle()
                        break
                if vis:
                    txt.set_visible(True)
                    txt.set_size(fontsize)
                    self.figure.canvas.draw_idle()
                    drawn.append(n)
            except RuntimeError:
                pass
                ## txt.set_visible(True)
                ## txt.set_size(fontsize)
                ## drawn.append(n)
                ## self.figure.canvas.draw_idle()

    def leaf_pixelsep(self):
        y0, y1 = self.get_ylim()
        y0 = max(0, y0); y1 = min(1, y1)
        display_points = self.transData.transform(((0, y0), (0, y1)))
        # height in pixels (visible y data extent)
        height = operator.sub(*reversed(display_points[:,1]))
        pixelsep = height/((y1-y0)/self.leaf_hsep)
        return pixelsep

    def draw_labels_old(self, *args):
        if self.nleaves:
            y0, y1 = self.get_ylim()
            y0 = max(0, y0); y1 = min(1, y1)

            display_points = self.transData.transform(((0, y0), (0, y1)))
            # height in pixels (visible y data extent)
            height = operator.sub(*reversed(display_points[:,1]))
            pixelsep = height/((y1-y0)/self.leaf_hsep)
            fontsize = min(max(pixelsep-2, 8), 12)

            if pixelsep >= 8:
                for node, txt in self.node2label.items():
                    if node.isleaf:
                        if self.leaflabels:
                            c = self.n2c[node]
                            x = c.x; y = c.y
                            if (y0 < y < y1):
                                txt.set_size(fontsize)
                                txt.set_visible(True)
                    else:
                        if self.branchlabels:
                            c = self.n2c[node]
                            x = c.x; y = c.y
                            if (y0 < y < y1):
                                txt.set_size(fontsize)
                                txt.set_visible(True)
            elif pixelsep >= 4:
                for node, txt in self.node2label.items():
                    if node.isleaf:
                        txt.set_visible(False)
                    else:
                        if self.branchlabels:
                            c = self.n2c[node]
                            x = c.x; y = c.y
                            if (y0 < y < y1):
                                txt.set_size(fontsize)
                                txt.set_visible(True)
            else:
                for node, txt in self.node2label.items():
                    txt.set_visible(False)
            self.figure.canvas.draw_idle()

    def redraw(self, home=False):
        xlim = self.get_xlim()
        ylim = self.get_ylim()
        self.cla()
        self.plot_tree(self.root)
        self.callbacks.connect("ylim_changed", self.draw_labels)

        for k, v in self.decorators.items():
            func, args, kwargs = v
            func(self, *args, **kwargs)

        if home:
            self.home()
        else:
            self.set_xlim(*xlim)
            self.set_ylim(*ylim)

    def set_name(self, name, frameon=True):
        self.name = name
        if name:
            at = AnchoredText(
                self.name, loc=2, frameon=frameon,
                prop=dict(size=12)
                )
            self.add_artist(at)
            return at

    def plot_tree(self, root, **kwargs):
        pyplot.ioff()
        self.root = root
        self.leaves = root.leaves()
        self.nleaves = len(self.leaves)
        self.leaf_hsep = 1.0/float(self.nleaves)
        if "branchlabels" in kwargs:
            self.branchlabels = kwargs["branchlabels"]
        if "leaflabels" in kwargs:
            self.leaflabels = kwargs["leaflabels"]

        for n in root.descendants():
            if n.length is None:
                self.scaled=False; break

        n2c = layout.cartesian(root, scaled=self.scaled)
        self.n2c = n2c
        sv = sorted([
            [c.y, c.x, n] for n, c in n2c.items()
            ])
        self.coords = sv#numpy.array(sv)

        self.yaxis.set_visible(False)

        M = Path.MOVETO; L = Path.LINETO; S = Path.STOP
        verts = []
        codes = []
        self.node2label = {}
        for node, coords in n2c.items():
            x = coords.x; y = coords.y
            if node.parent:
                pcoords = n2c[node.parent]
                px = pcoords.x; py = pcoords.y
                verts.append((x, y)); codes.append(M)
                verts.append((px, y)); codes.append(L)
                verts.append((px, py)); codes.append(L)

            if node.isleaf and node.label and self.leaflabels:
                txt = self.annotate(
                    node.label,
                    xy=(x, y),
                    xytext=(self.leaf_offset, 0),
                    textcoords="offset points",
                    verticalalignment=self.leaf_valign,
                    horizontalalignment=self.leaf_halign,
                    fontsize=self.leaf_fontsize,
                    clip_on=True,
                    picker=True
                )
                txt.set_visible(False)
                self.node2label[node] = txt

            if (not node.isleaf) and node.label and self.branchlabels:
                txt = self.annotate(
                    node.label,
                    xy=(x, y),
                    xytext=(self.branch_offset,0),
                    textcoords="offset points",
                    verticalalignment=self.branch_valign,
                    horizontalalignment=self.branch_halign,
                    fontsize=self.branch_fontsize,
                    bbox=dict(fc="lightyellow", ec="none", alpha=0.8),
                    clip_on=True,
                    picker=True
                )
                ## txt.set_visible(False)
                self.node2label[node] = txt

        px, py = verts[-1]
        verts.append((px, py)); codes.append(M)
        verts.append((px, py)); codes.append(S)

        self.branchpath = Path(verts, codes)
        self.branchpatch = PathPatch(self.branchpath, fill=False)
        self.add_patch(self.branchpatch)
        self.highlight_support()
        self.mark_named()
        self.home()
        self.set_name(self.name)
        pyplot.ion()
        return self

    def mark_named(self):
        if self._mark_named:
            n2c = self.n2c
            cv = [ c for n, c in n2c.items() if n.label and (not n.isleaf) ]
            x = [ c.x for c in cv ]
            y = [ c.y for c in cv ]
            if x and y:
                self.scatter(x, y, s=5, color='black')

    def home(self):
        transform = self.transData.inverted().transform
        if self.node2label:
            try:
                v = [ x.get_window_extent() for x in self.node2label.values() ]
                xmax = transform((max([ x.xmax for x in v ]),0))[0]
            except RuntimeError:
                xmax = 0
            #xmin = transform((min([ x.xmin for x in v ]),0))[0]
            xmin = 0
        else:
            xmax = 0; xmin = 0
        
        v = self.n2c.values()
        ymin = min([ c.y for c in v ])
        ymax = max([ c.y for c in v ])
        xmin = min(xmin, min([ c.x for c in v ]))
        xmax = max(xmax, max([ c.x for c in v ]))
        xspan = xmax - xmin; xpad = xspan*0.05
        yspan = ymax - ymin; ypad = yspan*0.05
        self.set_xlim(xmin-xpad, xmax+xpad)
        self.set_ylim(ymin-ypad, ymax+ypad)

    def scroll(self, x, y):
        x0, x1 = self.get_xlim()
        y0, y1 = self.get_ylim()
        xd = (x1-x0)*x
        yd = (y1-y0)*y
        self.set_xlim(x0+xd, x1+xd)
        self.set_ylim(y0+yd, y1+yd)

    def plot_labelcolor(self, nodemap, state2color=None):
        if state2color is None:
            import ivy
            colors = ivy.colors.tango()
            states = sorted(set(nodemap.values()))
            state2color = dict(zip(states, colors))

        for node, txt in self.node2label.items():
            s = nodemap.get(node)
            if s is not None:
                c = state2color[s]
                if c:
                    txt.set_color(c)
        self.figure.canvas.draw_idle()

    def plot_discrete(self, data, cmap=None, name=None,
                      xoff=10, yoff=0, size=15, legend=1):
        root = self.root
        if cmap is None:
            import ivy
            colors = ivy.colors.tango()
            states = sorted(set(data.values()))
            cmap = dict(zip(states, colors))
        n2c = self.n2c
        points = []; c = []
        d = dict([ (n, data.get(n)) for n in root if data.get(n) is not None ])
        for n, v in d.items():
            coord = n2c[n]
            points.append((coord.x, coord.y)); c.append(cmap[v])

        boxes = shapes.squares(self, points, c, size, xoff=xoff, yoff=yoff)

        if legend:
            handles = []; labels = []
            for v, c in sorted(cmap.items()):
                handles.append(Rectangle((0,0),0.5,1,fc=c))
                labels.append(str(v))
            self.legend(handles, labels, loc=legend)

        self.figure.canvas.draw_idle()
        return boxes
        
    def plot_continuous(self, data, mid=None, name=None, cmap=None,
                        size=15, colorbar=None):
        area = (size*0.5)*(size*0.5)*numpy.pi
        values = data.values()
        vmin = min(values); vmax = max(values)
        if mid is None:
            mid = (vmin+vmax)*0.5
            delta = vmax-vmin*0.5
        else:
            delta = max(abs(vmax-mid), abs(vmin-mid))
        norm = mpl_colors.Normalize(mid-delta, mid+delta)
        if cmap is None: cmap = mpl_colormap.binary
        n2c = self.n2c
        X = numpy.array(
            [ (n2c[n].x, n2c[n].y, v) for n, v in data.items() if n in n2c ]
            )
        circles = self.scatter(
            X[:,0], X[:,1], s=area, c=X[:,2], cmap=cmap, norm=norm,
            zorder=1000
            )
        if colorbar:
            cbar = self.figure.colorbar(circles, ax=self, shrink=0.7)
            if name:
                cbar.ax.set_xlabel(name)

        self.figure.canvas.draw_idle()

class OverviewTree(Tree):
    def __init__(self, *args, **kwargs):
        kwargs["leaflabels"] = False
        kwargs["branchlabels"] = False
        Tree.__init__(self, *args, **kwargs)
        self.add_overview_rect()
        
    def set_target(self, target):
        self.target = target

    def add_overview_rect(self):
        rect = UpdatingRect([0, 0], 0, 0, facecolor='black', edgecolor='red')
        rect.set_alpha(0.2)
        rect.target = self.target
        rect.set_bounds(*self.target.viewLim.bounds)
        self.zoomrect = rect
        self.add_patch(rect)
        self.target.callbacks.connect('xlim_changed', rect)
        self.target.callbacks.connect('ylim_changed', rect)

    def redraw(self):
        Tree.redraw(self)
        self.add_overview_rect()
        self.figure.canvas.draw_idle()

TreePlot = subplot_class_factory(Tree)
OverviewTreePlot = subplot_class_factory(OverviewTree)

def axes_enter(e):
    ax = e.inaxes
    ax._active = True

def axes_leave(e):
    ax = e.inaxes
    ax._active = False

def onselect(estart, estop):
    b = estart.button
    ## print b, estart.key

def onkeypress(e):
    ax = e.inaxes
    k = e.key
    if ax and k == 't':
        ax.home()
    if ax and k == "down":
        ax.scroll(0, -0.1)
        ax.figure.canvas.draw_idle()
    if ax and k == "up":
        ax.scroll(0, 0.1)
        ax.figure.canvas.draw_idle()
    if ax and k and k in '=+':
        ax.zoom(0.1,0.1)
    if ax and k == '-':
        ax.zoom(-0.1,-0.1)

def ondrag(e):
    ax = e.inaxes
    button = e.button
    if button == 2:
        if not ax.pan_start:
            ax.pan_start = (e.xdata, e.ydata)
            return
        x, y = ax.pan_start
        xdelta = x - e.xdata
        ydelta = y - e.ydata
        x0, x1 = ax.get_xlim()
        xspan = x1-x0
        y0, y1 = ax.get_ylim()
        yspan = y1 - y0
        midx = (x1+x0)*0.5
        midy = (y1+y0)*0.5
        ax.set_xlim(midx+xdelta-xspan*0.5, midx+xdelta+xspan*0.5)
        ax.set_ylim(midy+ydelta-yspan*0.5, midy+ydelta+yspan*0.5)

def onbuttonrelease(e):
    ax = e.inaxes
    button = e.button
    if button == 2:
        ## print "pan end"
        ax.pan_start = None

def onpick(e):
    ax = e.mouseevent.inaxes
    if ax:
        ax.picked(e)

def onscroll(e):
    ax = e.inaxes
    if ax:
        b = e.button
        ## print b
        k = e.key
        if k == None and b =="up":
            ax.zoom(0.1,0.1)
        if k == None and b =="down":
            ax.zoom(-0.1,-0.1)
        if k == "shift" and b == "up":
            ax.zoom_cxy(0.1, 0, e.xdata, e.ydata)
        if k == "shift" and b == "down":
            ax.zoom_cxy(-0.1, 0, e.xdata, e.ydata)
        if k == "control" and b == "up":
            ax.zoom_cxy(0, 0.1, e.xdata, e.ydata)
        if k == "control" and b == "down":
            ax.zoom_cxy(0, -0.1, e.xdata, e.ydata)
        if k == "d" and b == "up":
            ax.scroll(0, 0.1)
        if (k == "d" and b == "down"):
            ax.scroll(0, -0.1)
        if k == "e" and b == "up":
            ax.scroll(-0.1, 0)
        if k == "e" and b == "down":
            ax.scroll(0.1, 0)

def onclick(e):
    ax = e.inaxes
    if ax and e.button==1 and hasattr(ax, "zoomrect") and ax.zoomrect:
        # overview clicked; reposition zoomrect
        r = ax.zoomrect
        x = e.xdata
        y = e.ydata
        arr = ax.transData.inverted().transform(r.get_extents())
        xoff = (arr[1][0]-arr[0][0])*0.5
        yoff = (arr[1][1]-arr[0][1])*0.5
        r.target.set_xlim(x-xoff,x+xoff)
        r.target.set_ylim(y-yoff,y+yoff)
        r(r.target)

    if ax and e.button==2:
        ## print "pan start", (e.xdata, e.ydata)
        ax.pan_start = (e.xdata, e.ydata)


def test_decorate(treeplot):
    import evolve
    data = evolve.brownian(treeplot.root)
    values = data.values()
    vmin = min(values); vmax = max(values)
    norm = mpl_colors.Normalize(vmin, vmax)
    cmap = mpl_colormap.binary
    n2c = treeplot.n2c
    X = numpy.array(
        [ (n2c[n].x, n2c[n].y, v)
          for n, v in data.items() if n in n2c ]
        )
    circles = treeplot.scatter(
        X[:,0], X[:,1], s=200, c=X[:,2], cmap=cmap, norm=norm,
        zorder=100
        )


class SnapCursor:
    """
    Not used yet (under development).
    
    TODO: Implement a hover-mode cursor that snaps to the nearest node.
    """
    def __init__(self, ax):
        self.ax = ax
        self.bisect = bisect.bisect
        self.draw_idle = self.ax.figure.canvas.draw_idle
        self.marker = ax.nodemarker

    def dist(self, x, y, xmin, xmax, ymin, ymax):
        sqrt = math.sqrt
        transform = self.ax.transData.transform
        for node, c in self.ax.n2c.items():
            a, b = transform((c.x, c.y))
            xdelta = a-x; ydelta = b-y
            yield (sqrt(xdelta*xdelta + ydelta*ydelta), c.x, c.y, node)

    def mouse_move(self, event):
        if not event.inaxes: return
        ax = event.inaxes
        if ((ax != self.ax) or 
            (ax.figure.canvas.toolbar and ax.figure.canvas.toolbar.mode) or
            (not ax.snap)):
            return

        x, y = ax.transData.transform((event.xdata, event.ydata))
        xmin, xmax = ax.transData.transform(ax.get_xlim())
        ymin, ymax = ax.transData.transform(ax.get_ylim())
        d, px, py, node = min(self.dist(x, y, xmin, xmax, ymin, ymax))
        ## self.marker.set_visible(True)
        ## self.marker.set_data((px,py))
        if node.parent:
            c = ax.n2c[node.parent]
            self.marker.set_data([(px,c.x),(py,py)])

        ## txt = self.ax.node2label.get(node)
        ## if txt and txt.get_visible():
        ##     print node.label, txt.set_color("red")

        self.draw_idle()

class Decorator(object):
    def __init__(self, treeplot):
        self.plot = treeplot
        
class VisToggle(object):
    def __init__(self, name, treeplot=None, value=False):
        self.name = name
        self.plot = treeplot
        self.value = value

    def __nonzero__(self):
        return self.value

    def __repr__(self):
        return "%s: %s" % (self.name, self.value)

    def redraw(self):
        if self.plot:
            self.plot.redraw()

    def toggle(self):
        self.value = not self.value
        self.redraw()

    def show(self):
        if self.value == False:
            self.value = True
            self.redraw()

    def hide(self):
        if self.value == True:
            self.value = False
            self.redraw()


if __name__ == "__main__":
    import evolve
    root, data = evolve.test_brownian()
    plot_continuous(root, data, name="Brownian", mid=0.0)
