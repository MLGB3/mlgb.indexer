# -*- coding: utf-8 -*-
"""
Create a preliminary version of output from Richard Sharpe's list.master.
By Sushila Burgess
"""
##=============================================================================

source='http://www.history.ox.ac.uk/fileadmin/ohf/documents/projects/List-of-Identifications.pdf'

##=============================================================================

import sys
import os
import MySQLdb
import HTMLParser
import connectToMLGB as c
from importIndexEntries import biblio_block_start_html, biblio_block_end_html

final_output_dir = '/home/mlgb/sites/mlgb/static/templates/authortitle/'
work_dir = '/home/mlgb/sites/mlgb/parts/index/work/'

mlgb_book_url = '/mlgb/book'
if_editable = '{% if editable %}/e{% endif %}'
medieval_catalogues_url = "/authortitle/medieval_catalogues"

indexmenu = "{% include 'includes/indexmenu.html' %}"

##=============================================================================

html_parser = HTMLParser.HTMLParser()
em_dash = html_parser.unescape( '&mdash;' )

tab = '\t'
newline = '\n'
carriage_return = '\r'
space = ' '

linebreak = '<br>'
right_arrow = '&rarr;'

letters_with_entries = [ 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I/J', 'K', 'L', 'M', 'N', 'O', 'P',
                         'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Z' ]

##=============================================================================

def writeAllHTMLFiles(): #{

  print 'Producing output for author/title index menu'
  writeOneHTMLFile( '' )

  for letter in letters_with_entries: #{
    print 'Producing output for letter %s' % letter
    writeOneHTMLFile( letter )
  #}

  print 'Finished producing output.'
#}

##=============================================================================

def writeOneHTMLFile( letter ): #{


  try:
    filename_without_path = 'index' + letter.replace( '/', '' ) + '.html'
    output_filename = work_dir + filename_without_path

    outfile_handle = file
    outfile_handle = open( output_filename, 'wb' ) # 'wb' allows entry of UTF-8

    produceOutput( letter, outfile_handle )

    outfile_handle.close()

    os.rename( output_filename, final_output_dir + filename_without_path )

  except:
    if isinstance( outfile_handle, file ):
      if not outfile_handle.closed : outfile_handle.close()
    raise
#}

##=============================================================================

def get_alphabet( uppercase = False ): #{

  alphabet = []

  first_letter = 'a'
  last_letter = 'z'
  if uppercase: #{
    first_letter = 'A'
    last_letter = 'Z'
  #}

  this_letter = first_letter
  while this_letter <= last_letter: #{
    alphabet.append( this_letter )
    this_letter = chr( ord( this_letter ) + 1 )
  #}

  return alphabet
#}
##=============================================================================

def replace_trailing_accents( the_string ): #{

  # Accents are represented by, e.g. "e<" for e-acute and "e>" for e-grave
  # Convert these to HTML entities, but without mangling any formatting tags you've already added.

  trailing_accents = { '<' : 'acute', 
                       '>' : 'grave', 
                       '|': 'uml',
                       '~': 'circ',
                     }

  preserve_tags = [ '<i>', '</i>', biblio_block_start_html, biblio_block_end_html, linebreak ]

  replace_less = 'LeSs*ThAn*SiGn'  # just use something that really is not going to occur in the text
  replace_greater = 'GrEaTeR*tHaN*sIgN'

  # Don't convert tags like <i> to i-acute
  for tag in preserve_tags: #{
    replacement = tag.replace( '<', replace_less )
    replacement = replacement.replace( '>', replace_greater )
    the_string = the_string.replace( tag, replacement )
  #}

  uppercase_yn = [ False, True ]
  for uppercase_it in uppercase_yn: #{
    for letter in get_alphabet( uppercase_it ): #{
      for unconverted_accent in trailing_accents.keys(): #{
        to_change = '%s%s' % (letter, unconverted_accent)
        if to_change in the_string: #{

          converted_accent = trailing_accents[ unconverted_accent ]

          # It *seems* (not 100% sure) that if a tilde follows a letter N, it stays a tilde
          # but in other circumstances, it becomes a circumflex.
          if converted_accent == 'circ' and letter in [ 'n', 'N' ]:
            converted_accent = 'tilde'

          html_entity = '&%s%s;' % (letter, converted_accent)
          the_string = the_string.replace( to_change, html_entity )
        #}
      #}
    #}
  #}

  # Restore <i> etc
  for tag in preserve_tags: #{
    replacement = tag.replace( '<', replace_less )
    replacement = replacement.replace( '>', replace_greater )
    the_string = the_string.replace( replacement, tag )
  #}

  return the_string
#}
##=============================================================================

def replace_curly_brace_tags( the_string ): #{

  # Something like {^x^} should become superscript x.
  # Cedillas are represented by {c,}
  # Various other characters should be replaced e.g. {P} becomes the paragraph symbol

  conversions = { '{^': '<sup>',
                  '^}': '</sup>',
                  '{P}': '&para;',
                  '{x}': '&times;',
                  '{c,}': '&ccedil;',
                  '{C,}': '&Ccedil;',
                  '{+}': '&dagger;',
                  '{sc}': '', # should be 'small capitals' - come back to this later
                }

  for replace_from, replace_to in conversions.iteritems(): #{
    if replace_from in the_string: #{
      the_string = the_string.replace( replace_from, replace_to )
    #}
  #}

  return the_string
#}
##=============================================================================

def replace_ligatures( the_string ): #{

  conversions = { 'A+E': '&AElig;',
                  chr(146): '&AElig;',
                  'a+e': '&aelig;',
                  chr(145): '&aelig;',
                  'O+E': '&OElig;',
                  'o+e': '&oelig;',
                }

  for replace_from, replace_to in conversions.iteritems(): #{
    if replace_from in the_string: #{
      the_string = the_string.replace( replace_from, replace_to )
    #}
  #}

  return the_string
#}
##=============================================================================

def replace_odd_chars( the_string ): #{

  conversions = { 
                  '++' : '&Dagger;', 
                  '%'  : '&sect;',
                  '.#.': '.&nbsp;.',
                }
  for replace_from, replace_to in conversions.iteritems(): #{
    if replace_from in the_string: #{
      the_string = the_string.replace( replace_from, replace_to )
    #}
  #}

  return the_string
#}
##=============================================================================

def replace_double_curly_braces( the_string ): #{

  conversions = { 
                  '{{' : '{% templatetag openvariable %}',
                  '}}' : '{% templatetag closevariable %}',
                }
  for replace_from, replace_to in conversions.iteritems(): #{
    if replace_from in the_string: #{
      the_string = the_string.replace( replace_from, replace_to )
    #}
  #}

  return the_string
#}
##=============================================================================

def strip_html_for_hover( the_string ): #{

  # Reverse some of the string conversions needed for HTML
  conversions = { '"'                              : "'",
                  '<i>'                            : '',
                  '</i>'                           : '',
                  biblio_block_start_html          : '',
                  biblio_block_end_html            : '',
                  '{% templatetag openvariable %}' : '{{',
                  '{% templatetag closevariable %}': '}}',
                }
  for replace_from, replace_to in conversions.iteritems(): #{
    if replace_from in the_string: #{
      the_string = the_string.replace( replace_from, replace_to )
    #}
  #}

  # Turn HTML entities into UTF-8 characters
  the_string = html_parser.unescape( the_string ) 

  return the_string
#}
##=============================================================================

def reformat( the_string, preserve_linebreaks = False ): #{

  if the_string == None: the_string = ''

  the_string = the_string.replace( '&', '&amp;' )
  the_string = the_string.replace( '<>', '&loz;' )
  the_string = the_string.replace( '{<}', '&lt;' )
  the_string = the_string.replace( '{>}', '&gt;' )

  the_string = the_string.replace( '---', '&mdash;' )
  the_string = the_string.replace( '--', '&ndash;' )

  the_string = the_string.replace( '&mdash;-', '&mdash;&mdash;' )
  the_string = the_string.replace( '&ndash;-', '&ndash;&ndash;' )

  the_string = the_string.replace( '&amp;#', '&#' ) # preserve Greek numeric character entities
  the_string = the_string.replace( '&amp;loz', '&loz' ) # preserve the diamond symbol

  the_string = replace_trailing_accents( the_string )
  the_string = replace_curly_brace_tags( the_string )
  the_string = replace_ligatures( the_string )
  the_string = replace_odd_chars( the_string )
  the_string = replace_double_curly_braces( the_string )

  if preserve_linebreaks:
    the_string = the_string.replace( newline, linebreak )

  return the_string
#}
##=============================================================================

def get_copy_code_and_desc( copy_code, seqno_in_document, copy_notes, hover_title, mlgb_links ): #{

  output_string = ''
  has_mlgb_links = False
  num_mlgb_links = len( mlgb_links )
  if num_mlgb_links > 0: has_mlgb_links = True

  # Either start a link to the MLGB book record...
  if has_mlgb_links: #{
    i = 0
    for mlgb_link_row in mlgb_links: #{
      mlgb_book_id = mlgb_link_row[ 0 ]
      output_string += get_mlgb_book_link( mlgb_book_id, hover_title )
      output_string += copy_code
      i += 1

      if num_mlgb_links > 1: #{ # unlikely, but just possible in theory if there were 2 copies?
        if i < num_mlgb_links: output_string += '</a>'
      #}
    #}
  #}

  # Or start a span which you can hover over and get a bit more info.
  else: #{
    onclick_title = hover_title.replace( newline, ' ' )
    onclick_title = onclick_title.replace( carriage_return, '' )
    onclick_title = onclick_title.replace( "'", "\\'" )

    output_string += '<span title="%s" class="index_catalogue_entry" ' % hover_title 
    output_string += ' onclick="alert(' + "'" + onclick_title + "'" + ')" '
    output_string += '>' 
    output_string += copy_code 
  #}

  # Add description/notes if there are any, 
  # e.g. 'sermones Ailmeri prioris in glosis' or '(1 copy) = K5.7'
  copy_notes = copy_notes.strip()
  if copy_notes: output_string += ' ' + copy_notes 

  # Finish the link or the span that we started above.
  if has_mlgb_links:
    output_string += '</a>'
  else:
    output_string += '</span>'

  return output_string
#}
##=============================================================================

def get_mlgb_book_link( mlgb_book_id, hover_title ): #{

  mlgb_book_link = '<a href="%s%s/%d/" ' % (if_editable, mlgb_book_url, mlgb_book_id) 
  mlgb_book_link += ' title="%s: full details of book" ' % hover_title  
  mlgb_book_link += ' class="link_from_index_to_book">' 

  return mlgb_book_link
#}
##=============================================================================

def write_link_to_source_file( handle, include_link_to_definitions = True ): #{

  handle.write( '<p>' + newline )
  handle.write( 'All data was derived from the <a href="%s"' % source )
  handle.write( ' title="List of Identifications (PDF) by Richard Sharpe" target="_blank">' ) 
  handle.write( 'List of Identifications</a> by Professor Richard Sharpe.' + newline )

  if include_link_to_definitions: #{
    handle.write( '{% if not printing %}' )
    handle.write( '<br/><em>A <a href="%s/decode/"' % medieval_catalogues_url )
    handle.write( ' title="Definition of codes used in the List" target="_blank">' )
    handle.write( 'key to codes</a> used in the List is available (opens in new tab).</em>' )
    handle.write( '{% endif %}' )
  #}

  handle.write( '</p>' + newline )

#}
##=============================================================================

def get_outer_div_for_expand_collapse( entry_id ): #{

  return 'entry%d_div' % entry_id
#}
##=============================================================================

def get_concertina_button_id( display_id ): #{

  display_id = str( display_id )
  return 'concertina%s' % display_id
#}
##=============================================================================

def get_book_id_for_expand_collapse( entry_id, entry_book_count ): #{

  return '%d_%d' % (entry_id, entry_book_count)
#}
##=============================================================================

def get_expand_collapse_script(): #{

  script = newline + newline

  script += ' <script type="text/javascript">'                             + newline
  script += ' function expand_or_collapse( display_id, action, depth ) {'  + newline

  script += '   var button_id = "concertina" + display_id;'                + newline
  script += '   var the_button = document.getElementById( button_id );'    + newline
  script += '   if( ! the_button ) {'                                      + newline
  script += '     return;'                                                 + newline
  script += '   }'                                                         + newline

  # Expand/collapse either the top-level entry (depth 1) or the inner list of books (depth 2)
  script += '   var element_type = "div";'                                 + newline
  script += '   if( depth == 2 ) {'                                        + newline
  script += '     element_type = "tab";'                                   + newline
  script += '   }'                                                         + newline
  script += '   var element_id="entry" + display_id + "_" + element_type;' + newline
  script += '   var the_element = document.getElementById( element_id );'  + newline
  script += '   if( ! the_element ) {'                                     + newline
  script += '     return;'                                                 + newline
  script += '   }'                                                         + newline

  script += '   if( action == "+" ) {'                                     + newline
  script += '     the_element.style.display = "block";'                    + newline
  script += '     the_button.value = "-";'                                 + newline
  script += '     the_button.innerHTML = "-";'                             + newline
  script += '   }'                                                         + newline
  script += '   else {'                                                    + newline
  script += '     the_element.style.display = "none";'                     + newline
  script += '     the_button.value = "+";'                                 + newline
  script += '     the_button.innerHTML = "+";'                             + newline
  script += '   }'                                                         + newline

  # If this is a top-level entry (depth 1), also expand/collapse the bibliography block
  script += '   if( depth == 1 ) {'                                        + newline
  script += '     element_id = "biblio_" + element_id;'                    + newline
  script += '     the_element = document.getElementById( element_id );'    + newline
  script += '     if( ! the_element ) {'                                   + newline
  script += '       return;'                                               + newline
  script += '     }'                                                       + newline
  script += '     if( action == "+" ) {'                                   + newline
  script += '       the_element.style.display = "block";'                  + newline
  script += '     }'                                                       + newline
  script += '     else {'                                                  + newline
  script += '       the_element.style.display = "none";'                   + newline
  script += '     }'                                                       + newline
  script += '   }'                                                         + newline

  script += ' }'                                                           + newline
  script += '</script>'                                                    + newline
  script += newline + newline

  return script
#}
##=============================================================================

def get_expand_and_collapse_all_script( ids_for_expand_collapse ): #{

  script = newline + newline
  script += '<script type="text/javascript">' + newline

  script += '  var idsOnPage = new Array( '
  first = True
  for i in ids_for_expand_collapse: #{
    if first: first = False
    else: script += ', '
    script += "'%s'" % i
  #}
  script += ' );' + newline

  script += '  var idDepths = new Array( '
  first = True
  for i in ids_for_expand_collapse: #{
    if first: first = False
    else: script += ', '
    script += str( get_indentation_depth( i ))
  #}
  script += ' );' + newline

  script += '  function expandAllEntries() {'                            + newline
  script += '    for (var i = 0; i < idsOnPage.length; i++ ) {'          + newline
  script += '      expand_or_collapse( idsOnPage[i], "+", idDepths[i] );'+ newline
  script += '    }'                                                      + newline
  script += '  }'                                                        + newline

  script += '  function collapseAllEntries() {'                          + newline
  script += '    for (var i = 0; i < idsOnPage.length; i++ ) {'          + newline
  script += '      expand_or_collapse( idsOnPage[i], "-", idDepths[i] );'+ newline
  script += '    }'                                                      + newline
  script += '  }'                                                        + newline

  script += '</script>'                                                  + newline
  script += newline + newline

  return script
#}
##=============================================================================

def get_indentation_depth( display_id ): #{

  if display_id.isdigit():  # outer, 'author' entry
    depth = 1
  else:                     # inner, 'book' entry
    depth = 2

  return depth
#}
##=============================================================================

def get_expand_collapse_button( display_id, button_value = '+' ): #{

  display_id = str( display_id )
  depth = get_indentation_depth( display_id )

  button_id = get_concertina_button_id( display_id )

  button_text = '{% if not printing %}' 

  button_text += '<button name="%s" id="%s" ' % (button_id, button_id)
  button_text += ' title="expand/collapse this section" class="concertina" '
  button_text += ' value="%s" ' % button_value
  button_text += ' onclick="expand_or_collapse('
  button_text += " '%s', this.value, %d )" % (display_id, depth)
  button_text += '">%s</button>' % button_value
  button_text += newline + newline

  button_text += '{% endif %}'

  return button_text
#}
##=============================================================================

def get_expand_collapse_span( display_id, span_text = '', span_class='' ): #{

  display_id = str( display_id )
  depth = get_indentation_depth( display_id )

  button_id = get_concertina_button_id( display_id )
  action = "getElementById( '%s' ).value" % button_id

  the_span =   '<span class="index_entry %s" ' % span_class 
  the_span +=  ' title="expand/collapse this section" ' 
  the_span +=  ' {% if not printing %}onclick="expand_or_collapse(' 
  the_span +=  " '%s', %s, %d " % (display_id, action, depth) 
  the_span +=  '){% endif %}">' 
  the_span +=  '%s</span>' % span_text.strip() 
  the_span +=  newline 

  return the_span
#}
##=============================================================================

def produceOutput( letter, handle ): #{

  # Connect to the database and create a cursor
  the_database_connection = c.get_database_connection()
  the_cursor = the_database_connection.cursor() 

  #......................................

  # Start writing the template
  handle.write( '{% extends "base.html" %}'               + newline )
  handle.write( '{% block title %}'                       + newline )
  handle.write( '<title>MLGB3 Author/Title Index</title>' + newline )
  handle.write( '{% endblock %}'                          + newline )

  #......................................

  # Write our own treeview expand/collapse function so that we can handle links
  # how we want rather than being constrained by the behaviour of the jQuery function.
  handle.write( '{% block treeview %}'                    + newline )
  handle.write( get_expand_collapse_script()              + newline )

  # Get entry/book IDs for use in expand/collapse script
  statement = 'select i.entry_id, b.entry_book_count from index_entries i, index_entry_books b '
  statement += " where i.entry_id = b.entry_id and i.letter = '%s' " % letter
  statement += " order by i.entry_id, b.entry_book_count"
  the_cursor.execute( statement )
  id_results = the_cursor.fetchall()
  ids_for_expand_collapse = []
  for row in id_results: #{
    e_id_string = str( row[ 0 ] )
    b_id_string = get_book_id_for_expand_collapse( row[ 0 ], row[ 1 ] )
    if e_id_string not in ids_for_expand_collapse:
      ids_for_expand_collapse.append( e_id_string )
    ids_for_expand_collapse.append( b_id_string )
  #}

  # Write "expand/collapse all" scripts
  handle.write( get_expand_and_collapse_all_script( ids_for_expand_collapse ))
  handle.write( '{% endblock %}' + newline )  # end 'treeview' block

  #......................................

  # Start writing the main page content
  handle.write( '{% block maincontent %}' + newline )
  handle.write( '<div class="index">' )
  handle.write( newline + newline )


  # Write page heading
  handle.write( '<h2>Browse Author/Title Index: %s</h2>' % letter )
  handle.write( newline )

  # Write navigation by initial letter
  handle.write( '{% if not printing %}<div class="letterlinks">' )
  for possible_letter in letters_with_entries: #{
    if possible_letter == 'I/J': possible_letter = 'IJ'
    selection_class = ''
    if possible_letter == letter: selection_class = ' class="selected" '
    handle.write( '<a href="%s/authortitle/browse/%s/" %s >%s</a>\n' \
                  % (if_editable, possible_letter, selection_class, possible_letter))
    if possible_letter != 'Z': handle.write( '<span class="spacer"> </span>' )
  #}
  handle.write( '</div><!-- end div "letterlinks" -->{% endif %}' )
  handle.write( newline + newline )

  if not letter: #{ # just a menu of the letters available

    # Add the Advanced Search form here to fill up the blank space.
    handle.write( "{% include 'includes/authortitle_adv_search.html' %}" + newline )

    write_link_to_source_file( handle )
    handle.write( '</div><!-- end div "index" -->' )
    handle.write( newline + indexmenu + newline)
    write_end_of_page( handle )
    the_cursor.close()
    the_database_connection.close()
    return
  #}

  #......................................

  # Start writing author/title treeview
  handle.write( '<div id="authortreecontrol">' + newline )
  handle.write( '{% if not printing %}' )
  handle.write( '<span class="like_a_link" onclick="collapseAllEntries()">Collapse All</span> ' )
  handle.write( ' | ' )
  handle.write( '<span class="like_a_link" onclick="expandAllEntries()">Expand All</span> ' )
  handle.write( '{% endif %}' )
  handle.write( newline )
  handle.write( '</div>' + newline )

  handle.write( '<ul class="authortreeview" id="authortree">' + newline )

  #......................................

  # Get entry details for main display 
  statement = "select * from index_entries where letter = '%s' order by entry_id" % letter
  the_cursor.execute( statement )
  entry_results = the_cursor.fetchall()

  # Start writing the main display of results
  for entry_row in entry_results: #{ # id, letter, name, xref name, biblio line, biblio block
    entry_id = entry_row[ 0 ]
    # we already know letter
    primary_name    = reformat( entry_row[ 2 ] )
    xref_name       = reformat( entry_row[ 3 ] )
    entry_bib_line  = reformat( entry_row[ 4 ] )
    entry_bib_block = reformat( entry_row[ 5 ] )

    # Get a version of the index entry without HTML entities, for use in title displayed on hover
    hover_primary_name = strip_html_for_hover( primary_name )
    prev_problem = ''

    # Get the books belonging to this entry
    statement = "select * from index_entry_books where entry_id = %d order by entry_book_count" \
              % entry_id
    the_cursor.execute( statement )
    book_results = the_cursor.fetchall()
    num_books = len( book_results )
    num_catalogue_entries = 0

    # Start writing out the entry
    handle.write( newline + newline )
    handle.write( '<!-- Start new entry "%s", entry ID %d -->' % (primary_name.strip(), entry_id) )
    handle.write( newline + '<a name="entry%d_anchor"></a>' % entry_id )
    handle.write( newline )
    handle.write( '<li class="outerhead">' + newline )

    is_expandable = False
    if num_books > 0 or entry_bib_line or entry_bib_block: 
      is_expandable = True

    if is_expandable: #{
      handle.write( get_expand_collapse_button( entry_id, '+' ) )
      handle.write( get_expand_collapse_span( entry_id, primary_name, 'outerhead' ) )
    #}
    else:
      handle.write( '<span class="outerhead">%s</span>' % primary_name.strip() )

    if xref_name: handle.write( ' %s %s' % (right_arrow, xref_name) )

    if is_expandable: #{

      if num_books == 1: #{ # could be just a dummy book, i.e. this is an entry by title not author
        title_of_book = book_results[ 0 ][ 3 ].strip()
        if not title_of_book: num_books = 0
      #}

      # This 'bibliography' section should be invisible when tree is fully collapsed.
      biblio_block_id = 'biblio_' + get_outer_div_for_expand_collapse( entry_id )
      handle.write( '<div id="%s" class="author_biblio_block" ' % biblio_block_id )
      handle.write( 'style="display:{%if printing%}block{%else%}none{%endif%}">' ) 

      if entry_bib_line: #{
        handle.write( entry_bib_line + newline )
      #}

      if entry_bib_line.strip() and entry_bib_block.strip(): #{
        handle.write( linebreak + newline )
      #}

      if entry_bib_block: #{
        handle.write( entry_bib_block + newline )
      #}
      handle.write( '</div>' )


      # An entry by title will still have medieval catalogue entries
      statement = "select count(*) from index_entry_copies where entry_id = %d" % entry_id
      the_cursor.execute( statement )
      total_row = the_cursor.fetchone()
      num_catalogue_entries = total_row[ 0 ]
        
      if num_books or num_catalogue_entries: #{
        handle.write( newline + '<div class="totals">' + newline )
        totals_string = ''
        if num_catalogue_entries:  #{
          if num_catalogue_entries == 1:
            catcount_desc = 'catalogue entry'
          else:
            catcount_desc = 'catalogue entries'
          totals_string = '%d %s' % (num_catalogue_entries, catcount_desc)
        #}
        if num_books: #{
          if num_books == 1:
            bookcount_desc = 'book'
          else:
            bookcount_desc = 'books'
          totals_string += ' (%d %s)' % (num_books, bookcount_desc) 
        #}
        handle.write( get_expand_collapse_span( entry_id, totals_string, 'outer_subhead totals' ))
        handle.write( '</div><!-- end "totals" div -->' )
      #}

      # Begin the section that expands and collapses
      # i.e. generally the author name with a hidden list of books below.
      handle.write( newline + '<div id="%s" class="expand_entry" ' \
                            % get_outer_div_for_expand_collapse( entry_id ) )
      handle.write( ' style="display:{%if printing%}block{%else%}none{%endif%}">' )

      # If there are multiple books for one author, provide link to expand/collapse them all at once
      if num_books > 1: #{
        if num_books == 2: expand_collapse_msg = 'both'
        else: expand_collapse_msg = 'all %d' % num_books
        expand_collapse_msg = ' %s books' % expand_collapse_msg

        book_ids = []
        for book in book_results: #{
          entry_book_count = book[ 1 ]
          book_ids.append( get_book_id_for_expand_collapse( entry_id, entry_book_count ) )
        #}

        handle.write( '<script type="text/javascript">' + newline )

        handle.write( '  function expand_books_for_entry_%d() { ' % entry_id )
        handle.write( newline )
        for book_id in book_ids: #{
          handle.write( "    expand_or_collapse( '%s', '+', 2 );" % book_id )
          handle.write( newline )
        #}
        handle.write( '  }' + newline )

        handle.write( '  function collapse_books_for_entry_%d() { ' % entry_id )
        handle.write( newline )
        for book_id in book_ids: #{
          handle.write( "  expand_or_collapse( '%s', '-', 2 );" % book_id )
          handle.write( newline )
        #}
        handle.write( '  }' + newline )

        handle.write( '</script>' + newline )

        handle.write( '{% if not printing %}' )
        handle.write( '<span class="like_a_link" onclick="collapse_books_for_entry_%d()">' % entry_id )
        handle.write( 'Collapse %s</span> ' % expand_collapse_msg )
        handle.write( ' | ' )
        handle.write( '<span class="like_a_link" onclick="expand_books_for_entry_%d()">' % entry_id )
        handle.write( 'Expand %s</span> ' % expand_collapse_msg )
        handle.write( linebreak + linebreak + newline )
        handle.write( '{% endif %}' )
      #}

      # Now start writing out the list of books
      handle.write( newline + '<ul><!-- start list of books -->' + newline )
    #}

    for book in book_results: #{ 0: entry_id, 1: entry_book_count, 2: role_in_book 
                              #  3: title_of_book, 4: book_biblio_line, 5: xref_title_of_book
                              #  6: copies, 7: problem

      entry_book_count   = book[ 1 ]
      role_in_book       = reformat( book[ 2 ] )
      title_of_book      = reformat( book[ 3 ] )
      book_biblio_line   = reformat( book[ 4 ] )
      xref_title_of_book = reformat( book[ 5 ] )
      copies             = reformat( book[ 6 ], preserve_linebreaks = True )
      problem            = reformat( book[ 7 ] )

      # Get a version of the book title without HTML entities, for use in title displayed on hover
      hover_title_of_book = strip_html_for_hover( title_of_book )

      if problem != prev_problem: #{
        handle.write( newline )
        handle.write( '<p>%s</p>' % problem )
        handle.write( newline )
        prev_problem = problem
      #}

      handle.write( newline + '<li>' )
      handle.write( '<!-- start entry ID %d, book %d -->' % (entry_id, entry_book_count) )
      handle.write( newline )

      statement = "select copy_code, copy_notes, document_name, doc_group_name, doc_group_type_name, " 
      statement += " document_code, seqno_in_document, copy_count "
      statement += " from index_entry_copies where entry_id = %d " % entry_id
      statement += " and entry_book_count = %d order by copy_count" % entry_book_count
      the_cursor.execute( statement )
      copy_results = the_cursor.fetchall()
      prev_copy_code = ''

      first_line_of_book_entry = role_in_book
      first_line_of_book_entry += title_of_book
      if book_biblio_line: first_line_of_book_entry += ": %s" % book_biblio_line
      if xref_title_of_book: first_line_of_book_entry += "%s %s" % (right_arrow, xref_title_of_book)

      # Write out the first line for this book, initially with the catalogue entries under it hidden
      book_id_for_expand_collapse = get_book_id_for_expand_collapse( entry_id, entry_book_count )

      if first_line_of_book_entry > '' and len( copy_results ) > 0: #{
        handle.write( get_expand_collapse_button( book_id_for_expand_collapse, '+' ) )
        handle.write( get_expand_collapse_span( book_id_for_expand_collapse, \
                                                first_line_of_book_entry, 'innerhead' ) )
      #}
      else:
        handle.write( first_line_of_book_entry )

      if len( copy_results ) > 0: #{
        if first_line_of_book_entry > '':
          initial_display_style = '{%if printing%}block{%else%}none{%endif%}'
        else:
          initial_display_style = 'block'

        handle.write( newline + '<table id="entry%s_tab" style="display:%s" ' \
                      % (book_id_for_expand_collapse, initial_display_style) )
        handle.write( ' class="catalogue_entries">' )
        handle.write( newline )
        handle.write( '<tr class="catalogue_entry_head"><td>Catalogue entry</td>' )
        handle.write( '<td>Catalogue</td></tr>' )
        handle.write( newline )

        for one_copy in copy_results: #{

          copy_code           = reformat( one_copy[ 0 ] )
          copy_notes          = reformat( one_copy[ 1 ] )
          document_name       = reformat( one_copy[ 2 ] )
          doc_group_name      = reformat( one_copy[ 3 ] )
          doc_group_type_name = reformat( one_copy[ 4 ] )
          document_code       = one_copy[ 5 ]
          seqno_in_document   = one_copy[ 6 ]
          copy_count          = one_copy[ 7 ]

          if copy_code == prev_copy_code: continue
          prev_copy_code = copy_code

          hover_title = hover_primary_name
          if hover_title_of_book: hover_title += ' ' + em_dash + ' ' + hover_title_of_book

          # See if we have got any links to the actual MLGB database
          mlgb_links = []
          if seqno_in_document == None: seqno_in_document = '0'

          statement  = "select mlgb_book_id from index_mlgb_links "
          statement += " where document_code = '%s' and seqno_in_document = %s " \
                     % (document_code, seqno_in_document)
          statement += " and seqno_in_document > 0 order by mlgb_book_id" 
          the_cursor.execute( statement )
          mlgb_links = the_cursor.fetchall()

          handle.write( newline + '<!-- start entry %d, book %d, copy %d -->' \
                        % (entry_id, entry_book_count, copy_count) )
          handle.write( newline + '<tr class="catalogue_entry">' + newline )

          handle.write( '<td class="catalogue_entry_code">' )
          handle.write( get_copy_code_and_desc( copy_code, seqno_in_document, copy_notes, \
                                                hover_title, mlgb_links ) )
          handle.write( '</td>' )
          handle.write( newline )

          handle.write( '<td class="catalogue_name">' )
          handle.write( newline )
          handle.write( '<a href="%s%s/%s"' % (if_editable, medieval_catalogues_url, document_code))
          handle.write( ' title="Further details of catalogue %s" ' % document_code )
          handle.write( ' class="link_to_catalogue" >' )
          if doc_group_type_name:
            handle.write( doc_group_type_name )
          if doc_group_name: #{
            if not doc_group_type_name.endswith( doc_group_name ): #{
              handle.write( ': %s' % doc_group_name )
            #}
          #}
          if document_name: handle.write( ': %s' % document_name )
          handle.write( '</a>' )
          handle.write( '</td>' )
          handle.write( newline )

          handle.write( newline + '</tr>' )
        #}

        handle.write( newline + '</table>' + newline )
      #}

      handle.write( '</li><!-- end of one book -->' )
      handle.write( newline + newline ) # make it a bit clearer by having a proper gap between books
    #}

    if is_expandable: #{
      handle.write( newline + '</ul><!-- end list of books for one author -->' + newline )
      handle.write( newline + '</div><!-- end outer expandable/collapsible section -->' + newline )
    #}

    handle.write( newline + '</li><!-- end outerhead list item -->' )
    handle.write( newline + '<!-- end entry ID %d (%s) -->' % (entry_id, primary_name.strip()) )
  #}

  handle.write( '</ul><!-- end tree -->' + newline )


  write_link_to_source_file( handle )
  handle.write( '</div><!-- end div class "index" -->' )
  handle.write( newline )

  handle.write( newline + indexmenu + newline)

  handle.write( newline + '{% if printing %}<script>window.print();</script>{% endif %}' + newline )
  write_end_of_page( handle )

  # Close your cursor and your connection
  the_cursor.close()
  the_database_connection.close()

#}

##=============================================================================

def write_end_of_page( handle ): #{

  handle.write( '{% endblock %}' + newline )

  handle.write( '{% block search %}' + newline )
  handle.write( '{% endblock %}' + newline )

  handle.write( '{% block useful_links %}' + newline ) 
  handle.write( '{% endblock %}' + newline )
#}
##=============================================================================

if __name__ == '__main__':


  # These two lines are hacks (copied from Mat's clever hack, thanks Mat). 
  # They switch the default encoding to utf8 so that the command line will convert UTF8 + Ascii to UTF8
  reload(sys)
  sys.setdefaultencoding("utf8")

  writeAllHTMLFiles()

##=============================================================================

