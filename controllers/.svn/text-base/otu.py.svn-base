# coding: utf-8
from uuid import uuid4
from gluon.storage import Storage

response.subtitle = "OTUs"

def index():
    t = db.study

    class Virtual(object):
        @virtualsettings(label='OTUs')
        def otu_url(self):
            study = t[self.study.id]
            n = db(db.otu.study==study.id).count()
            if n > 0:
                u = URL(c="otu",f="study",args=[study.id])
                return A("%s OTUs" % n, _href=u)
            else:
                return "%s OTUs" % n

        @virtualsettings(label='Study')
        def study_url(self):
            study = t[self.study.id]
            u = URL(c="study",f="view",args=[study.id])
            s = study.citation
            if len(s)>65: s = s[:60]+" ..."
            return A(s, _href=u, _title=study.citation)

    powerTable = plugins.powerTable
    powerTable.datasource = t
    powerTable.dtfeatures["sScrollY"] = "100%"
    powerTable.dtfeatures["sScrollX"] = "100%"
    powerTable.virtualfields = Virtual()
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
    powerTable.columns = ["study.id",
                          "study.focal_clade",
                          "virtual.study_url",
                          "study.year_published",
                          "virtual.otu_url",
                          "study.uploaded"]
    #powerTable.hiddencolumns = ["study.treebase_id"]
    ## details = dict(detailscallback=URL(c="study",f="details"))
    ## powerTable.extra = dict(autoresize=True,
    ##                         tooltip={},
    ##                         details=details)
    powerTable.extra = {}
   
    return dict(table=powerTable.create())    

def study():
    t = db.otu
    study = db.study(request.args(0)) or redirect(URL("index"))

    class Virtual(object):
        @virtualsettings(label='Taxon')
        def taxon(self):
            ## taxon = db.taxon(t[self.otu.id].taxon) or Storage()
            if auth.has_membership(role="contributor"):
                return taxon_link(self.otu.id)
            else:
                rec = db.taxon(self.otu.taxon) or Storage()
                return SPAN(rec.name)
            
    powerTable = plugins.powerTable
    powerTable.datasource = db(t.study==study).select()
    powerTable.virtualfields = Virtual()
    powerTable.dtfeatures["sScrollY"] = "100%"
    powerTable.dtfeatures["sScrollX"] = "100%"
    powerTable.virtualfields = Virtual()
    powerTable.headers = "labels"
    powerTable.showkeycolumn = False
    powerTable.dtfeatures["bJQueryUI"] = request.vars.get("jqueryui",True)
    ## powerTable.uitheme = request.vars.get("theme","cupertino")
    powerTable.uitheme = request.vars.get("theme","smoothness")
    powerTable.dtfeatures["iDisplayLength"] = 25
    powerTable.dtfeatures["aaSorting"] = [[1,'asc']]
    powerTable.dtfeatures["sPaginationType"] = request.vars.get(
        "pager","full_numbers"
        ) # two_button scrolling
    powerTable.columns = ["otu.id",
                          "otu.label",
                          "virtual.taxon"]
    ## powerTable.hiddencolumns = ["stree.type"]

    ## details = dict(detailscallback=URL(c="stree",f="details"))
    ## powerTable.extra = dict(autoresize=True,
    ##                         tooltip={},
    ##                         details=details)
    study_url = A(_study_rep(study),
                  _href=URL(c="study",f="view",args=[study.id]))
    N = db(db.otu.study==study.id).count()
    return dict(study_url=study_url, N=N, table=powerTable.create())

def taxon_link(otu):
    otu = db.otu(int(otu))
    taxon = db.taxon(otu.taxon) or Storage()
    ## d = request.vars
    ## if d.otu != otu: d.otu = otu
    ## if d.taxon != taxon.id: d.taxon = taxon.id
    ## d = dict(otu=otu, taxon=taxon.id)
    u = URL(c="otu",f="taxon_edit.load",args=[otu.id])
    uid = uuid4().hex
    return SPAN(A(str(taxon.name), _href=u, cid=uid), _id=uid)

def taxon_edit():
    otu = db.otu(int(request.args(0)))
    field = Field("taxon", "integer", default=otu.taxon)
    field.widget = SQLFORM.widgets.autocomplete(
        request, db.taxon.name, id_field=db.taxon.id
        )
    form = SQLFORM.factory(field, formstyle="divs")
    if form.accepts(request.vars, session):
        taxon = form.vars.taxon
        if taxon != otu.taxon:
            response.flash="record updated"
            otu.update_record(taxon=taxon)
        return dict(form=None, cancel=None, a=taxon_link(otu.id))

    cancel = A("Cancel",
               _href=URL(c="otu",f="taxon_edit_cancel.load",args=[otu.id]),
               cid=request.cid)
    return dict(form=form, cancel=cancel, a=None)

def taxon_edit_cancel():
    return taxon_link(request.args(0))
