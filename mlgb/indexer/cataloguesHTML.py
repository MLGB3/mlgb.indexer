#-*- coding: utf-8 -*-
"""
Create a preliminary version of output from Richard Sharpe's list.master.
Sorted by medieval catalogue provenance and date.
By Sushila Burgess
"""
##=============================================================================

import sys
import os
import math
import MySQLdb

import connectToMLGB as c
from importIndexEntries import biblio_block_start_html, biblio_block_end_html
import writeHTML as w

final_output_dir = w.final_output_dir
work_dir = w.work_dir
output_filename = ''

mlgb_book_url = w.mlgb_book_url
if_editable = w.if_editable

##=============================================================================

tab = '\t'
newline = '\n'
carriage_return = '\r'
space = ' '

linebreak = '<br>'
right_arrow = '&rarr;'

##=============================================================================

medieval_catalogues_url = "/authortitle/medieval_catalogues"
medieval_catalogues_by_date_url = medieval_catalogues_url + '/bydate'
authortitle_url = "/authortitle/browse"

inline_lists = [ 'K', 'R' ] # for Henry de Kirkestede and Registrum Anglie, the decode is
                            # the same in every one of hundreds of documents, so no need to
                            # put each list item on a separate line.


##=============================================================================

def writeAllHTMLFiles(): #{


  writeOneHTMLFile( 'listbydate' )

  writeOneHTMLFile( 'list' )

  the_database_connection = c.get_database_connection()
  the_cursor = the_database_connection.cursor() 

  statement = "select coalesce( doc_group_type_parent, doc_group_type ) as doc_group_type, "
  statement += " doc_group_id, doc_group_name, document_code "
  statement += " from index_medieval_documents_view where document_code > '' "
  statement += " order by doc_group_type, doc_group_name, document_code_sort, document_code" 
  the_cursor.execute( statement )
  documents = the_cursor.fetchall()

  prev_type_code = ''
  prev_loc_name = ''
 
  for document in documents: #{
    type_code     = document[ 0 ]
    loc_id        = document[ 1 ]
    loc_name      = document[ 2 ]
    document_code = document[ 3 ]

    if type_code != prev_type_code: #{
      prev_type_code = type_code
      prev_loc_name = ''
      
      print ""
      print 'Producing LIST for document group type %s' % type_code
      writeOneHTMLFile( 'list', type_code )
    #}

    if loc_name != prev_loc_name: #{
      prev_loc_name = loc_name
      
      print ""
      print 'Producing LIST for document group %s' % loc_name
      writeOneHTMLFile( 'list', type_code, loc_id, loc_name )
    #}

    print 'Producing output for ONE document code: %s' % document_code
    writeOneHTMLFile( document_code )
  #}

  the_cursor.close()
  the_database_connection.close()
  print 'Finished producing output.'
#}

##=============================================================================

def writeOneHTMLFile( document_code = 'list', type_code = '', loc_id = 0, loc_name = '' ): #{

  global output_filename

  try:
    filename_without_path = 'catalogue' + document_code 
    if type_code: filename_without_path += type_code
    if loc_id: filename_without_path += '-' + str( loc_id )
    filename_without_path += '.html'

    output_filename = work_dir + filename_without_path

    outfile_handle = file
    outfile_handle = open( output_filename, 'wb' ) # 'wb' allows entry of UTF-8

    if document_code == 'list':
      writeDocumentList( outfile_handle, type_code, loc_id, loc_name )
    elif document_code == 'listbydate':
      writeDocumentListByDate( outfile_handle )
    else:
      writeDocumentContents( outfile_handle, document_code )

    outfile_handle.close()
    os.rename( output_filename, final_output_dir + filename_without_path )

  except:
    if isinstance( outfile_handle, file ):
      if not outfile_handle.closed : outfile_handle.close()
    raise
#}

##=============================================================================

def writeDocumentList( handle, selected_type_code='', selected_loc_id=0, selected_loc_name=''): #{

  # Connect to the database and create a cursor
  the_database_connection = c.get_database_connection()
  the_cursor = the_database_connection.cursor() 

  # Work out what to show in your breadcrumbs trail etc.
  display_all = False
  selected_type_name = ''

  if not selected_type_code and not selected_loc_id: #{
    display_all = True
  #}
  elif selected_type_code: #{
    statement = "select doc_group_type_name from index_medieval_doc_group_types" \
              + " where doc_group_type_code = '%s'" % selected_type_code
    the_cursor.execute( statement )
    type_row = the_cursor.fetchone()
    selected_type_name = type_row[ 0 ]
  #}

  write_inherit_and_title_block( handle )

  # Override the default treeview behaviour, which starts off expanded.
  # With such long files as the ones generated here, it might be best to start off collapsed.
  if display_all:
    set_treeview_collapsed( handle )

  write_start_main_content( handle )

  handle.write( '<h2>List of medieval catalogues</h2>' )
  handle.write( newline )

  write_breadcrumbs( handle, selected_type_code, selected_type_name, \
                     selected_loc_id, selected_loc_name )

  handle.write( newline + newline )

  if display_all: #{ # add navigation links to individual institution types
    statement = "select distinct coalesce( doc_group_type_parent, doc_group_type_code ) " \
              + " as doc_group_type, doc_group_type_name from index_medieval_doc_group_types " \
              + " order by doc_group_type"
    the_cursor.execute( statement )
    institution_types = the_cursor.fetchall()
    i = 0
    handle.write( '<p>' + newline )
    for ins_type in institution_types: #{
      if i > 0: handle.write( ' | ' )
      i += 1

      type_code = ins_type[ 0 ]
      type_name = ins_type[ 1 ]

      handle.write( '<a href="%s%s/source/%s" ' % (w.if_editable, medieval_catalogues_url, type_code) )
      handle.write( ' title="%s" >' % type_name )
      handle.write( type_name )
      handle.write( '</a> ' )

    #}
    handle.write( '</p>' + newline )
  #}

  if display_all: #{
    handle.write( '<h3 class="inline_heading">Overview by provenance</h3>' )
    handle.write( '{% if not printing %}' )
    handle.write( ' | <a href="%s">Overview by date</a>' % medieval_catalogues_by_date_url )
    handle.write( '{% endif %}' )
    handle.write( newline + newline )
    handle.write( '{% if not printing %}' )
    handle.write( '<div id="sidetreecontrol">' + newline )
    handle.write( '<a href="?#">Collapse All</a> | <a href="?#">Expand All</a>' + newline )
    handle.write( '</div>' + newline )
    handle.write( '{% endif %}' )
  #}

  statement = "select coalesce( doc_group_type_parent, doc_group_type ) as doc_group_type, " \
            + " doc_group_type_name, doc_group_id, doc_group_name, document_code, document_name " \
            + " from index_medieval_documents_view "
  if selected_type_code: #{
    statement += " where document_code > '' "
    statement += " and coalesce( doc_group_type_parent, doc_group_type ) = '%s' " % selected_type_code
  #}
  if selected_loc_id:
    statement += " and doc_group_id = %d " % selected_loc_id
  statement += " order by doc_group_type, doc_group_name, document_code_sort, document_code" 
  the_cursor.execute( statement )
  documents = the_cursor.fetchall()

  prev_type_code = ''
  prev_loc_name = ''
  inline_display = False

  if display_all:
    handle.write( '<ul class="treeview AAA" id="tree">' + newline )
  else: # use a different CSS class and ID so that links behave normally
    handle.write( '<ul class="AAA" id="catalogue_tree">' + newline )

  for document in documents: #{ 

    type_code     = document[ 0 ] # doc_group_type      e.g. BX for Benedictines
    type_name     = document[ 1 ] # doc_group_type_name e.g. Benedictines 
    loc_id        = document[ 2 ] # doc_group_name      e.g. numeric ID for Canterbury
    loc_name      = document[ 3 ] # doc_group_name      e.g. Canterbury
    document_code = document[ 4 ] # document_code       e.g. BC21
    document_name = document[ 5 ] # document_name       e.g. 'Books read in the refectory 1473'

    type_name     = w.reformat( type_name )
    loc_name      = w.reformat( loc_name )
    document_name = w.reformat( document_name )

    inline_display = False
    if type_code in inline_lists: inline_display = True

    if type_code != prev_type_code: #{
      if prev_type_code: #{
        handle.write( '</ul><!-- end CCC list -->' + newline )
        handle.write( '</li><!-- end BBB list item -->' + newline )
        handle.write( '</ul><!-- end BBB list -->' + newline )
        handle.write( '</li><!-- end AAA list item -->' + newline )
      #}

      prev_type_code = type_code
      prev_loc_name = loc_name

      write_outerhead( handle, type_name, display_all )

      if inline_display: heading = document_name # show the sole decode for K and R
      else: heading = loc_name 

      write_innerhead( handle, heading, display_all )

      if display_all:
        handle.write( '<ul style="display: {% if printing %}block{% else %}none{% endif %}"' )
        handle.write( '><!-- start CCC list -->' + newline )
      else:
        handle.write( '<ul><!-- start CCC list -->' + newline )
    #}

    elif loc_name != prev_loc_name: #{
      prev_loc_name = loc_name

      handle.write( '</ul><!-- end CCC list -->' + newline )
      handle.write( '</li><!-- end BBB list item -->' + newline )
      handle.write( '</ul><!-- end BBB list -->' + newline )
      handle.write( newline )

      if inline_display: heading = document_name # show the sole decode for K and R
      else: heading = loc_name 

      write_innerhead( handle, heading, display_all ) # start BBB list

      if display_all:
        handle.write( '<ul style="display: {% if printing %}block{% else %}none{% endif %}"' )
        handle.write( '><!-- start CCC list -->' + newline )
      else:
        handle.write( '<ul><!-- start CCC list -->' + newline )
    #}

    if document_code: #{
      statement = "select count(*) from index_entry_copies where document_code = '%s'" % document_code
      the_cursor.execute( statement )
      count_row = the_cursor.fetchone()
      num_catalogue_entries = count_row[ 0 ]
    #}
    else:
      num_catalogue_entries = 0

    print output_filename, type_name, loc_name, document_code

    handle.write( '<li' );
    if inline_display: handle.write( ' style="display: inline-block; width: 80px;" ' )
    handle.write( '><!-- start CCC list item -->' + newline );

    if num_catalogue_entries > 0: #{
      handle.write( '<a href="%s%s/%s" ' \
                    % (w.if_editable, medieval_catalogues_url, document_code) )
      handle.write( ' title="View details of catalogue %s">' % document_code )
    #}

    if inline_display: # no need to keep repeating the same decode hundreds of times for K and R
      handle.write( '&bull; %s (%d)'  % (document_code, num_catalogue_entries))
    else:
      handle.write( '%s %s (%d)'  % (document_code, document_name, num_catalogue_entries))

    if num_catalogue_entries > 0: handle.write( '</a>' + newline )

    handle.write( newline + '</li><!-- end CCC list item -->' + newline );

  #}

  handle.write( '</ul><!-- end CCC list -->' + newline )
  handle.write( '</li><!-- end BBB list item -->' + newline )
  handle.write( '</ul><!-- end BBB list -->' + newline )
  handle.write( newline + '</li><!-- end AAA outerhead list item -->' )
  handle.write( '</ul><!-- end tree AAA -->' + newline )

  handle.write( newline + linebreak + newline )

  if selected_loc_name: write_documents_total( handle, len( documents ) )

  write_end_main_content( handle )

  # Close your cursor and your connection
  the_cursor.close()
  the_database_connection.close()

#} # end writeDocumentList()

##=============================================================================

def writeDocumentListByDate( handle ): #{

  # Connect to the database and create a cursor
  the_database_connection = c.get_database_connection()
  the_cursor = the_database_connection.cursor() 

  write_inherit_and_title_block( handle )

  write_start_main_content( handle )

  handle.write( '<h2>List of medieval catalogues</h2>' )
  handle.write( newline )

  handle.write( '<div class="index">' )
  handle.write( newline + newline )

  # Write navigation by century
  centuries = [ '10', '11', '12', '13', '14', '15', '16', '17', 'undated' ]
  century_nav = ''
  for century in centuries: #{
    century_desc = get_century_desc( century )
    anchor_name = get_century_anchor( century )

    if century_nav != '': century_nav += ' | '
    century_nav += '<a href="#%s">%s</a>' % (anchor_name, century_desc )
  #}


  handle.write( '<h3 class="inline_heading">Overview by date</h3>' )
  handle.write( '{% if printing %}<br />{%else%}' )
  handle.write( ' | <a href="%s">Overview by provenance</a>' % medieval_catalogues_url )
  handle.write( '{% endif %}' )
  handle.write( newline + newline )

  statement  = "select document_code, document_name, "
  statement += " coalesce( start_date, '2000-01-01') as sort_start_date, "
  statement += " coalesce( end_date, '2000-01-01') as sort_end_date, "
  statement += " doc_group_type_name, doc_group_name "
  statement += " from index_medieval_documents_view where document_code > '' "
  statement += " order by sort_start_date, sort_end_date, document_code_sort"
  the_cursor.execute( statement )
  documents = the_cursor.fetchall()

  prev_type_code = ''
  prev_start_year = ''
  prev_century = 0
  century_desc = ''
  total_for_century = 0

  handle.write( '<div id="catalogues_by_date">' + newline )

  for document in documents: #{ 
    document_code = document[ 0 ] #document_code e.g. BC21
    document_name = document[ 1 ] #document_name e.g. 'Books read in the refectory 1473'
    start_date = document[ 2 ]
    end_date   = document[ 3 ]
    library_type = document[ 4 ] # e.g. Benedictines
    library_loc  = document[ 5 ] # e.g. Abbey of St Frideswide

    document_name = w.reformat( document_name )
    library_type  = w.reformat( library_type )
    library_loc   = w.reformat( library_loc )

    type_code = document_code[ 0 : 1 ] # this wouldn't work with 2-letter types e.g. BA
                                       # but we are only really interested in K and R
    start_year = start_date[ 0 : 4 ]
    if start_year.startswith( '0' ): start_year = start_year[ 1 : ]
    century = int( math.floor( int( start_year ) / 100 ) + 1 )

    print century, start_year, document_code, document_name

    if century != prev_century: #{
      if prev_century > 0: #{ 
        handle.write( '</td></tr></table>' + newline )
        write_total_for_century( handle, century_desc, total_for_century )
      #}

      century_desc = get_century_desc( century )
      anchor_name = get_century_anchor( century )
      handle.write( '<p><a name="%s"></a></p>' % anchor_name )
      write_century_nav( handle, century_nav )

      prev_century = century
      total_for_century = 0
      prev_type_code = ''

      handle.write( '<h4>%s</h4>' % century_desc )
      handle.write( newline )
      handle.write( '<table class="century" id="century%dtab">' % century )
      handle.write( newline )
    #}

    total_for_century += 1

    statement = "select count(*) from index_entry_copies where document_code = '%s'" \
              % document_code
    the_cursor.execute( statement )
    count_row = the_cursor.fetchone()
    num_catalogue_entries = count_row[ 0 ]

    # no need to keep repeating the same decode hundreds of times for K and R
    if type_code in inline_lists and type_code == prev_type_code: #{
      handle.write( ' &bull; ' )
      if num_catalogue_entries > 0: write_link_to_document( handle, document_code )
      handle.write( '%s (%d) '  % (document_code, num_catalogue_entries))
      if num_catalogue_entries > 0: handle.write( '</a>' + newline )
    #}

    else: #{  # not in middle of K or R, so write out a complete row for each entry
      if total_for_century > 1: handle.write( '</td></tr>' + newline )

      handle.write( '<tr><td>' + newline )
      if start_year in document_name: 
        handle.write( '<em>' + start_year + '</em>' + newline )

      handle.write( '</td><td>' + newline )
      handle.write( '%s' % library_type )
      if library_loc != library_type:
        handle.write( ': %s' % library_loc )

      handle.write( '</td><td>' + newline )
      if num_catalogue_entries > 0: write_link_to_document( handle, document_code )
      handle.write('%s. %s (%d)' % (document_code, document_name, num_catalogue_entries))
      if num_catalogue_entries > 0: handle.write( '</a>' + newline )

      # the final <td> gets finished off when you get to the next entry
    #}

    prev_type_code = type_code


    handle.write( newline );

  #}
  handle.write( '</td></tr></table>' + newline )

  write_total_for_century( handle, century_desc, total_for_century )

  handle.write( '</div><!-- end list of catalogues by date -->' + newline )
  write_century_nav( handle, century_nav )
  handle.write( '</div><!-- end div class "index" -->' )
  handle.write( newline + newline )

  write_end_main_content( handle )

  # Close your cursor and your connection
  the_cursor.close()
  the_database_connection.close()

#} # end writeDocumentListByDate()

##=============================================================================

def get_century_desc( century ): #{

  century = str( century )
  if century.isdigit(): #{
    if int( century ) >= 20: #{ # undated documents are sorted to the end
      century_desc = 'Undated'
    #}
    else: #{
      century_desc = '%sth century' % century
    #}
  #}
  elif century.lower() == 'undated': #{
    century_desc = 'Undated'
  #}
  return century_desc
#}
##=============================================================================

def get_century_anchor( century ): #{

  century = str( century )
  if century.isdigit(): #{
    if int( century ) >= 20: #{ # undated documents are sorted to the end
      anchor_name = 'undated_anchor'
    #}
    else: #{
      anchor_name = 'century%s_anchor' % century
    #}
  #}
  elif century.lower() == 'undated': #{
    anchor_name = 'undated_anchor'
  #}
  return anchor_name
#}
##=============================================================================

def write_century_nav( handle, century_nav ): #{

  handle.write( '{% if not printing %}' )
  handle.write( '<div class="navigate_catalogues">' )
  handle.write( '<p>%s</p></div>' % century_nav )
  handle.write( '{% endif %}' )
  handle.write( newline ) 

#}
##=============================================================================

def write_total_for_century( handle, century_desc, total_for_century ): #{

  handle.write( newline )
  handle.write( '<p><em>Number of %s catalogues found: %d</em></p>' \
                % (century_desc.lower(), total_for_century) )
  handle.write( newline )
#}
##=============================================================================

def write_link_to_document( handle, document_code ): #{

  handle.write( '<a href="%s%s/%s" ' \
                % (w.if_editable, medieval_catalogues_url, document_code) )
  handle.write( ' title="View details of catalogue %s">' % document_code )
  handle.write( newline )
#}
##=============================================================================

def writeDocumentContents( handle, document_code ): #{

  write_inherit_and_title_block( handle )

  write_start_main_content( handle )

  # Connect to the database and create a cursor
  the_database_connection = c.get_database_connection()
  the_cursor = the_database_connection.cursor() 

  statement = "select coalesce( doc_group_type_parent, doc_group_type ) as doc_group_type, " 
  statement += " doc_group_type_name, doc_group_id, doc_group_name, document_name "
  statement += " from index_medieval_documents_view where document_code = '%s'" % document_code

  the_cursor.execute( statement )
  document = the_cursor.fetchone()

  type_code     = document[ 0 ]
  type_name     = w.reformat( document[ 1 ] )
  loc_id        = document[ 2 ]
  loc_name      = w.reformat( document[ 3 ] )
  document_name = w.reformat( document[ 4 ] )

  statement = "select entry_id, entry_book_count, copy_count, copy_code, copy_notes, seqno_in_document"
  statement += " from index_entry_copies where document_code = '%s'" % document_code
  statement += " order by seqno_in_document, copy_code"
  the_cursor.execute( statement )
  copy_results = the_cursor.fetchall()

  write_breadcrumbs( handle, type_code, type_name, loc_id, loc_name, document_name )

  if type_name == loc_name: # don't have 'HENRY DE KIRKESTEDE: HENRY DE KIRKESTEDE'
    handle.write( '<h2>%s</h2>' % type_name )
  else:
    handle.write( '<h2>%s: %s</h2>' % (type_name, loc_name) )
  handle.write( '<h3 class="medieval_catalogue_desc">%s. %s</h3>' % (document_code, document_name)  )

  handle.write( newline )
  write_catalogue_entries_total( handle, len( copy_results ) )
  handle.write( newline )

  handle.write( '<div class="index">' )
  handle.write( newline + newline )

  prev_copy_code = ''
  authors = []  # record which authors have already been displayed on this page
                # and don't repeat the bibliography paragraph on 2nd or subsequent appearances


  handle.write( '<ul id="catalogue_entry_list">' + newline )

  for copy_row in copy_results: #{ 

    # Extract copy information
    entry_id         = copy_row[ 0 ]
    entry_book_count = copy_row[ 1 ]
    copy_count       = copy_row[ 2 ]
    copy_code  = w.reformat( copy_row[ 3 ] )
    copy_notes = w.reformat( copy_row[ 4 ] )
    seqno_in_document = copy_row[ 5 ]

    if copy_code and copy_code == prev_copy_code: continue # don't repeat e.g. BC1.5--7
    prev_copy_code = copy_code

    # Extract book information
    statement="select role_in_book, title_of_book, book_biblio_line, xref_title_of_book, problem"
    statement += " from index_entry_books where entry_id = %d" % entry_id
    statement += " and entry_book_count = %d" % entry_book_count
    the_cursor.execute( statement )
    book = the_cursor.fetchone()

    role_in_book       = w.reformat( book[ 0 ] )
    title_of_book      = w.reformat( book[ 1 ] )
    book_biblio_line   = w.reformat( book[ 2 ] )
    xref_title_of_book = w.reformat( book[ 3 ] )
    problem            = w.reformat( book[ 4 ] )

    # Extract author information
    statement="select entry_name, xref_name, entry_biblio_line, entry_biblio_block, letter"
    statement += " from index_entries where entry_id = %d" % entry_id
    the_cursor.execute( statement )
    author = the_cursor.fetchone()

    # Get links to the main MLGB database
    mlgb_links = get_mlgb_links( the_cursor, document_code, seqno_in_document )

    entry_name         = w.reformat( author[ 0 ] )
    xref_name          = w.reformat( author[ 1 ] )
    entry_biblio_line  = w.reformat( author[ 2 ] )
    entry_biblio_block = w.reformat( author[ 3 ] )

    letter = author[ 4 ].replace( '/', '' )
   

    # Write out the details
    handle.write( '<li>' + newline )

    if mlgb_links: #{
      mlgb_book_id = mlgb_links[0][0]
      hover_title_of_book = w.strip_html_for_hover( title_of_book )
      handle.write( w.get_mlgb_book_link( mlgb_book_id, hover_title_of_book ))
    #}
    handle.write( copy_code )
    if mlgb_links: handle.write( '</a>' )

    copy_notes = copy_notes.strip()
    if copy_notes: #{
      if not copy_notes.startswith( ',' ) and not copy_notes.startswith( ': ' ):
        copy_notes = ' ' + copy_notes
      handle.write( copy_notes )
    #}

    handle.write( ': ' + newline )

    # Write out details from 'entry' table
    # linking to the main entry in the author/title index.

    link_to_authortitle = authortitle_url + '/' + letter + '/'
    anchor = '#entry%d_anchor' % entry_id
    link_to_authortitle += anchor

    handle.write( '<a href="%s%s">' % (w.if_editable, link_to_authortitle) )
    handle.write( entry_name + '</a>' + newline )
    if xref_name: handle.write( ' ' + right_arrow + ' ' + xref_name + newline )
    if entry_biblio_line: handle.write( entry_biblio_line + newline )
    handle.write( linebreak + newline )

    if entry_biblio_block: #{
      if entry_name not in authors: #{
        handle.write( entry_biblio_block + linebreak + newline )
        authors.append( entry_name )
      #}
    #}

    # Write out details from 'book' table
    if problem: handle.write( problem + newline )
    if role_in_book: handle.write( role_in_book + newline )
    if title_of_book: handle.write( '<strong>' + title_of_book + '</strong>' + newline )
    if xref_title_of_book: handle.write( ' ' + right_arrow + ' ' + xref_title_of_book + newline )
    if book_biblio_line: handle.write( book_biblio_line + newline )

    handle.write( '</li>' + newline + newline )
  #}

  handle.write( '</ul><!-- end catalogue_entry_list -->' + newline )

  handle.write( '</div><!-- end div class "index" -->' )
  handle.write( newline )

  handle.write( '<p>' + newline )
  write_catalogue_entries_total( handle, len( copy_results ) )
  handle.write( '</p>' + newline )

  write_end_main_content( handle )

  # Close your cursor and your connection
  the_cursor.close()
  the_database_connection.close()

#} # end writeDocumentContents()
##=============================================================================

def set_treeview_collapsed( handle ): #{

  # Override the default treeview behaviour, which starts off expanded.
  # With such long files as the ones generated here, it might be best to start off collapsed.
  # (But if printing the output, you will want it expanded.)
  handle.write( '{% block treeview %}' )
  handle.write( '<script type="text/javascript">' )
  handle.write( '    $(function() {' )
  handle.write( '        $("#tree").treeview({' )
  handle.write( '            collapsed: {% if printing %}false{% else %}true{% endif %},' )
  handle.write( '            animated: "medium",' )
  handle.write( '            control:"#sidetreecontrol",' )
  handle.write( '            prerendered: {% if printing %}true{% else %}false{% endif %},' )
  handle.write( '            persist: "location"' )
  handle.write( '        });' )
  handle.write( '    })' )
  handle.write( '</script>' )
  handle.write( '{% endblock %}' )

#}
##=============================================================================

def write_inherit_and_title_block( handle ): #{

  handle.write( '{% extends "base.html" %}'               + newline )

  handle.write( '{% block title %}'                       + newline )
  handle.write( '<title>MLGB3 List of Medieval Catalogues</title>' + newline )
  handle.write( '{% endblock %}'                          + newline )
#}
##=============================================================================

def write_start_main_content( handle ): #{

  handle.write( newline + '{% block maincontent %}' + newline )
  handle.write( '<div class="index">' + newline )
#}
##=============================================================================

def write_end_main_content( handle, include_link_to_definitions = True ): #{

  handle.write( newline )

  w.write_link_to_source_file( handle, include_link_to_definitions )

  handle.write( '</div><!-- end div class "index" -->' + newline )

  handle.write( newline + w.indexmenu + newline)

  handle.write( newline + '{% if printing %}<script>window.print();</script>{% endif %}' + newline )

  handle.write( '{% endblock %}' + newline )

  handle.write( '{% block search %}' + newline )
  handle.write( '{% endblock %}' + newline )

  handle.write( '{% block useful_links %}' + newline ) 
  handle.write( '{% endblock %}' + newline )

#}
##=============================================================================

def write_breadcrumbs( handle, type_code = '', type_name = '', loc_id = 0, loc_name = '', \
                       document_name = '' ): #{

  # e.g. Medieval catalogues > Benedictines > Anglesey > List of books, 1314

  # no need for 'navigate back' links if on the first page anyway
  if not type_code and not type_name and not loc_name and not document_name: return

  separator = '&gt;'

  handle.write( '{% if not printing %}<p>' )

  handle.write( '<a href="%s%s"' % (w.if_editable, medieval_catalogues_url) )
  handle.write( ' title="Back to list of medieval catalogues">' ) 
  if type_code:
    handle.write( 'Medieval catalogues</a> ' )

  # Link back to type of institution e.g. 'BENEDICTINES', 'SECULAR INSTITUTIONS: Towns and Hospitals'
  if type_code and type_name and loc_name: #{
    handle.write( ' %s <a href="%s%s/source/%s"' \
                  % (separator, w.if_editable, medieval_catalogues_url, type_code) )
    handle.write( ' title="%s">' % type_name ) 
    handle.write( '%s</a> ' %  type_name )
  #}
  elif type_name: #{
    handle.write( ' %s %s' % (separator, type_name) )
  #}

  # Link back to location of institution, e.g. 'Canterbury'
  if type_code and loc_name and loc_id and document_name: #{
    if type_name != loc_name: #{
      handle.write( ' %s <a href="%s%s/source/%s/%d"' \
                    % (separator, w.if_editable, medieval_catalogues_url, type_code, loc_id) )
      handle.write( ' title="%s">' % loc_name ) 
      handle.write( '%s</a> ' % loc_name )
    #}
  #}
  elif loc_name: #{
    handle.write( ' %s %s' % (separator, loc_name) )
  #}

  if document_name: #{
    handle.write( ' %s %s' % (separator, document_name) )
  #}

  handle.write( '</p>{% endif %}' )

#}
##=============================================================================

def write_catalogue_entries_total( handle, entry_count ): #{

  if entry_count == 1:
    handle.write( '<em>1 identified entry found.</em>' )
  else:
    handle.write( '<em>%d identified entries found.</em>' % entry_count )
#}
##=============================================================================

def write_documents_total( handle, document_count ): #{

  if document_count == 1:
    handle.write( '<em>1 catalogue found.</em>' )
  else:
    handle.write( '<em>%d catalogues found.</em>' % document_count )
#}
##=============================================================================

def write_outerhead( handle, heading, expandable ): #{

  handle.write( newline + newline )
  if expandable: #{
    handle.write( '<li class="expandable outerhead AAA">' + newline )
    handle.write( '<div class="hitarea expandable-hitarea"></div>' + newline )
    handle.write( '<span class="outerhead AAA" title="expand/collapse this section">' )
  #}
  else:
    handle.write( '<li class="outerhead AAA"><span class="outerhead AAA">' + newline )
  handle.write( '%s</span>' % heading )
  handle.write( newline + newline )
#}
##=============================================================================

def write_innerhead( handle, heading, expandable ): #{

  if expandable: #{
    handle.write( '<ul style="display: {% if printing %}block{% else %}none{% endif %}">' )
    handle.write( '<!-- start BBB list -->' + newline )
    handle.write( '<li class="expandable innerhead BBB">' + newline )
    handle.write( '<div class="hitarea expandable-hitarea"></div>' + newline )
    handle.write( '<span class="innerhead heading2 BBB" title="expand/collapse this section">' )
  #}
  else: #{
    handle.write( '<ul><!-- start BBB list -->' + newline )
    handle.write( '<li class="innerhead BBB"><span class="innerhead BBB">' + newline )
  #}
  handle.write( heading )
  handle.write( '</span>' )
  handle.write( newline + newline )

#}
##=============================================================================

def get_mlgb_links( the_cursor, document_code, seqno_in_document ): #{

  # See if we have got any links to the actual MLGB database
  mlgb_links = []
  if seqno_in_document == None: seqno_in_document = '0'
  seqno_in_document = str( seqno_in_document )

  statement  = "select mlgb_book_id from index_mlgb_links "
  statement += " where document_code = '%s' and seqno_in_document = %s " \
            % (document_code, seqno_in_document)
  statement += " and seqno_in_document > 0 order by mlgb_book_id" 
  the_cursor.execute( statement )
  mlgb_links = the_cursor.fetchall()

  return mlgb_links
#}
##=============================================================================

if __name__ == '__main__':


  # These two lines are hacks (copied from Mat's clever hack, thanks Mat). 
  # They switch the default encoding to utf8 so that the command line will convert UTF8 + Ascii to UTF8
  reload(sys)
  sys.setdefaultencoding("utf8")

  writeAllHTMLFiles()

##=============================================================================

