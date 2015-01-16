# -*- coding: utf-8 -*-
"""
Text fields where the user can enter formatting can end up getting extra, unwanted formatting
pasted in from other websites. This later interferes with searching, e.g. a search for 'background'
will bring up enormous numbers of irrelevant records. So strip out CSS in any <div>, <span> and <p> tags, 
as these cannot have been entered via the TinyMCE editor used in the admin interface.
May as well get rid of anchors too, as these are not ours.

By Sushila Burgess
"""
##=============================================================================

import sys
sys.path.append( '/home/mlgb/sites/mlgb/parts/index' )
import connectToMLGB as c

problem_tags_start = [ '<div ', '<span ', '<p ', '<a ' ]
closing_angle_bracket = '>'
percent = '%'

text_fields = {
  'books_book': [ 'evidence_notes', 'pressmark', 'ownership', 'notes' ],
  'books_contains': [ 'contains' ],
}

newline = '\n'

##=============================================================================

def stripUnwantedTags(): #{

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

    # Look at all the text fields that could contain unwanted formatting
    for table_name, field_names in text_fields.items(): #{
      #print newline + table_name + newline

      for field in field_names: #{
        #print newline + table_name + ': ' + field + newline

        # generate a select statement to pick up rows containing any of the problematic tags
        first_tag = True
        for problem_tag_start in problem_tags_start: #{
          if first_tag:
            select = "select id, %s from %s where %s like '%s%s%s'" \
                   % (field, table_name, field, percent, problem_tag_start, percent)
          else:
            select = "%s or %s like '%s%s%s'" % (select, field, percent, problem_tag_start, percent)
          first_tag = False
        #}
        select += " order by id"
        #print select
        the_cursor.execute( select )
        results = the_cursor.fetchall()

        # start working through the results
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

          for problem_tag_start in problem_tags_start: #{
            print 'Processing', problem_tag_start
            if problem_tag_start not in text_value: continue

            # Convert, e.g., '<div style="font-family: Courier New">' to just '<div>'
            value_parts = text_value.split( problem_tag_start )
            new_value_parts = []
            new_value = ''
            i = -1
            for part in value_parts: #{
              i += 1
              formatting = ''
              data = ''

              if i == 0: #{  # the first section (index 0) is before the formatting tag
                data = part
              #}
              else: #{ # at start of formatting tag

                formatting_and_data = part.split( closing_angle_bracket, 1 )
                
                if len( formatting_and_data ) != 2: #{
                  print 'Mismatched tag start and end in:', formatting_and_data
                  print 'Cancelling change.'
                  continue
                #}

                formatting = formatting_and_data[ 0 ]
                data       = formatting_and_data[ 1 ]
                
                #print newline + 'About to remove the following formatting:'
                #print formatting + newline
              #}

              new_value_parts.append( data )
            #}

            fixed_tag = problem_tag_start.strip() + closing_angle_bracket
            new_value = fixed_tag.join( new_value_parts )
            if fixed_tag == '<a>': # no point in keeping these
              new_value = new_value.replace( '<a></a>', '' )
            text_value = new_value

            new_value = new_value.replace( "'", "''" ) # escape for SQL
            new_value = new_value.replace( "\\", "\\\\" ) # escape for SQL
            statement = "update %s set %s = '%s' where id = %d" % (table_name, field, new_value, row_id)

            print newline, '/* new value */', statement, newline
            the_cursor.execute( statement )

          #} # end processing all problem tags in one field of one row of data
        #} # end loop through rows containing problem tags in a particular field
      #} # end loop through one table's fields that may contain problem tags
    #} # end loop through tables with fields that may contain problem tags

    the_cursor.close()
    the_database_connection.close()

  except:
    if the_cursor: the_cursor.close()
    if the_database_connection: the_database_connection.close()
    raise
#}

##=============================================================================

if __name__ == '__main__':
  
  stripUnwantedTags()

##=============================================================================

