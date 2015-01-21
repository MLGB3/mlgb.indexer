# -*- coding: utf-8 -*-
"""
Read the file 'list.master' and parse the text into fields suitable for use in 
indexing.
Save the data in tables 'index_entries' and 'index_entry_books'.
By Sushila Burgess
"""
##=============================================================================

import sys

from common import virtualenv_root

#==================
# Read-only globals
#==================

input_filename  = virtualenv_root + "/parts/index/list.master" 
output_filename = virtualenv_root + "/parts/index/insert_index_entries_and_entry_books.sql" 

tab = '\t'
newline = '\n'
carriage_return = '\r'

entry_start_tag = '$$'
xref_start_tag = '-->'
title_start_tag = '-----'
copy_start_tag = '  ' # copies start on a line with 2 spaces
heading_start_tag = '$c'

italic_tag = '_'
comment_continuation_tag = '##'
no_more_records = '.sub' # introduces a final section of notes on when the last revision was, etc

biblio_block_start_html = '<span class="biblio_block">'
biblio_block_end_html = '</span>'

start_tag_replacements = {
  '.sm': biblio_block_start_html,
}
end_tag_replacements = {
  '.smz': biblio_block_end_html,
}

problem_categories = [
  '[app.]',
  '[attrib.]',
  '[dub.]',
  '[pseud.]',
  '[unidentified]',
  '[<i>app.</i>]',
  '[<i>attrib.</i>]',
  '[<i>dub.</i>]',
  '[<i>pseud.</i>]',
  '[<i>unidentified</i>]',
]

#=========================
# Globals that get changed
#=========================
letter = ''
current_field = ''
entry_id = None
entry_book_count = None
problem = None
already_in_italics = None

##=============================================================================

def clear_globals(): #{

  global current_field
  global entry_id
  global entry_book_count
  global problem

  current_field = ''

  entry_id = 0
  entry_book_count = 0

  problem = ''
  already_in_italics = False
#}

##=============================================================================

def rewriteDataFile(): #{

  clear_globals()

  #=================================================================
  # Read each line of the original file, manipulate it as necessary,
  # and then write it into the new file.
  #=================================================================
  try:
    infile_handle = file
    outfile_handle = file

    infile_handle = open( input_filename, 'r' )
    outfile_handle = open( output_filename, 'wb' ) # 'wb' allows entry of UTF-8

    outfile_handle.write( newline )
    outfile_handle.write( '-- This SQL script is generated by importIndexEntries.py.' )
    outfile_handle.write( newline )

    for line_of_file in infile_handle.readlines(): #{
      if line_of_file.strip() == no_more_records: break # last few lines are just footnotes

      processed_line = ''
      sql_statements = process_line( line_of_file )
      processed_line = newline.join( sql_statements )

      if processed_line: #{
        outfile_handle.write( processed_line.encode( 'utf-8' ))
        outfile_handle.write( newline )
      #}
    #}

    outfile_handle.close()
    infile_handle.close()

  except:
    if isinstance( infile_handle, file ):
      if not infile_handle.closed : infile_handle.close()
    if isinstance( outfile_handle, file ):
      if not outfile_handle.closed : outfile_handle.close()
    raise
#}

##=============================================================================

def reformat( the_string ): #{

  global already_in_italics

  the_string = the_string.replace( "'", "''" ) # escape single quotes for SQL

  # sometimes the 'title start tags' contain the wrong number of dashes
  if the_string.startswith( '---- ' ):  # one dash too short
    the_string = title_start_tag + the_string[ len( '----' ): ]
  elif the_string.startswith( '----,' ):  # also one dash too short
    the_string = title_start_tag + the_string[ len( '----' ): ]
  elif the_string.startswith( '------' ):  # one dash too long
    the_string = title_start_tag + the_string[ len( '------' ): ]

  while italic_tag in the_string: #{
    if already_in_italics: #{
      replacement = '</i>'
      already_in_italics = False
    #}
    else: #{
      replacement = '<i>'
      already_in_italics = True
    #}

    the_string = the_string.replace( italic_tag, replacement, 1 )
  #}

  # replace end tags before start tags, so that, e.g., we don't change '.smz' to '<span type="x">z'
  for end_tag in end_tag_replacements.keys(): #{
    if end_tag in the_string: #{
      replace_end = end_tag_replacements[ end_tag ]
      the_string = the_string.replace( end_tag, replace_end )
    #}
  #}
  for start_tag in start_tag_replacements.keys(): #{
    if start_tag in the_string: #{
      replace_start = start_tag_replacements[ start_tag ]
      the_string = the_string.replace( start_tag, replace_start )
    #}
  #}
  
  the_string = the_string.replace( comment_continuation_tag, '' )

  return the_string
#}

##=============================================================================

def get_main_insert_statement(): #{

  statement = "insert into index_entries ( entry_id, letter ) values ( %d, '%s' );" \
            % (entry_id, letter)
  return statement
#}
##=============================================================================

def get_main_update_statement( value ): #{

  statement = "update index_entries set %s = concat( %s, '%s' ) where entry_id = %d;" \
            % (current_field, current_field, value, entry_id)
  return statement
#}
##=============================================================================

def get_book_insert_statement( title_of_book, role_in_book = '' ): #{

  statement = "insert into index_entry_books "
  statement += " (entry_id, entry_book_count, title_of_book, role_in_book, problem) "
  statement += " values (%d, %d, '%s', '%s', '%s');" \
            % (entry_id, entry_book_count, title_of_book, role_in_book, problem.strip())
  return statement
#}
##=============================================================================

def get_book_update_statement( value ): #{

  statement = "update index_entry_books set %s = concat( %s, '%s' ) " \
            % (current_field, current_field, value)
  statement += " where entry_id = %d and entry_book_count = %d;" % (entry_id, entry_book_count)
  return statement
#}
##=============================================================================

def is_start_of_new_book( line_of_file ): #{

  if line_of_file.startswith( title_start_tag ):
    return True
  else:
    return False
#}
##=============================================================================

def parse_three_part_line( line_of_file ): #{

  primary_name = ''
  xref_name = ''
  comment = ''

  # Is this a main entry or a cross-reference entry?
  # If it's a cross-reference entry, extract cross-referenced name.
  line_parts = line_of_file.split( xref_start_tag, 1 )
  if len( line_parts ) == 2: #{
    xref_name = line_parts[ 1 ].lstrip()
  #}

  # Extract primary name and possibly a comment
  start_of_line = line_parts[ 0 ] 

  # Is there a comment (introduced by colon)?
  # If so, extract the comment.
  line_parts = start_of_line.split( ':', 1 )
  if len( line_parts ) == 2: #{
    comment = line_parts[ 1 ].lstrip()
    if comment == '': #{  line actually ended in a colon
      comment = ' '
    #}
  #}

  # Extract the primary name
  primary_name = line_parts[ 0 ].lstrip()
 
  return primary_name, comment, xref_name
#}

##=============================================================================

def parse_two_part_line( line_of_file ): #{ # a comment may be followed by a cross-referenced name

  xref_name = ''
  comment = ''

  line_parts = line_of_file.split( xref_start_tag, 1 )

  comment = line_parts[ 0 ]

  if len( line_parts ) == 2: #{
    xref_name = line_parts[ 1 ].lstrip()
  #}

  return comment, xref_name
#}

##=============================================================================

def parse_first_line_of_book( value ): #{

  primary_name = ''
  xref_name = ''
  comment = ''
  role_in_book = ''

  primary_name, comment, xref_name = parse_three_part_line( value )
 
  # if role in book is given, it appears at the start of the first line of the book, in brackets,
  # e.g. '(as translator) --> The Works of Joe Bloggs'

  if primary_name.strip().startswith( '(' ) \
  and primary_name.strip().endswith( ')' ) \
  and xref_name.strip(): #{
    role_in_book = primary_name
    primary_name = ''
  #}

  return role_in_book, primary_name, comment, xref_name
#}

##=============================================================================

def get_initial_letter( value ): #{

  if not value.startswith( heading_start_tag ): return ''

  value = value[ len( heading_start_tag ): ] # strip off the start tag
  value = value.replace( '\\', '' )
  value = value.strip()

  if len( value ) == 1 and value.isalpha() and value.isupper():
    return value
  elif value == 'I/J':
    return value
  else:
    return ''
#}
##=============================================================================

def process_line( value ): #{

  global current_field
  global entry_id
  global entry_book_count
  global problem
  global letter

  if not value: return []

  if value.startswith( heading_start_tag ): #{ heading for entries starting with A, with B, etc
    value = get_initial_letter( value )
    if value: letter = value
    return []
  #}

  value = reformat( value )

  line = ''
  lines = []
  line_parts = []
  entry_name = ''

  primary_name = ''
  comment = ''
  xref_name = ''

  #=============================
  # If at start of new record...
  #=============================
  if value.startswith( entry_start_tag ): #{
    next_entry_id = entry_id + 1
    clear_globals()
    entry_id = next_entry_id

    value = value[ len( entry_start_tag ): ] # strip off the initial '$$' tag

    # Insert a new entry into the 'index entries' table, 
    # then start adding the rest of the data via a series of update statements.
    line = newline + get_main_insert_statement()
    lines.append( line )

    # The initial line for an entry may need dividing into up to three parts.
    # First, extract the name (author or title) given as the main index entry.
    # Secondly, there may also be a bibliographical comment (introduced by a colon).
    # Thirdly, there may be a cross-referenced name.

    primary_name, comment, xref_name = parse_three_part_line( value )

    # Save primary name
    current_field = 'entry_name'
    line = get_main_update_statement( primary_name )
    lines.append( line )

    # Save bibliographical comment, if any.
    if comment: #{
      current_field = 'entry_biblio_line'
      line = get_main_update_statement( comment )
      lines.append( line )
    #}

    # Add the cross-referenced name, if any.
    if xref_name: #{
      current_field = 'xref_name'
      line = get_main_update_statement( xref_name )
      lines.append( line )
    #}

    return lines
  #}

  #==================================
  # Already in the middle of a record 
  #==================================
  else: #{ 
    if not entry_id: return [] # in middle of record UNLESS you have not reached the first record yet

    #===================================================
    # If at start of new book title, insert a new record 
    # in the 'index entry books' table then return.
    #===================================================
    if is_start_of_new_book( value ): #{
      entry_book_count += 1

      value = value[ len( title_start_tag ) : ] # strip off title start tag
      if value.startswith( ',' ):  # most tags have the title start tag ending in comma: '-----,'
        value = value[ 1: ]

      value = value.lstrip()

      role_in_book, primary_name, comment, xref_name = parse_first_line_of_book( value )
      current_field = 'title_of_book'

      # Save title of book and in some cases person's role in book (e.g. translator)
      line = get_book_insert_statement( primary_name, role_in_book )
      lines.append( line )

      # Save bibliographical comment, if any.
      if comment: #{
        current_field = 'book_biblio_line'
        line = get_book_update_statement( comment )
        lines.append( line )
      #}

      # Add the cross-referenced name, if any.
      if xref_name: #{
        current_field = 'xref_title_of_book'
        line = get_book_update_statement( xref_name )
        lines.append( line )
      #}

      return lines
    #}

    #=======================================================================
    # If not a new book or a new index entry, work out which field we're on.
    # We may still be processing the same field as on the last line.
    # Or, we may need to change the name of the field we are processing.
    #=======================================================================

    # Free-standing notes on a separate line from the author name or book title
    if value.strip() == biblio_block_start_html:
      current_field = 'entry_biblio_block'

    # Heading such as [pseud] or [dub.] to indicate problematic identification
    elif value.strip() in problem_categories: #{
      current_field = 'problem'
      problem = value
    #}

    # Normally, lines starting with 2 spaces contain document numbers to identify individual copies.
    # However, an exception to this rule seems to be new paragraphs within the bibliography block.
    elif value.startswith( copy_start_tag ) and current_field != 'entry_biblio_block' : #{
      current_field = 'copies'
    #}

    #===============================================
    # Parse the line and save the individual fields.
    #===============================================
    # See if you need to sub-divide the line. E.g. the 'primary name' field may have continued
    # into a second line, and now there may be a comment or a cross-referenced name.

    # Multi-part lines in the MAIN entry
    if current_field in [ 'entry_name', 'entry_biblio_line' ]: #{
      if current_field == 'entry_name':
        primary_name, comment, xref_name = parse_three_part_line( value )
      else:
        comment, xref_name = parse_two_part_line( value )

      # Save continuation of author name or book title
      if primary_name: #{
        line = get_main_update_statement( primary_name )
        lines.append( line )
      #}

      # Save bibliographical comment, if any.
      if comment: #{
        current_field = 'entry_biblio_line'
        line = get_main_update_statement( comment )
        lines.append( line )
      #}

      # Add the cross-referenced name, if any.
      if xref_name: #{
        current_field = 'xref_name'
        line = get_main_update_statement( xref_name )
        lines.append( line )
      #}
    #}

    # Multi-part lines in the BOOK entry
    elif current_field in [ 'title_of_book', 'book_biblio_line' ]: #{
      if current_field == 'title_of_book':
        primary_name, comment, xref_name = parse_three_part_line( value )
      else:
        comment, xref_name = parse_two_part_line( value )

      # Save continuation of book title
      if primary_name: #{
        line = get_book_update_statement( primary_name )
        lines.append( line )
      #}

      # Save bibliographical comment, if any.
      if comment: #{
        current_field = 'book_biblio_line'
        line = get_book_update_statement( comment )
        lines.append( line )
      #}

      # Add the cross-referenced name, if any.
      if xref_name: #{
        current_field = 'xref_title_of_book'
        line = get_book_update_statement( xref_name )
        lines.append( line )
      #}
    #}

    # Simple lines in either the main or book entries
    elif current_field in [ 'copies', 'xref_title_of_book' ]: #{

      if current_field == 'copies' and entry_book_count == 0: #{
        # Ah, but not so simple after all! Some entries have the book title as the main entry
        # (as opposed to the author name) so there is no 'start of book' section to pick up on.
        # So in that case, we won't yet have inserted a 'book' row and the copies will get lost.
        entry_book_count = 1
        line = get_book_insert_statement( '' )
        lines.append( line )
      #}

      line = get_book_update_statement( value )
      lines.append( line )
    #}

    elif current_field == 'problem':
      pass # problematic identification type will be set up as each new book is inserted

    else: #{
      if value.strip(): #{
        line = get_main_update_statement( value )
        lines.append( line )
      #}
    #}
  #}

  return lines
#}

##=============================================================================

if __name__ == '__main__':


  # These two lines are hacks (copied from Mat's clever hack, thanks Mat). 
  # They switch the default encoding to utf8 so that the command line will convert UTF8 + Ascii to UTF8
  reload(sys)
  sys.setdefaultencoding("utf8")

  rewriteDataFile()

##=============================================================================

