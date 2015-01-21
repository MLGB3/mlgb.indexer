# -*- coding: utf-8 -*-
"""
Output the MLGB3 database in as close a style to the original Ker book as possible.
By Sushila Burgess
"""
##=====================================================================================

import sys
sys.path.append( '/home/mlgb/sites/mlgb/parts/index' )
import os
import MySQLdb

import connectToMLGB as c

filename_without_path = 'mlgb3.html'
final_output_dir = '/home/mlgb/sites/mlgb/static/media/pdf/'
work_dir = '/home/mlgb/sites/mlgb/parts/jobs/'

##=====================================================================================

tab = '\t'
newline = '\n'
carriage_return = '\r'
space = ' '

linebreak = '<br />'

blank_paragraph = '<p>&nbsp;</p>'
two_spaces = '&nbsp;&nbsp;'

##=====================================================================================

def writeStaticHTML(): #{

  try:
    output_filename = work_dir + filename_without_path

    outfile_handle = file
    outfile_handle = open( output_filename, 'wb' ) # 'wb' allows entry of UTF-8

    html = startHTML() # write <html><head><body> tags

    html += '<h2>List of surviving books</h2>' + newline
    html += get_list_of_surviving_books()

    html += '<h2>Index by modern location</h2>' + newline
    html += get_index_by_modern_location()

    html += '</body>' + newline
    html += '</html>' + newline

    outfile_handle.write( html.decode('iso-8859-1').encode('utf8') )

    outfile_handle.close()

    os.rename( output_filename, final_output_dir + filename_without_path )

  except:
    if isinstance( outfile_handle, file ):
      if not outfile_handle.closed : outfile_handle.close()
    raise
#}

##=====================================================================================

# Get static HTML for later conversion into PDF on command line

def get_list_of_surviving_books(): #{

  html = "<ul><!-- start list of provenances -->" + newline + newline

  # Connect to the database and create a cursor
  the_database_connection = c.get_database_connection()
  the_cursor = the_database_connection.cursor() 

  statement = "select provenance, county, institution, cells, notes, id "
  statement += " from books_provenance "
  statement += " order by lower( replace( provenance, 'St ', 'Saint ' ) )"
  the_cursor.execute( statement )
  prov_results = the_cursor.fetchall()

  for prov in prov_results: #{
    html += linebreak + '<li><!-- start provenance -->' + newline

    provenance  = prov[ 0 ].strip().upper()
    county      = prov[ 1 ].strip()
    institution = prov[ 2 ].strip()
    cells       = prov[ 3 ].strip()
    notes       = prov[ 4 ].strip()
    prov_id     = prov[ 5 ]

    cells = cells.replace( blank_paragraph, '' ).strip()
    notes = notes.replace( blank_paragraph, '' ).strip()
     
    html += provenance

    if county: #{
      if not html.endswith( ',' ): html += ','
      html += ' ' + county
    #}

    if institution: #{
      if not html.endswith( ',' ): html += ','
      html += ' <i>' + institution + '</i>'
    #}

    html += newline

    if notes or cells: #{
      html += '<div><small>' + newline
      if notes: html += notes + newline
      if cells: html += cells + newline
      html += '</small></div>' + newline
    #}

    statement = "select distinct ml1.modern_location_1, ml1.id "
    statement += " from books_book b, books_modern_location_1 ml1 "
    statement += " where b.modern_location_1_id = ml1.id and b.provenance_id = %d " % prov_id
    statement += " order by lower( replace(modern_location_1, 'St ', 'Saint ') )"
    the_cursor.execute( statement )
    modern_city_results = the_cursor.fetchall()
    if len( modern_city_results ) > 0: #{
      html += '<ul><!-- start list of modern locations -->' + newline
      for modern_city in modern_city_results: #{
        modern_city_name = modern_city[ 0 ]
        modern_city_id   = modern_city[ 1 ]
        html += '<li><!-- start modern location 1 (city) -->' + newline
        html += modern_city_name

        statement = "select ml2.modern_location_2, b.shelfmark_1, b.shelfmark_2, b.evidence_id, "
        statement += " b.author_title, b.date, b.pressmark, b.medieval_catalogue, b.unknown "
        statement += " from books_book b, books_modern_location_2 ml2 "
        statement += " where b.modern_location_2_id = ml2.id " 
        statement += " and b.provenance_id = %d " % prov_id
        statement += " and b.modern_location_1_id = %d" % modern_city_id
        statement += " order by lower( replace( modern_location_2, 'St ', 'Saint ' ) ),"
        statement += " shelfmark_sort, b.id"
        the_cursor.execute( statement )
        modern_library_results = the_cursor.fetchall()
        if len( modern_library_results ) > 0: #{
          html += newline + '<ul><!-- start list of books and their modern libraries -->' + newline

          for book in modern_library_results: #{
            modern_library     = book[ 0 ].strip()
            shelfmark_1        = book[ 1 ].strip()
            shelfmark_2        = book[ 2 ].strip()
            evidence_code      = book[ 3 ].strip()
            author_title       = book[ 4 ].strip()
            date               = book[ 5 ].strip()
            pressmark          = book[ 6 ].strip()
            medieval_catalogue = book[ 7 ].strip()
            unknown            = book[ 8 ].strip()
          #}

          shelfmark = "%s %s" % (shelfmark_1, shelfmark_2)
          shelfmark = shelfmark.strip()
          if shelfmark and not shelfmark.endswith( '.' ): shelfmark += '.'
 
          if evidence_code: evidence_code = '<i>%s</i>' % evidence_code

          if date and not date.endswith( '.' ): date += '.'

          pressmark = pressmark.replace( '<p>', '' )
          pressmark = pressmark.replace( '</p>', '' )
          pressmark = pressmark.strip()
          if pressmark and not pressmark.endswith( '.' ): pressmark += '.'

          if medieval_catalogue: medieval_catalogue = "[%s]" % medieval_catalogue

          if unknown and not unknown.endswith( '.' ) and not unknown.endswith( '?' ): unknown += '.'

          html += '<li><!-- start one book -->' + newline
          html += '<b>%s</b>%s' % (modern_library, two_spaces)

          html += "%s " % shelfmark
          html += "%s"  % evidence_code
          html += "%s " % author_title
          html += "%s " % date
          html += "%s " % pressmark
          html += "%s " % medieval_catalogue
          html += "%s " % unknown

          html += newline
          html += '</li><!-- end one book -->' + newline

          html += '</ul><!-- end list of books and their modern libraries -->' + newline
        #}
        html += '</li><!-- end modern location 1 (city) -->' + newline
      #}
      html += '</ul><!-- end list of modern locations -->' + newline
    #}

    html += '</li><!-- end provenance -->' + newline + newline
  #}

  html += newline + "</ul><!-- end list of provenances -->" + newline

  # Close your cursor and your connection
  the_cursor.close()
  the_database_connection.close()

  return html
#}
##=====================================================================================

def get_index_by_modern_location(): #{

  html = newline + "<ul><!-- start list of modern locations -->" + newline

  # Connect to the database and create a cursor
  the_database_connection = c.get_database_connection()
  the_cursor = the_database_connection.cursor() 

  statement = "select p.provenance, ml1.modern_location_1, ml2.modern_location_2, "
  statement += " b.shelfmark_1, b.shelfmark_2, p.institution "
  statement += " from books_provenance p, "
  statement += " books_modern_location_1 ml1, "
  statement += " books_modern_location_2 ml2, "
  statement += " books_book b  "
  statement += " where b.provenance_id = p.id "
  statement += " and b.modern_location_1_id = ml1.id "
  statement += " and b.modern_location_2_id = ml2.id "
  statement += " order by lower( replace( modern_location_1, 'St ', 'Saint ' ) ), " 
  statement += " lower( replace( modern_location_2, 'St ', 'Saint ' ) ), " 
  statement += " b.shelfmark_sort, b.id" 
  the_cursor.execute( statement )
  loc_results = the_cursor.fetchall()

  prev_location = ''
  prev_shelfmark1 = ''

  for loc in loc_results: #{
    provenance = loc[ 0 ].strip()
    location1  = loc[ 1 ].strip()
    location2  = loc[ 2 ].strip()
    shelfmark1 = loc[ 3 ].strip()
    shelfmark2 = loc[ 4 ].strip()
    inst       = loc[ 5 ].strip()

    location = location1
    if location2 and not location1.endswith( ',' ): location += ', '
    location += location2
    
    if location != prev_location: #{
      if prev_location: html += '</table></li><!-- end modern location -->' + newline
      prev_location = location
      prev_shelfmark1 = ''
      html += '<li><!-- start modern location -->' + newline
      html += '<h3>' + location + '</h3>' + newline
      html += '<table>' + newline
    #}

    html += '<tr>' + newline

    html += '<td>' 
    #if shelfmark1 != prev_shelfmark1: html += shelfmark1
    #html += '</td>' + newline

    #html += '<td>' 
    #html += shelfmark2
    html += "%s %s" % (shelfmark1, shelfmark2)
    html += '</td>' + newline

    html += '<td>' 
    html += '<i>see</i> %s, <i>%s</i>' % (provenance.upper(), inst)
    html += '</td>' + newline

    html += '</tr>' + newline

    prev_shelfmark1 = shelfmark1
  #}

  html += '</table></li><!-- end modern location -->' + newline
  html += newline + "</ul><!-- end list of modern locations -->" + newline

  # Close your cursor and your connection
  the_cursor.close()
  the_database_connection.close()

  return html
#}
##=====================================================================================

def startHTML(): #{
  html = '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" '
  html += ' "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">' + newline
  html += '<html xmlns="http://www.w3.org/1999/xhtml">' + newline
  html += '<head>' + newline
  html += '<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />' + newline
  html += '<title>Medieval Libraries of Great Britain III</title>' + newline

  html += '<style type="text/css">' + newline

  html += 'body { ' + newline
  html += '  margin: 0 0 0 0;' + newline
  html += '  padding-left: 12px;' + newline
  html += '  padding-right: 12px;' + newline
  html += '  background: #FFFFFF;' + newline
  html += '  font: normal medium "Trebuchet MS", Arial, Helvetica, sans-serif;' + newline
  html += '  color: #666666;' + newline
  html += '  font-size: 18px;' + newline # maybe too big? (default is 16px;)
                                         # but it had been looking very spidery
  html += '} ' + newline

  html += 'ul { ' + newline
  html += '  list-style: none;' + newline
  html += '} ' + newline

  html += 'table {' + newline
  html += '  margin-left: 25px;' + newline
  html += '} ' + newline

  html += 'td {' + newline
  html += '  vertical-align: top;' + newline
  html += '  padding-right: 10px;' + newline
  html += '} ' + newline

  html += '</style>' + newline

  html += '</head>' + newline
  html += '<body>' + newline

  html += '<h1>Medieval Libraries of Great Britain III</h1>' + newline
  return html
#}
##=====================================================================================

if __name__ == '__main__':


  # These two lines are hacks (copied from Mat's clever hack, thanks Mat). 
  # They switch the default encoding to utf8 so that the command line will convert UTF8 + Ascii to UTF8
  reload(sys)
  sys.setdefaultencoding("utf8")

  writeStaticHTML()

##=====================================================================================
