# -*- coding: utf-8 -*-
"""
Extract document codes from the MLGB 'medieval catalogue' field.
Look up entries with those document codes in the index based on the 'List of Identifications'.
Set the MLGB book ID for those entries. 
This will then allow us to provide links from the index entry to the corresponding MLGB record.

By Sushila Burgess
"""
##=============================================================================

import sys
import connectToMLGB as c
import importIndexedCopies as i

##=============================================================================


def setBookIDs(): #{
  the_database_connection = None
  the_cursor = None

  #=================================================================
  # Read each line of the original file, manipulate it as necessary,
  # and then write it into the new file.
  #=================================================================
  try:
    # Connect to the database and create a cursor
    the_database_connection = c.get_database_connection()
    the_cursor = the_database_connection.cursor() 

    # Get details of the medieval catalogues in which an MLGB book appeared.
    select = "select id, medieval_catalogue from books_book where medieval_catalogue > ''"
    select += " order by id"
    the_cursor.execute( select )
    results = the_cursor.fetchall()

    # Clear out old data
    the_cursor.execute( "TRUNCATE TABLE index_mlgb_links" )

    # Insert the new data
    for row in results: #{

      book_id = row[ 0 ]
      medieval_catalogue = row[ 1 ].strip()

      print "\n\n%s" % medieval_catalogue

      # Avoid confusion potentially caused by spaces in wrong place etc.
      medieval_catalogue = medieval_catalogue.replace( '. ', '.' )
      medieval_catalogue = medieval_catalogue.replace( '?', '' )
      medieval_catalogue = medieval_catalogue.replace( '=', ' ' )

      words = medieval_catalogue.split()
      for word in words: #{
        catalogue_entries = []

        if not i.is_copy_code( word ): continue

        word = word.strip()
        if word.endswith( ',' ): word = word[ 0 : -1 ] # take off any commas from the end

        document_code = i.get_document_code( word )
        seqno_in_document = i.get_seqno_in_document( word )

        if document_code.isalnum() and seqno_in_document.isdigit() \
        and int( seqno_in_document ) > 0: #{

          catalogue_entries.append( seqno_in_document )

        else: # some kind of incomplete or garbled entry - don't try to save it
          continue
        #}

        if i.is_numeric_range( word ): #{ # need to generate sequence numbers for rest of range
          rest_of_range = i.get_rest_of_numeric_range( word )

          for int_seqno in rest_of_range: #{
            seqno_in_document = str( int_seqno )
            catalogue_entries.append( seqno_in_document )
          #}
        #}

        for seqno_in_document in catalogue_entries: #{
          print  "%d: '%s' %s" % (book_id, document_code, seqno_in_document)

          insert_statement = 'insert into index_mlgb_links '
          insert_statement += '( mlgb_book_id, document_code, seqno_in_document ) values '
          insert_statement += "( %d, '%s', %s )" % (book_id, document_code, seqno_in_document)
          the_cursor.execute( insert_statement )
        #}
      #}
    #}

    the_cursor.close()
    the_database_connection.close()

  except:
    if the_cursor: the_cursor.close()
    if the_database_connection: the_database_connection.close()
    raise
#}

##=============================================================================

if __name__ == '__main__':

  setBookIDs()

##=============================================================================

