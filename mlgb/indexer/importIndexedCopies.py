import sys
import MySQLdb
import connectToMLGB as c
##=====================================================================================

newline = '\n'
comma = ','
equals_sign = '='
space = ' '
full_stop = '.'
question_mark = '?'
double_dash = '--'
plus_sign = '+'
ampersand = '&'
colon = ':'

copy_code_connectors = [ equals_sign, plus_sign, ampersand ]

survives_flag = '*'
misc_flags = [ '{<}', '{+}', '{^a^}', '{^i^}', '{^m^}', '{^o^}', 
               '{P}', '{^um^}', '{^us^}', '{^x^}', '++', '<>', '<i>bis</i>' ]

output_filename = "/home/mlgb/sites/mlgb/parts/index/insert_index_entry_copies.sql" 

known_typos = {

  'A20. 1289--1296':
  'A20.1289--1296',

  '(6 copies), A20. 1933a':
  '(6 copies), A20.1933a',

  'B39. 264l (attrib. Cyprian)':
  'B39.264l (attrib. Cyprian)',

  'B44.23 = B45. 34 (attrib. Alcuin)':
  'B44.23 = B45.34 (attrib. Alcuin)',

  'B89.8 = B90. 10':
  'B89.8 = B90.10',

  '  BA1. 750':
  '  BA1.750',
 
  ', BA1. 799{^x^},':
  ', BA1.799{^x^},',

  '  BA1. 1093h':
  '  BA1.1093h',

  'BA1..445': 
  'BA1.445',

  'Ba1.1167c':
  'BA1.1167c',

  "BA1.1267e (`liber de floribus naturarum Geberi'), BA1. 1275k":
  "BA1.1267e (`liber de floribus naturarum Geberi'), BA1.1275k",

  "BP2.33 = BP23. 14":
  "BP2.33 = BP23.14",

  "F18.2 = F19. 38":
  "F18.2 = F19.38",

  "B79.*92 = H2.* 728a":
  "B79.*92 = H2.*728a",

  "K667.20 (`epistolarum cclx lib. 1') ?= B13":
  "K667.20 (`epistolarum cclx lib. 1') ?= B13.17",  # not sure if this is right

  ", P6. 108o,":
  ", P6.108o,",

  ", P6. 90a (tabula),":
  ", P6.90a (tabula),",

  "Petri de Samine') = S2. 107":
  "Petri de Samine') = S2.107",

  "fo.) = S2. 18,":
  "fo.) = S2.18,",

  "SH62. 53--54 (uetus, 2 copies)":
  "SH62.53--54 (uetus, 2 copies)",

  "UC49. 60 (`Abraham de luminaribus')":
  "UC49.60 (`Abraham de luminaribus')",

  "UC11.48 = UC143. 16c":
  "UC11.48 = UC143.16c",

  "UO1. 71 (`Serapion in practica')":
  "UO1.71 (`Serapion in practica')",

  "(`secunda pars') = UO6. 201":
  "(`secunda pars') = UO6.201",

  "UO33.{P}P*211":
  "UO33.{P}*211",

  "UO33.{P}P*187":
  "UO33.{P}*187",

  'UO24.{P}*2(^x^} = UO33.{P}*6d':
  'UO24.{P}*2{^x^} = UO33.{P}*6d',

  "(`librum Ysidori', 2nd fo.),UO68.*388":
  "(`librum Ysidori', 2nd fo.), UO68.*388",

  'UO46.{+}79 )`commentum [_illegible_] super librum de anima in duobus':
  'UO46.{+}79 (`commentum [_illegible_] super librum de anima in duobus',

  'U33.{P}141,': 
  'UO33.{P}141,',

  'UO22.*28{^x^},UO24.{P}*53c':
  'UO22.*28{^x^}, UO24.{P}*53c',

  'UO22.*5{^x^},UO24.{P}*53a':
  'UO22.*5{^x^}, UO24.{P}*53a',

  'Z14.283b, Z14. 284a,':
  'Z14.283b, Z14.284a,',
}

##=====================================================================================

def is_copy_code( word ): #{

  if not full_stop in word: return False

  if word.endswith( comma ): word = word.replace( comma, '', 1 )
  if word.endswith( newline ): word = word.replace( newline, '', 1 )
  if word.endswith( colon ): word = word.replace( colon, '', 1 )

  # There are a few copy codes of the format BA1.821.4
  word_parts = word.split( full_stop )
  if len( word_parts ) == 3: #{
    last_part = word_parts[ 2 ]
    if last_part.isdigit():  # found a copy code of the 3-part pattern, e.g. BA1.821.4
      word = full_stop.join( word_parts[ 0 : 2 ] )
    else:
      return False
  #}

  word = word.replace( full_stop, '', 1 )
  word = word.replace( survives_flag, '', 1 )
  word = word.replace( double_dash, '', 1 )
  word = word.replace( question_mark, '', 1 )

  for flag in misc_flags: 
    word = word.replace( flag, '' )

  if not word.isalnum(): return False

  first_char = word[ 0 : 1 ]
  if not first_char.isalpha() or not first_char.isupper(): return False

  second_char = word[ 1 : 2 ]
  if not (second_char.isdigit() or second_char.isupper()): return False

  contains_numeric_chars = False
  for one_char in word[ : ]: #{
    if one_char.isdigit(): #{
      contains_numeric_chars = True
      break
    #}
  #}

  if not contains_numeric_chars: return False
  return True
#}

##=====================================================================================

def is_document_code( word ): #{

  if word.endswith( comma ): word = word.replace( comma, '', 1 )
  if word.endswith( newline ): word = word.replace( newline, '', 1 )

  if not word.isalnum(): return False
  if len( word ) < 2: return False # we need at least one uppercase letter and one number

  first_char = word[ 0 : 1 ]
  if not first_char.isalpha() or not first_char.isupper(): return False

  second_char = word[ 1 : 2 ]
  if not (second_char.isdigit() or second_char.isupper()): return False

  if second_char.isalpha():
    numbers_start = 2
  else:
    numbers_start = 1
  if len( word ) < numbers_start + 1: return False
    
  for one_char in word[ numbers_start: ]:
    if not one_char.isdigit(): return False

  return True
#}

##=====================================================================================

def get_document_code( copy_code ): #{

  code_parts = copy_code.split( full_stop )
  return code_parts[ 0 ]
#}

##=====================================================================================

def get_seqno_in_document( copy_code ): #{

  seqno = ''
  code_parts = copy_code.split( full_stop )
  if len( code_parts ) < 2: return ''

  second_part = code_parts[ 1 ]
  second_part = second_part.replace( survives_flag, '', 1 )
  second_part = second_part.replace( question_mark, '', 1 )
  for flag in misc_flags: 
    second_part = second_part.replace( flag, '' )

  if double_dash in second_part: #{  # indicates a range, e.g. 793--4
    dash_pos = second_part.find( double_dash )
    second_part = second_part[ 0 : dash_pos ] # for now, just strip off end of range
  #}

  if not second_part.isalnum(): return ''

  for one_char in second_part[ : ]: #{
    if one_char.isdigit():
      seqno += one_char
    else:
      break
  #}

  return seqno
#}

##=====================================================================================

def is_numeric_range( copy_code ): #{

  if double_dash not in copy_code: return False

  start_and_end_of_range = copy_code.split( double_dash, 1 )
  end_of_range = start_and_end_of_range[ 1 ]

  if end_of_range.isdigit():
    return True
  else:
    return False
#}

##==============================================================mm=======================

def get_rest_of_numeric_range( copy_code ): #{

  rest_of_range = []
  if not is_numeric_range( copy_code ): return []

  start_of_range = get_seqno_in_document( copy_code )
  end_of_range = copy_code.split( double_dash, 1 )[ 1 ]

  int_start = int( start_of_range )
  int_end = int( end_of_range )

  if int_end < int_start: #{  # e.g. 47--8 gives start 47, end 8
    prefix = start_of_range[ 0 : 0 - len( end_of_range ) ] # e.g. '47' gives '4'
    end_of_range = prefix + end_of_range # then '8' becomes '48'
    int_end = int( end_of_range )
  #}

  int_copy = int_start
  while int_copy < int_end: #{
    int_copy += 1
    rest_of_range.append( int_copy )
  #}

  return rest_of_range
#}

##==============================================================mm=======================

def strip_bits_in_brackets( the_line ): #{

  if '(' not in the_line and ')' not in the_line: return the_line

  line_parts = the_line.split( '(' )
  num_parts = len( line_parts )
  keep = []
  current_part = 0

  for line_part in line_parts: #{
    current_part += 1
    codestring = ''

    if ')' in line_part: #{
      sub_parts = line_part.split( ')' ) # there could be multiple nested brackets,
                                         # so get the text after the FINAL bracket
      last_part = len( sub_parts ) - 1
      codestring = sub_parts[ last_part ]
    #}
    elif num_parts > 1 and current_part == 1: #{ get the bit before the first opening bracket 
      codestring = line_part
    #}

    if codestring: #{
      keep.append( codestring )
    #}
  #}

  return newline.join( keep )
#}
##=====================================================================================


def correct_typos( the_string ): #{

  for typo in known_typos.keys(): #{
    if typo in the_string: #{
      correction = known_typos[ typo ]
      the_string = the_string.replace( typo, correction )
    #}
  #}

  return the_string
#}
##=====================================================================================

def get_copy_insert_statement( entry_id, entry_book_count, copy_count, copy_code, \
                               document_code, seqno_in_document, copy_notes ): #{

  statement = 'insert into index_entry_copies ( entry_id, entry_book_count, copy_count,' \
            + ' copy_code, document_code, seqno_in_document, copy_notes ) values ' \
            + "( %d, %d, %d, '%s', '%s', %s, '%s' )" \
            % (entry_id, entry_book_count, copy_count, copy_code, document_code, seqno_in_document, \
              copy_notes.replace( "'", "''" ))

  statement += ';' + newline + newline 
  return statement
#}
##=====================================================================================

def parseCopies(): #{

  # Write the SQL to a file. We can then store this in Subversion and revert to it if necessary.
  outfile_handle = open( output_filename, 'wb' ) # 'wb' allows entry of UTF-8
  outfile_handle.write( newline )
  outfile_handle.write( '-- This SQL script is generated by importIndexedCopies.py.' )
  outfile_handle.write( newline )

  # Connect to the database
  the_database_connection = c.get_database_connection()

  # Create a Cursor object
  the_cursor = the_database_connection.cursor() 

  # Clear out the destination table ('index entry copies') before you begin
  outfile_handle.write( newline + "TRUNCATE TABLE index_entry_copies;" + newline + newline )

  # Get the 'copies' text field from the source table ('index entry books')
  statement = "SELECT e.entry_id, b.entry_book_count, b.copies, e.entry_name, b.title_of_book " \
            + " FROM index_entry_books b, index_entries e" \
            + " WHERE b.entry_id = e.entry_id " \
            + " order by entry_id, entry_book_count"
  the_cursor.execute( statement )
  results = the_cursor.fetchall()

  # Extract the copy IDs from the text field, and from each copy ID extract
  # the document code and sequence number.
  for row in results: #{
    entry_id = row[0]
    entry_book_count = row[1]
    copies = row[2]
    entry_name = row[3]
    title_of_book = row[4]

    outfile_handle.write( '%s%s/*Entry ID %d, book count %d*/%s' \
                          % (newline, newline, entry_id, entry_book_count, newline))

    author_and_title_comment = "/* %s %s */%s" % (entry_name, title_of_book, newline)
    outfile_handle.write( author_and_title_comment )
    print author_and_title_comment, 'Book count', entry_book_count

    # Remove a few known typo's
    copies = correct_typos( copies )

    copies_comment = "%s/* %s */%s" % (newline, copies, newline)
    outfile_handle.write( copies_comment )

    # Remove any final full stops, as these can cause the final copy code not to be recognised
    if copies.strip().endswith( full_stop ):
      copies = copies.strip()[ 0 : -1 ]
    
    # Remove the 'notes' sections between brackets before trying to extract the copy codes
    full_copies = copies
    copies = strip_bits_in_brackets( copies )

    copy_count = 0
    copy_codes = []
    words = copies.split() # since no separator is specified, any whitespace is used as the separator

    for word in words: #{

      copy_code = ''
      document_code = ''
      seqno_in_document = ''
      is_valid_document_code = False

      if not is_copy_code( word ): #{
        if is_document_code( word ): #{
          # Try to avoid picking up bibliographical references that are NOT document codes
          checkword = word
          if checkword.endswith( comma ): checkword = checkword.replace( comma, '', 1 )
          checkword = checkword.strip()

          statement = "select count(*) from index_medieval_documents where document_code = '%s'" \
                    % checkword
          #outfile_handle.write( "/* %s */ \n" % statement )
          the_cursor.execute( statement )
          docrow = the_cursor.fetchone()
          found = docrow[ 0 ]
          if found > 0: #{ # it is a real document code, just missing sequence no
            is_valid_document_code = True
          #}
        #}
      #}

      if is_copy_code( word ) or is_valid_document_code: #{
        copy_code = word.strip()
        if copy_code.endswith( comma ): 
          copy_code = copy_code[ 0 : -1 ]
      #}

      if copy_code: #{
        # Check that we haven't already got it
        already_in_list = False
        if copy_code in copy_codes: already_in_list = True
        if already_in_list: continue

        copy_codes.append( copy_code )
        copy_count += 1
      #}
    #}

    # Finished picking out the copy codes from the 'copies' field.
    # Now get the text in between the copy codes
    copy_count = 0
    num_copies = len( copy_codes )
    while copy_count < num_copies: #{
      copy_code = copy_codes[ copy_count ]
      copy_count += 1
      copy_notes = ''

      rest_of_line = full_copies.split( copy_code, 1 )[ 1 ]

      if copy_count < len( copy_codes ): #{ # still another copy code to come after this one
        next_copy_code = copy_codes[ copy_count ]

        copy_notes = rest_of_line.split( next_copy_code, 1 )[ 0 ]

        copy_notes = copy_notes.strip()
        last_char = ''
        if copy_notes: last_char = copy_notes[ -1 : ]
        if next_copy_code and last_char in copy_code_connectors: #{
          copy_notes = '%s %s' % (copy_notes, next_copy_code)
        #}
      #}
      else:
        copy_notes = rest_of_line

      copy_notes = copy_notes.strip()

      if copy_notes == comma or copy_notes == full_stop: #{
        copy_notes = ''
      #}
      elif copy_notes.endswith( comma ): #{
        copy_notes = copy_notes[ 0 : -1 ]
      #}

      document_code = get_document_code( copy_code )
      seqno_in_document = get_seqno_in_document( copy_code )
      if not seqno_in_document.strip(): seqno_in_document = 'null'
      copy_notes = copy_notes.strip()

      statement = get_copy_insert_statement( entry_id, entry_book_count, copy_count, copy_code, \
                                             document_code, seqno_in_document, copy_notes )
      outfile_handle.write( statement.encode( 'utf-8' ))

      if is_numeric_range( copy_code ): #{ # need to generate sequence numbers for rest of range
        rest_of_range = get_rest_of_numeric_range( copy_code )

        for int_seqno in rest_of_range: #{
          copy_count += 1
          num_copies += 1
          copy_codes.insert( 0, copy_code ) # add to start so we don't keep coming to the same one again!

          seqno_in_document = str( int_seqno )

          outfile_handle.write( '/* generating sequence no. %d for %s */' % (int_seqno, copy_code))

          statement = get_copy_insert_statement( entry_id, entry_book_count, copy_count, copy_code, \
                                                 document_code, seqno_in_document, copy_notes )
          outfile_handle.write( statement.encode( 'utf-8' ))
        #}
      #}
    #}
    print newline
  #}

  the_cursor.close()
  the_database_connection.close()
#}


##=====================================================================================

if __name__ == '__main__':


  # These two lines are hacks (copied from Mat's clever hack, thanks Mat). 
  # They switch the default encoding to utf8 so that the command line will convert UTF8 + Ascii to UTF8
  reload(sys)
  sys.setdefaultencoding("utf8")

  parseCopies()

##=====================================================================================
