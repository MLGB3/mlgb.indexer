# -*- coding: utf-8 -*-
##=============================================================================

import sys
import MySQLdb

import connectToMLGB as c

entry_fields = [
  'entry_id',
  'letter',
  'entry_name',
  'xref_name',
  'entry_biblio_line',
  'entry_biblio_block',
]

solr_entry_fields = {
  'entry_id'           : 'sql_entry_id',
  'letter'             : 'sql_letter',
  'entry_name'         : 's_entry_name',
  'xref_name'          : 's_entry_xref_name',
  'entry_biblio_line'  : 's_entry_biblio_line',
  'entry_biblio_block' : 's_entry_biblio_block',
}

book_fields = [
  'entry_book_count',
  'title_of_book',
  'xref_title_of_book',
  'book_biblio_line',
  'role_in_book',
  'problem',
]

solr_book_fields = {
  'entry_book_count'    : 'sql_entry_book_count',
  'title_of_book'       : 's_title_of_book',
  'xref_title_of_book'  : 's_xref_title_of_book',
  'book_biblio_line'    : 's_book_biblio_line',
  'role_in_book'        : 's_role_in_book',
  'problem'             : 's_problem',
}

copy_fields = [
  'copy_count',
  'copy_code',
  'copy_notes',
  'survives_yn',
  'printed_yn',
  'uncertain_yn',
  'duplicate_title_yn',
  'document_code',
  'document_code_sort',
  'seqno_in_document',
]


solr_copy_fields = {
  'copy_count'         : 'sql_copy_count',
  'copy_code'          : 's_copy_code',
  'copy_notes'         : 's_copy_notes',
  'survives_yn'        : 's_survives_yn',
  'printed_yn'         : 's_printed_yn',
  'uncertain_yn'       : 's_uncertain_yn',
  'duplicate_title_yn' : 's_duplicate_title_yn',
  'document_code'      : 's_document_code',
  'document_code_sort' : 's_document_code_sort',
  'seqno_in_document'  : 's_seqno_in_document',
}

document_lookup = {}

mlgb_links_lookup = {}

newline = '\n'

##=============================================================================

def writeXML(): #{

  global document_lookup

  the_database_connection = None
  the_cursor = None
  outfile_handle = file

  try:
    the_database_connection = c.get_database_connection()
    the_cursor = the_database_connection.cursor() 

    print 'Looking up document list...'
    statement = "select document_code, document_name, doc_group_type_name, doc_group_name, "
    statement += " start_date, end_date, document_type, doc_group_id, "
    statement += " coalesce( doc_group_type_parent, doc_group_type ) as doc_group_type, "
    statement += " start_year, end_year, date_in_words "
    statement += " from u_index_medieval_documents_view"
    the_cursor.execute( statement )
    results = the_cursor.fetchall()
    for row in results: #{
      document_code = row[ 0 ] 
      document_name = row[ 1 ] 
      library_type  = row[ 2 ] #doc_group_type_name  
      library_loc   = row[ 3 ] #doc_group_name  
      start_date    = row[ 4 ] 
      end_date      = row[ 5 ] 
      document_type = row[ 6 ] 

      library_loc_id    = row[ 7 ] #doc_group_id  
      library_type_code = row[ 8 ] #doc_group_type  

      start_year    = str( row[ 9 ] )
      end_year      = str( row[ 10 ] )
      date_in_words = row[ 11 ] 

      if start_year and len( start_year ) < 4: start_year = start_year.rjust( 4, '0' )
      if end_year and len( end_year ) < 4: end_year = end_year.rjust( 4, '0' )

      document_lookup[ document_code ] = { 's_document_name' : document_name ,
                                           's_library_type'  : library_type  ,
                                           's_library_loc'   : library_loc   ,
                                           'd_document_start': start_date    ,
                                           'd_document_end'  : end_date      ,
                                           's_document_type' : document_type ,
                                           's_library_loc_id': library_loc_id,
                                           's_library_type_code': library_type_code,
                                           's_document_start_year': start_year,
                                           's_document_end_year': end_year,
                                           's_document_date_in_words': date_in_words,
                                          }
    #}


    # Get links to MLGB book IDs. Don't miss any out if there is a range of numbers.
    print 'Looking up MLGB book links...'
    statement = "select distinct copy_code, mlgb_book_id "
    statement += " from index_mlgb_links l, u_index_entry_copies c "
    statement += " where c.document_code = l.document_code "
    statement += " and c.seqno_in_document = l.seqno_in_document "
    statement += " order by copy_code, mlgb_book_id" 
    the_cursor.execute( statement )
    link_results = the_cursor.fetchall()
    for link_row in link_results: #{
      copy_code = link_row[ 0 ]
      mlgb_book_id = link_row[ 1 ]
      print copy_code, mlgb_book_id
      if mlgb_links_lookup.has_key( copy_code ):
        mlgb_links_lookup[ copy_code ].append( mlgb_book_id )
      else:
        mlgb_links_lookup[ copy_code ] = [ mlgb_book_id ]
    #}


    
    output_filename = '/home/mlgb/sites/mlgb/parts/index/authortitle_to_solr.xml'
    print 'About to write %s' % output_filename
    outfile_handle = open( output_filename, 'wb' ) # 'wb' allows entry of UTF-8

    outfile_handle.write( '<doc>' + newline )

    the_cursor.execute( "select max( entry_id ) from index_entries" )
    results = the_cursor.fetchone()
    max_entry_id = results[ 0 ]
    solr_id = 0

    statement = get_entry_select_statement()
    the_cursor.execute( statement )
    entry_results = the_cursor.fetchall()
    current_entry_id = 0
    for entry in entry_results: #{

      current_entry_id = entry[ 0 ]
      print "Getting data for entry %d of %d"  % (current_entry_id, max_entry_id)

      entry_name = entry[ 2 ]

      book_results = []
      copy_results = []

      statement = get_book_select_statement( current_entry_id )

      the_cursor.execute( statement )
      book_results = the_cursor.fetchall()

      if not book_results: #{
        # This is presumably a cross-reference entry, but we cannot tell 
        # whether it is referring to an author or a book title - both are possible.
        solr_id += 1
        write_entry_fields( entry, solr_id, outfile_handle )
        write_entry_end( outfile_handle )
      #}
      else: #{
        # Work out whether the primary entry refers to an author or a book title.
        # If it refers to a book title, there will only be one (dummy) book record,
        # and the title of this dummy entry will be blank.

        author = ''
        title_of_book = ''

        if len( book_results ) == 1: #{
          book = book_results[ 0 ]
          title_of_book = book[ 1 ].strip()
          xref_title_of_book = book[ 2 ].strip()

          if title_of_book: # will be saved automatically as part of book fields
            title_of_book = ''
          else: #{
            if xref_title_of_book:
              title_of_book = xref_title_of_book
            else:
              title_of_book = entry_name
          #}
        #}

        if not title_of_book: author = entry_name

        for book in book_results: #{
          current_book_count = book[ 0 ]
          statement = get_copy_select_statement( current_entry_id, current_book_count )

          the_cursor.execute( statement )
          copy_results = the_cursor.fetchall()

          if not copy_results: #{
            solr_id += 1
            write_entry_fields( entry, solr_id, outfile_handle )
            write_author_or_title( author, title_of_book, outfile_handle )
            write_book_fields( book, outfile_handle )
            write_entry_end( outfile_handle )
          #}
          else: #{
            for copy in copy_results: #{
              solr_id += 1
              write_entry_fields( entry, solr_id, outfile_handle )
              write_author_or_title( author, title_of_book, outfile_handle )
              write_book_fields( book, outfile_handle )
              document_code = write_copy_fields( copy, outfile_handle )
              write_document_fields( document_code, outfile_handle )

              copy_code = copy[ 1 ].strip()
              write_mlgb_book_link_fields( copy_code, outfile_handle )

              write_entry_end( outfile_handle )
            #}
          #}
        #}
      #}
    #}

    outfile_handle.write( '</doc>' + newline )
    outfile_handle.close()
    the_cursor.close()
    the_database_connection.close()

  except:
    if not outfile_handle.closed: outfile_handle.close()
    if the_cursor: the_cursor.close()
    if the_database_connection: the_database_connection.close()
    raise
#}

##=============================================================================

def get_entry_select_statement( current_entry_id = None ): #{

  statement = "select " 
  statement += ", ".join( entry_fields ) 
  statement += " from u_index_entries"

  if current_entry_id: 
    statement += " where entry_id = %d" % current_entry_id

  statement += " order by entry_id"

  return statement
#}
##=============================================================================

def get_book_select_statement( current_entry_id ): #{

  statement = "select " 
  statement += ", ".join( book_fields ) 
  statement += " from u_index_entry_books where entry_id = %d" % current_entry_id
  statement += " order by entry_book_count" 
  return statement
#}
##=============================================================================

def get_copy_select_statement( current_entry_id, current_book_count ): #{

  statement = "select " 
  statement += ", ".join( copy_fields ) 
  statement += " from u_index_entry_copies where entry_id = %d" % current_entry_id
  statement += " and entry_book_count = %d" % current_book_count
  statement += " order by copy_count" 
  return statement
#}
##=============================================================================

def write_entry_fields( entry, solr_id, outfile_handle ): #{

  outfile_handle.write( '<entry id="%d">' % solr_id )

  solr_id_sort = str( solr_id )
  solr_id_sort = solr_id_sort.rjust( 7, '0' )
  outfile_handle.write( '<solr_id_sort>%s</solr_id_sort>' % solr_id_sort )

  outfile_handle.write( newline )

  i = -1
  for fieldname in entry_fields: #{
    i += 1
    value = get_valid_string( entry[ i ] )
    if len( value ) == 0: continue

    if solr_entry_fields.has_key( fieldname ):
      fieldname = solr_entry_fields[ fieldname ]

    outfile_handle.write( '<%s>%s</%s>' % (fieldname, value, fieldname) )
    outfile_handle.write( newline )
  #}
#}
##=============================================================================

def write_author_or_title( author, title, outfile_handle ): #{

  if author.strip(): #{
    author = get_valid_string( author )
    outfile_handle.write( '<s_author_name>%s</s_author_name>' % author )
    outfile_handle.write( newline )
  #}

  if title.strip(): #{
    title = get_valid_string( title )
    outfile_handle.write( '<s_title_of_book>%s</s_title_of_book>' % title )
    outfile_handle.write( newline )
  #}
#}
##=============================================================================

def write_book_fields( book, outfile_handle ): #{

  i = -1
  for fieldname in book_fields: #{
    i += 1
    value = get_valid_string( book[ i ] )
    if len( value ) == 0: continue

    if solr_book_fields.has_key( fieldname ):
      fieldname = solr_book_fields[ fieldname ]

    outfile_handle.write( '<%s>%s</%s>' % (fieldname, value, fieldname) )
    outfile_handle.write( newline )
  #}
#}
##=============================================================================

def write_copy_fields( copy, outfile_handle ): #{

  document_code = ''

  i = -1
  for fieldname in copy_fields: #{
    i += 1
    value = get_valid_string( copy[ i ] )
    if len( value ) == 0: continue

    if fieldname == 'document_code': document_code = value

    if solr_copy_fields.has_key( fieldname ):
      fieldname = solr_copy_fields[ fieldname ]

    outfile_handle.write( '<%s>%s</%s>' % (fieldname, value, fieldname) )
    outfile_handle.write( newline )

    if fieldname == 's_seqno_in_document': #{
      fieldname = 's_seqno_in_doc_sort'
      value = value.rjust( 6, '0' )
      outfile_handle.write( '<%s>%s</%s>' % (fieldname, value, fieldname) )
      outfile_handle.write( newline )
    #}
  #}

  return document_code
#}
##=============================================================================

def write_document_fields( document_code, outfile_handle ): #{

  if not document_code:
    return
  elif not document_lookup.has_key( document_code ):
    return
  else:
    one_document_lookup = document_lookup[ document_code ]

  i = -1
  for fieldname, value in one_document_lookup.items(): #{
    i += 1
    value = get_valid_string( value )
    if len( value.strip() ) == 0: continue

    if fieldname == 'd_document_start' or fieldname == 'd_document_end':
      outfile_handle.write( '<%s>%sT00:00:00.000Z</%s>' % (fieldname, value, fieldname) )
    else:
      outfile_handle.write( '<%s>%s</%s>' % (fieldname, value, fieldname) )
    outfile_handle.write( newline )
  #}
#}
##=============================================================================

def write_mlgb_book_link_fields( copy_code, outfile_handle ): #{

  if not copy_code:
    return
  elif not mlgb_links_lookup.has_key( copy_code ):
    return
  else:
    mlgb_book_ids = mlgb_links_lookup[ copy_code ]

  for mlgb_book_id in mlgb_book_ids: #{
    outfile_handle.write( '<s_mlgb_book_id>%d</s_mlgb_book_id>' % mlgb_book_id )
    outfile_handle.write( newline )
  #}
#}
##=============================================================================

def write_entry_end( outfile_handle ): #{

  outfile_handle.write( '</entry>' )
  outfile_handle.write( newline + newline )
#}
##=============================================================================

def get_valid_string( value ): #{

  if not isinstance( value, (str, unicode)): #{
    if value == None: 
      value = ""
    else: 
      value = str( value )
  #}
  value = change_for_xml( value )
  return value
#}
##=============================================================================

def change_for_xml( the_string ): #{

  the_string = the_string.replace( '&', '&amp;' )
  the_string = the_string.replace( '<', '&lt;' )
  the_string = the_string.replace( '>', '&gt;' )
  return the_string
#}
##=============================================================================

if __name__ == '__main__':


  # These two lines are hacks (copied from Mat's clever hack, thanks Mat). 
  # They switch the default encoding to utf8 so that the command line will convert UTF8 + Ascii to UTF8
  reload(sys)
  sys.setdefaultencoding("utf8")

  writeXML()

##=============================================================================

