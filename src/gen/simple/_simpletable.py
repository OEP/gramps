#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2008  Donald N. Allingham
# Copyright (C) 2009  Douglas S. Blank
# Copyright (C) 2011       Tim G L Lyons
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# $Id$
#

"""
Provide a simplified table creation interface
"""

import cgi
from gen.ggettext import sgettext as _
import gen.lib
import config
import gen.datehandler

class SimpleTable(object):
    """
    Provide a simplified table creation interface.
    """

    def __init__(self, access, title=None):
        """
        Initialize the class with a simpledb
        """
        self.access = access
        self.title = title
        self._columns = []
        self._cell_markup = {} # [col][row] = "<b>data</b>"
        self._cell_type = {} # [col] = "text"
        self._rows = []
        self._raw_data = []
        self._link = []
        self._sort_col = None
        self._sort_reverse = False
        self._link_col = None
        self._callback_leftclick = None
        self._callback_leftdouble = None
        self.model_index_of_column = {}

    def get_row_count(self):
        return len(self._rows)

    def get_row(self, index):
        return self._rows[index]

    def get_raw_data(self, index):
        return self._raw_data[index]

    def columns(self, *cols):
        """
        Set the columns
        """
        self._columns = [unicode(col) for col in cols]
        self._sort_vals = [[] for i in range(len(self._columns))]

    def row_sort_val(self, col, val):
        """
        Add a row of data to sort by.
        """
        self._sort_vals[col].append(val) 

    def set_link_col(self, col):
        """
        Manually sets the column that defines link.
        col is either a number (column) or a (object_type_name, handle).
        """
        self._link_col = col

    def row(self, *data):
        """
        Add a row of data.
        """
        retval = [] 
        link   = None
        row = len(self._rows)
        self._raw_data.append([])
        for col in range(len(data)):
            item = data[col]
            self._raw_data[-1].append(item)
            # FIXME: add better text representations of these objects
            if item is None:
                retval.append("")
            elif isinstance(item, basestring):
                if item == "checkbox": 
                    retval.append("")
                    self.set_cell_type(col, "checkbox")
                else:
                    retval.append(item)
            elif isinstance(item, (int, float, long)):
                retval.append(item)
                self.row_sort_val(col, item)
            elif isinstance(item, gen.lib.Person):
                retval.append(self.access.describe(item))
                if (self._link_col == col or link is None):
                    link = ('Person', item.handle)
            elif isinstance(item, gen.lib.Family): 
                retval.append(self.access.describe(item))
                if (self._link_col == col or link is None):
                    link = ('Family', item.handle)
            elif isinstance(item, gen.lib.Citation): 
                retval.append(self.access.describe(item))
                if (self._link_col == col or link is None):
                    link = ('Citation', item.handle)
            elif isinstance(item, gen.lib.Source): 
                retval.append(self.access.describe(item))
                if (self._link_col == col or link is None):
                    link = ('Source', item.handle)
            elif isinstance(item, gen.lib.Event):
                retval.append(self.access.describe(item))
                if (self._link_col == col or link is None):
                    link = ('Event', item.handle)
            elif isinstance(item, gen.lib.MediaObject):
                retval.append(self.access.describe(item))
                if (self._link_col == col or link is None):
                    link = ('Media', item.handle)
            elif isinstance(item, gen.lib.Place):
                retval.append(self.access.describe(item))
                if (self._link_col == col or link is None):
                    link = ('Place', item.handle)
            elif isinstance(item, gen.lib.Repository):
                retval.append(self.access.describe(item))
                if (self._link_col == col or link is None):
                    link = ('Repository', item.handle)
            elif isinstance(item, gen.lib.Note):
                retval.append(self.access.describe(item))
                if (self._link_col == col or link is None):
                    link = ('Note', item.handle)
            elif isinstance(item, gen.lib.Date):
                text = gen.datehandler.displayer.display(item)
                retval.append(text)
                if item.get_valid():
                    if item.format:
                        self.set_cell_markup(col, row, 
                                             item.format % cgi.escape(text))
                    self.row_sort_val(col, item.sortval)
                else:
                    # sort before others:
                    self.row_sort_val(col, -1)
                    # give formatted version:
                    invalid_date_format = config.get('preferences.invalid-date-format')
                    self.set_cell_markup(col, row,
                                         invalid_date_format % cgi.escape(text))
                if (self._link_col == col or link is None):
                    link = ('Date', item)
            elif isinstance(item, gen.lib.Span):
                text = str(item)
                retval.append(text)
                self.row_sort_val(col, item)
            elif isinstance(item, list): # [text, "PersonList", handle, ...]
                retval.append(item[0])
                link = (item[1], item[2:])
            else:
                retval.append(str(item))
                if (self._link_col == col or link is None):
                    if hasattr(item, "get_url"):
                        link = ("url", item.get_url())
        self._link.append(link)
        self._rows.append(retval)

    def sort(self, column_name, reverse=False):
        self._sort_col = column_name
        self._sort_reverse = reverse

    def _sort(self):
        idx = self._columns.index(self._sort_col)
        # FIXME: move raw_data with this
        if self._sort_reverse:
            self._rows.sort(lambda a, b: -cmp(a[idx],b[idx]))
        else:
            self._rows.sort(lambda a, b: cmp(a[idx],b[idx]))

    def write(self, document):
        doc = document.doc
        columns = len(self._columns)
        doc.start_table('simple', 'Table')
        doc._tbl.set_column_widths([100/columns] * columns)
        doc._tbl.set_columns(columns)
        if self.title:
            doc.start_row()
            doc.start_cell('TableHead', span=columns) 
            doc.start_paragraph('TableTitle')
            doc.write_text(_(self.title))
            doc.end_paragraph()
            doc.end_cell()
            doc.end_row()
        if self._sort_col:
            self._sort()
        doc.start_row()
        for col in self._columns:
            doc.start_cell('TableHeaderCell', span=1) 
            doc.write_text(col, 'TableTitle')
            doc.end_cell()
        doc.end_row()
        index = 0
        for row in self._rows:
            doc.start_row()
            for col in row:
                doc.start_cell('TableDataCell', span=1) 
                obj_type, handle = None, None
                if isinstance(self._link_col, tuple):
                    obj_type, handle = self._link_col
                elif isinstance(self._link_col, list):
                    obj_type, handle = self._link_col[index]
                elif self._link[index]:
                    obj_type, handle = self._link[index]
                ######
                if obj_type:
                    if obj_type.lower() == "url":
                        doc.start_link(handle)
                    else:
                        doc.start_link("/%s/%s" % 
                                       (obj_type.lower(), handle))
                doc.write_text(col, 'Normal')
                if obj_type:
                    doc.stop_link()
                doc.end_cell()
            doc.end_row()
            index += 1
        doc.end_table()
        doc.start_paragraph("Normal")
        doc.end_paragraph()

    def get_cell_markup(self, x, y=None, data=None):
        """
        See if a column has formatting (if x and y are supplied) or
        see if a cell has formatting. If it does, return the formatted 
        string, otherwise return data that is escaped (if that column
        has formatting), or just the plain data.
        """
        if x in self._cell_markup:
            if y is None: 
                return True # markup for this column
            elif y in self._cell_markup[x]:
                return self._cell_markup[x][y]
            else:
                return cgi.escape(data)
        else:
            if y is None: 
                return False # no markup for this column
            else:
                return data

    def get_cell_type(self, col):
        """
        See if a column has a type, else return "text" as default.
        """
        if col in self._cell_type:
            return self._cell_type[col]
        return "text"

    def set_cell_markup(self, x, y, data):
        """
        Set the cell at position [x][y] to a formatted string.
        """
        col_dict = self._cell_markup.get(x, {})
        col_dict[y] = data
        self._cell_markup[x] = col_dict

    def set_cell_type(self, col, value):
        """
        Set the cell type at position [x].
        """
        self._cell_type[col] = value