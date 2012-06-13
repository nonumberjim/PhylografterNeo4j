from gluon.html import TABLE
from gluon.sqlhtml import table_field

class SQLTABLE2(TABLE):
    def __init__(
        self,
        sqlrows,
        linkto=None,
        upload=None,
        orderby=None,
        headers={},
        truncate=16,
        columns=None,
        th_link='',
        **attributes
        ):

        TABLE.__init__(self, **attributes)
        self.components = []
        self.attributes = attributes
        self.sqlrows = sqlrows
        (components, row) = (self.components, [])
        if not columns:
            columns = sqlrows.colnames
        ## if headers=='fieldname:capitalize':
        if not headers:
            headers = {}
            for c in columns:
                headers[c] = ' '.join(
                    [w.capitalize() for w in c.split('.')[-1].split('_')]
                    )

        for c in columns:
            if orderby:
                row.append(TH(A(headers.get(c, c),
                                _href=th_link+'?orderby=' + c)))
            else:
                row.append(TH(headers.get(c, c)))

        components.append(THEAD(TR(*row)))
        tbody = []
        for (rc, record) in enumerate(sqlrows):
            row = []
            if rc % 2 == 0:
                _class = 'even'
            else:
                _class = 'odd'
            for colname in columns:
                if not table_field.match(colname):
                    r = record._extra[colname]
                    row.append(TD(r))
                    continue
                (tablename, fieldname) = colname.split('.')
                field = sqlrows.db[tablename][fieldname]
                if tablename in record \
                        and isinstance(record,Row) \
                        and isinstance(record[tablename],Row):
                    r = record[tablename][fieldname]
                elif fieldname in record:
                    r = record[fieldname]
                else:
                    raise SyntaxError, 'something wrong in Rows object'
                r_old = r
                if field.represent:
                    r = field.represent(r)
                elif field.type == 'blob' and r:
                    r = 'DATA'
                elif field.type == 'upload':
                    if upload and r:
                        r = A('file', _href='%s/%s' % (upload, r))
                    elif r:
                        r = 'file'
                    else:
                        r = ''
                elif field.type in ['string','text']:
                    r = str(field.formatter(r))
                    ur = unicode(r, 'utf8')
                    if truncate!=None and len(ur) > truncate:
                        r = ur[:truncate - 3].encode('utf8') + '...'
                ## elif linkto and field.type == 'id':
                ##     try:
                ##         href = linkto(r, 'table', tablename)
                ##     except TypeError:
                ##         href = '%s/%s/%s' % (linkto, tablename, r_old)
                ##     r = A(r, _href=href)
                ## elif linkto and field.type.startswith('reference'):
                ##     ref = field.type[10:]
                ##     try:
                ##         href = linkto(r, 'reference', ref)
                ##     except TypeError:
                ##         href = '%s/%s/%s' % (linkto, ref, r_old)
                ##         if ref.find('.') >= 0:
                ##             tref,fref = ref.split('.')
                ##             if hasattr(sqlrows.db[tref],'_primarykey'):
                ##                 href = '%s/%s?%s' % (linkto, tref, urllib.urlencode({fref:ur}))
                ##     r = A(r, _href=href)
                ## elif linkto and hasattr(field._table,'_primarykey') and fieldname in field._table._primarykey:
                ##     # have to test this with multi-key tables
                ##     key = urllib.urlencode(dict( [ \
                ##                 ((tablename in record \
                ##                       and isinstance(record, Row) \
                ##                       and isinstance(record[tablename], Row)) and
                ##                  (k, record[tablename][k])) or (k, record[k]) \
                ##                     for k in field._table._primarykey ] ))
                ##     r = A(r, _href='%s/%s?%s' % (linkto, tablename, key))
                row.append(TD(r))
            tbody.append(TR(_class=_class, _style="cursor:pointer;",
                            _onclick="load_record(%s);" % record.id, *row))
        components.append(TBODY(*tbody))
