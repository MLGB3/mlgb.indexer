# -*- coding: utf-8 -*-
"""
Text fields where the user can enter formatting can end up getting massive quantities
of XML/HTML comments pasted in. This later interferes with searching, e.g. a search for 'mirror'
brought up records containing the hidden formatting instruction 'MirrorIndent Off'.
So strip out any XML comments that have slipped in.

By Sushila Burgess
"""
##=============================================================================

import sys

import connectToMLGB as c

comment_start = '<!--'
comment_end = '-->'
percent = '%'

text_fields = {
  'books_book': [ 'evidence_notes', 'pressmark', 'ownership', 'notes' ],
  'books_contains': [ 'contains' ],
}

newline = '\n'

##=============================================================================

def stripComments(): #{

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

    # Look at all the text fields that could contain unwanted XML
    for table_name, field_names in text_fields.items(): #{
      #print newline + table_name + newline

      for field in field_names: #{
        #print newline + table_name + ': ' + field + newline

        select = "select id, %s from %s where %s like '%s%s%s%s%s'" \
               % (field, table_name, field, percent, comment_start, percent, comment_end, percent)
        select += " order by id"
        the_cursor.execute( select )
        results = the_cursor.fetchall()

        # Check each value for XML/HTML comments
        for row in results: #{
          row_id = row[ 0 ]
          text_value = row[ 1 ]

          print ''
          print ''
          print '======================================='
          print table_name, field, 'ID', row_id
          print '======================================='
          print ''

          print '==== RAW VALUE, ID %d ====' % row_id
          print text_value
          print '==== end RAW VALUE, ID %d ==== %s' % (row_id, newline)

          comment_start_count = text_value.count( comment_start )
          comment_end_count = text_value.count( comment_end )

          if comment_start_count != comment_end_count: #{
            print 'Mismatched start/end tags:', comment_start_count, 'starts', comment_end_count, 'ends' 
            continue # don't risk stripping out any real data
          #}

          value_parts = text_value.split( comment_start )
          new_value_parts = []
          new_value = ''
          i = -1
          for part in value_parts: #{
            i += 1
            comment = ''
            data = ''

            if i == 0: #{  # the first section (index 0) is before the comment
              data = part.strip()
            #}
            else: #{ # at start of a comment
              comment_end_count = part.count( comment_end )
              if comment_end_count != 1: #{
                print 'Mismatched start/end tags in:', part
                continue
              #}

              comment_and_data = part.split( comment_end )
              comment = comment_and_data[ 0 ]
              data    = comment_and_data[ 1 ].strip()
              
              print newline + 'About to remove the following comment:'
              print comment + newline
            #}

            if data: #{
              print newline + 'Retaining the following data:'
              print data + newline
              new_value_parts.append( data )
            #}
          #}

          new_value = "".join( new_value_parts )
          new_value = new_value.replace( "'", "''" ) # escape for SQL
          statement = "update %s set %s = '%s' where id = %d" % (table_name, field, new_value, row_id)

          print newline, '/* new value */', statement, newline
          the_cursor.execute( statement )
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
  
  stripComments()

##=============================================================================

