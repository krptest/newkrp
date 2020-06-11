# Convert Kanripo format to Philologic4 TEI

# import libraries
import re  #=RegEx
import sys
import os


# *** Begin Read filename from command line & verify section ***
def usage():
  sys.exit('Usage: python ' + sys.argv[0] + ' [filename]')

# check command line    
if len(sys.argv) < 2:
  print('Error: No source file specified. TEI headers should be in [filename]_TEI-header.txt .')
  usage()
elif len(sys.argv) > 2:
  print('Error: ' + str(len(sys.argv)) + ' args provided')
  usage()

# get filenamefrom command line (arg 1)
fileName = sys.argv[1]

# check file exists
if os.path.isfile(fileName) is False:
  print('File not found: ' + fileName)
  usage()
# *** End filename from command line & verify section ***


# *** Begin Main Conversion Routine ***
#
#

# Verbose mode (1 = on, 0 = off)
verbosemode = 0

sourcefilename = fileName #"KR2a0001_fulltext.txt" #"KR2a0001_001.txt" #"KR2a0001_109.txt"

outfilename = sourcefilename[:(len(sourcefilename)-4)] + "_tei.txt"

# Create the outfile, truncate old file to 0 if exists
outfile = open(outfilename, "w+")

# Check for header file, write to outfile if exists
headerfilename = sourcefilename[:(len(sourcefilename)-4)] + "_TEI-header.txt"
if os.path.isfile(headerfilename) is True:
  headerfile = open(headerfilename, "r")
  for hline in headerfile:
    outfile.write(hline)
  headerfile.close()

# Write text headers to outfile
outfile.write("\n<text>\n<body>\n")

# Set flags and counters
titleflag = 1
titlestring = '#+TITLE: '
setheader = 1
linecounter = 1
notecounter = 1
firstsection = 1
sectionfirstnote = 0
notesectionbegin = 1
zanflag = 0

# Create empty list to hold Notes data (written to file @ end)
notesdata = []

# Main File Loop
with open(sourcefilename) as sourcefile:
  for line in sourcefile:

    # Remove end-of-line chars now
    line = line.replace("\n","")

    # Reset teiline each line
    teiline = ""

    # Set the header tags, and close <div1> if open
    # Turn off the zanflag at the beginning of each part of the source file
    if (line[:1] == "#"):
      if (zanflag == 1):
        outfile.write("\n</div1>\n")
        zanflag = 0
      titleflag = 1
      firstsection = 1
      # If this is the first source text, set the <head> tag to the TITLE -- this is incorrect (see section w/ <div1> tag below)
      if (setheader == 1):
        if titlestring in line:
          teiline = line.replace(titlestring, '')
          # outfile.write("<head>" + teiline + "</head>\n")
          setheader = 0

    # Check for "#" or "<pb:" at beginning of line (=header, to be ignored)
    if ((not line[:1] == "#") and (not line[:3] == "<pb")):

      # Check to see if line is blank
      if (line and (not line.isspace())):

        # Go content!
        # if (verbosemode == 1):
        # print ("line " + str(linecounter) + " is not blank, is [" + line + "]")

        # Go parse & do string replaces
        if (not line[:2].isspace()):

          # Check for brackets
          if (line[:1] == "〔"):

            # This is a note -- use sectionfirstnote to find start # for these notes
            if (verbosemode == 1):
              print ("line " + str(linecounter) + " is part of a footnote, = [" + line + "]")

            if (notesectionbegin == 1):
              notecounter2 = sectionfirstnote
              closenote = ""
              notesectionbegin = 0
            else:
              notecounter2 = notecounter2 + 1
#              closenote = "</note>\n"

            if (firstnote == 1):
#              noteline1 = '</div>\n<div type="notes">\n<note id="note'
              noteline1 = '</note>\n<note id="note'
              firstnote = 0
            else:
              noteline1 = '</note>\n<note id="note'

#            teiline = closenote + noteline1 + str(notecounter2) + '">' + line
            teiline = ""
            notesdata.append(noteline1 + str(notecounter2) + '">' + line)

          elif (line[:1] == "【"):

            # this is the 贊, how should it be marked?
            if (verbosemode == 1):
              print ("line " + str(linecounter) + " is the 贊, = [" + line + "]")

            zanflag = 1
#            teiline = line
            teiline = '<ref type="note" target="note' + str(notecounter) + '" n="贊"/>'
            zanline = '</note>\n<note id="note' + str(notecounter) + '">' + line
            notecounter += 1
            notesdata.append(zanline)

          else:

            # This is a real line

            # if (verbosemode == 1):
            #   print ("line " + str(linecounter) + " is a real line, = [" + line + "]")

            if (titleflag == 1):
              # This is a title
              if (verbosemode == 1):
                print ("line " + str(linecounter) + " is a title, = [" + line + "]")

              #teiline = "<div1>" + line
              teiline = "<div1><head>" + line + "</head>"
              titleflag = 0

            elif (zanflag == 1):
              notesdata.append(line)

            else:

              if (verbosemode == 1):
                print ("line " + str(linecounter) + " is head text, = [" + line + "]")

              # This line is head text, continued
              notesectionbegin = 1

              # Do inline note parsing here

              # Check to see if there are any "〔" note brackets
              numofbrackets = line.count("〔")

              # If there are this indicates there is no 序 in this text, set firstsection = 0
              if (numofbrackets > 0):
                firstsection = 0

              # if (verbosemode == 1):
                # print ("numofbrackets is " + str(numofbrackets))

              if (numofbrackets > 0):
                # note bracket found, walk through string and do replaces
                bracketindex = []
                boffset = 0
                bbi = 0
#                replacetext = '<ref type="note" id="note' + str(notecounter) + '" n="1">'
                replacetext = '<ref type="note" target="note' + str(notecounter) + '" n="'

                # get the indices for '〔'
                for charno in range(len(line)):
                  if (line[charno] == '〔'):
                    bracketindex.append(charno)

                for bi in bracketindex:
                  bbi = bi + boffset
                  # print("replace char " + str(bbi) + ": original = [" + line + "]")
                  line = line[:bbi] + replacetext + line[bbi:]
                  # print("replace char " + str(bbi) + ": changed to = [" + line + "]")
                  boffset = boffset + len(replacetext)
                  notecounter += 1
#                  replacetext = '<ref type="note" id="note' + str(notecounter) + '" n="1">'
                  replacetext = '<ref type="note" target="note' + str(notecounter) + '" n="'

                line = line.replace('〕', '〕"/>')

              teiline = line

        # check how many blanks
        elif (line[:4].isspace()):
          # this is an indented line in the notes
          if (verbosemode == 1):
            print ("line " + str(linecounter) + " is an indented line of notes, = [" + line + "]")

          if (firstsection == 1):
#            setnote = '\n<div type="notes">\n<note id="note1">'
#            teiline = setnote + line
            teiline = '<ref type="note" target="note' + str(notecounter) + '" n="序"/>'
            notesdata.append(line)
            notecounter += 1
            firstsection = 0
          else:
#            teiline = line
            teiline = ""
            notesdata.append(line)

        else:
          # this is the beginning of the section
          if (verbosemode == 1):
            print ("line " + str(linecounter) + " : section begin, = [" + line + "]")

          sectionfirstnote = notecounter
          firstnote = 1

          # Check to see if there are any "〔" note brackets in the line
          # If there are this indicates there is no 序 in this text, set firstsection = 0
          # numofbrackets is also used to drive the loop below
          numofbrackets = line.count("〔")
          if (numofbrackets > 0):
            firstsection = 0

#          if (notecounter == 1):
#            closenote = ""
#          else:
#            closenote = "</note>"

          if (firstsection == 1):
            if (firstnote == 1):
#              divstart = "\n<div>"
              divstart = "\n<p>"
            else:
#              divstart = "<\div>\n<div>"
              divstart = "</p>\n<p>"
          else:
#            divstart = "</div>\n<div>"
            divstart = "</p>\n<p>"

          # if (verbosemode == 1):
            # print ("numofbrackets is " + str(numofbrackets))

          if (numofbrackets > 0):
            # note bracket found, walk through string and do replaces
            bracketindex = []
            boffset = 0
            bbi = 0
            replacetext = '<ref type="note" target="note' + str(notecounter) + '" n="'

            # get the indices for '〔'
            for charno in range(len(line)):
              if (line[charno] == '〔'):
                bracketindex.append(charno)

            for bi in bracketindex:
              bbi = bi + boffset
              # print("replace char " + str(bbi) + ": original = [" + line + "]")
              line = line[:bbi] + replacetext + line[bbi:]
              # print("replace char " + str(bbi) + ": changed to = [" + line + "]")
              boffset = boffset + len(replacetext)
              notecounter += 1
              replacetext = '<ref type="note" target="note' + str(notecounter) + '" n="'

            line = line.replace('〕', '〕"/>')

#          teiline = closenote + divstart + line
          teiline = divstart + line

        # elseif


        # kill extraneous chars (pilcrows, spaces and line endings)
        teiline = teiline.replace("¶", "")
        # teiline = teiline.replace("〕　", "〕")
        teiline = teiline.replace("　", "")

        # Write line to outfile
        outfile.write(teiline)

        linecounter += 1

outfile.write("</p>\n</div1>\n")

# Write notesdata list to file
outfile.write('<div1 type="notes">\n<note id="note1">')
for nd in notesdata:
  nd = nd.replace("¶", "")
  nd = nd.replace("　", "")
  outfile.write(nd)
outfile.write("</note>\n</div1>\n")

outfile.write("</body>\n</text>")
outfile.close

# *** End Main Conversion Routine ***
