# Convert Kanripo format to Philologic4 TEI

# import libraries
import re  #=RegEx
import sys
import os
import datetime

pb_re = re.compile("<pb:([^>]+)>")
puamagic = int(0x107000)

lang="zho"
# template for xml
# need the following vars:
# user, txtid, title, date, branch, today, body, lang
# body should contain the preformatted content for the body element
tei_template="""<?xml version="1.0" encoding="UTF-8"?>
<?xml-model href="http://www.tei-c.org/release/xml/tei/custom/schema/relaxng/tei_all.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>
<?xml-model href="http://www.tei-c.org/release/xml/tei/custom/schema/relaxng/tei_all.rng" type="application/xml"
	schematypens="http://purl.oclc.org/dsdl/schematron"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="{txtid}_{branch}">
  <teiHeader>
      <fileDesc>
         <titleStmt>
            <title>{title}</title>
         </titleStmt>
         <publicationStmt>
            <p>Published by @kanripo on GitHub.com</p>
         </publicationStmt>
         <sourceDesc>
            <p>{branch}</p>
         </sourceDesc>
      </fileDesc>
  </teiHeader>
      {sd}
</TEI>
"""

def save_gjd (txtid, branch, gjd, type="entity"):
    if (type=="entity"):
        fname = "%s/aux/map/%s_%s-entity-map.xml" % (txtid, txtid, branch)
    else:
        fname = "%s/aux/map/%s_%s-entity-g.xml" % (txtid, txtid, branch)
    of=open(fname, "w")
    of.write("""<?xml version="1.0" encoding="UTF-8"?>
<stylesheet xmlns="http://www.w3.org/1999/XSL/Transform" version="2.0">
<character-map  name="krx-map">\n""")
    k = [a for a in  gjd.keys()]
    k.sort()
    for kr in k:
        if (type=="entity"):
            of.write("""<output-character character="%s" string="&amp;%s;"/>\n""" % (gjd[kr], kr))
        else:
            of.write("""<output-character character="%s" string="&lt;g ref=&#34;%s&#34;/&gt;"/>\n""" % (gjd[kr], kr))
    of.write("""</character-map>\n</stylesheet>\n""")
    of.close()



# *** Begin Read filename from command line & verify section ***
def usage():
  sys.exit('Usage: python ' + sys.argv[0] + ' [filename]')


# *** Begin Main Conversion Routine ***
#
#
def conv(indirName, txtid, gjd):
  # Verbose mode (1 = on, 0 = off)
  verbosemode = 0
  sfiles = [a for a in os.listdir(indirName) if a.endswith(".txt")]
  sfiles.sort()
  ntxtid = txtid.replace("KR", "KX")
  bt= ntxtid + "/int/hist/"
  href=[]
  try:
    os.makedirs(bt)
  except:
    pass
  for sourcefilename in sfiles:
    outfilename = sourcefilename[:(len(sourcefilename)-4)] + ".xml"
    outfilename = outfilename.replace("KR", "KX")
    href.append(outfilename)
    # Create the outfile, truncate old file to 0 if exists
    outfile = open(bt+outfilename, "w+")
    lid=ntxtid + "_hist_" + outfilename[:-4].split("_")[-1]
    outfile.write("<div xmlns='http://www.tei-c.org/ns/1.0'  xml:id='%s'>\n" % (lid) )

    # Set flags and counters
    titleflag = 1
    titlestring = '#+TITLE: '
    setheader = 1
    linecounter = 1
    notecounter = 1
    firstsection = 1
    sectionfirstnote = 0
    headopenflag = 0
    notesectionbegin = 1
    zanflag = 0
    noteprefix = lid + "-note"
    # Create empty list to hold Notes data (written to file @ end)
    notesdata = []
    cpb=""
    pcnt=0

    # Main File Loop
    with open(indirName + "/" + sourcefilename) as sourcefile:
      for line in sourcefile:

        # Remove end-of-line chars now
        line = line.replace("\n","")

        if "&GJ" in line:
            # only for the sideeffect
            re.sub("&GJ([^;]+);", lambda x : gjd.update({"GJ%s" % (x.group(1)) : "%c" % (int(x.group(1),16) + puamagic)}), line)
        #elif re.match("&[^;]+;", line):
            # other gaiji, fttb just escape them...
            # line = re.sub("&([^;]+);", "[\1]", line)
        line = re.sub("&GJ([^;]+);", lambda x : "%c" % (int(x.group(1),16) + puamagic ), line)
        line = re.sub(r"&([^;]+);", "[\\1]", line)
        # Reset teiline each line
        teiline = ""
        # Set the header tags, and close <div1> if open
        # Turn off the zanflag at the beginning of each part of the source file
        if (line[:1] == "#"):
          if (zanflag == 1):
            outfile.write("\n</div>\n")
            zanflag = 0
          titleflag = 1
          firstsection = 1
          # If this is the first source text, set the <head> tag to the TITLE -- this is incorrect (see section w/ <div1> tag below)
          if (setheader == 1):
            if titlestring in line:
              teiline = line.replace(titlestring, '')
              title=teiline
              # outfile.write("<head>" + teiline + "</head>\n")
              setheader = 0

        # Check for "#" or "<pb:" at beginning of line (=header, to be ignored)
        if (pb_re.match(line)):
          npb=pb_re.findall(line)[0].split("_")
          nx=npb[-1].split("-")
          n=nx[1]
          last = "%3.3d-%s" % (int(nx[0]), n)
          npb[-1] = last
          npb[0] = ntxtid
          cpb="_".join(npb)
          pcnt += 1
          ## the following disturbs the note counting, disabling for the moment
          #line= pb_re.sub("<pb xml:id='%s' n='%s'/>" % (cpb, "-".join(nx)), line)
        if ((not line[:1] == "#") and (not line[:4] == "<pb:")):

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
                if (firstnote == 1):
                  noteline1 = '</note>\n<note xml:id="%s' % (noteprefix)
                  firstnote = 0
                else:
                  noteline1 = '</note>\n<note xml:id="%s' % (noteprefix)
                teiline = ""
                notesdata.append(noteline1 + str(notecounter2) + '">' + line)

              elif (line[:1] == "【"):

                # this is the 贊, how should it be marked?
                if (verbosemode == 1):
                  print ("line " + str(linecounter) + " is the 贊, = [" + line + "]")

                zanflag = 1
    #            teiline = line
                teiline = '<ref type="note" target="#' + noteprefix + str(notecounter) + '" n="贊"/>'
                zanline = '</note>\n<note xml:id="' + noteprefix + str(notecounter) + '">' + line
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
                  teiline = "<div><head>" + line
                  headopenflag = 1
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
                    replacetext = '<ref type="note" target="#' + noteprefix + str(notecounter) + '" n="'

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
                      replacetext = '<ref type="note" target="#' + noteprefix + str(notecounter) + '" n="'

                    line = line.replace('〕', '〕"/>')

                  teiline = line

            # check how many blanks
            elif (line[:4].isspace()):
              # this is an indented line in the notes
              if (verbosemode == 1):
                print ("line " + str(linecounter) + " is an indented line of notes, = [" + line + "]")

              if (firstsection == 1):
    #            setnote = '\n<div type="notes">\n<note xml:id="note1">'
    #            teiline = setnote + line
                #teiline = '<ref type="note" target="#' + noteprefix + str(notecounter) + '" n="序"/>'
                teiline = '<ref type="note" target="#' + noteprefix + '0" n="序"/>'
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
#&M-49301;
              pcnt += 1
              if (firstsection == 1):
                if (headopenflag == 1):
                  divstart = "</head>\n<p xml:id='%s-%d'>" % (cpb, pcnt)
                  headopenflag = 0
                else:
                  divstart = "</p>\n<p xml:id='%s-%d'>" % (cpb, pcnt)
              else:
                divstart = "</p>\n<p xml:id='%s-%d'>" % (cpb, pcnt)


              # if (verbosemode == 1):
                # print ("numofbrackets is " + str(numofbrackets))

              if (numofbrackets > 0):
                # note bracket found, walk through string and do replaces
                bracketindex = []
                boffset = 0
                bbi = 0
                replacetext = '<ref type="note" target="#'+ noteprefix  + str(notecounter) + '" n="'

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
                  replacetext = '<ref type="note" target="#'+ noteprefix  + str(notecounter) + '" n="'

                line = line.replace('〕', '〕"/>')

    #          teiline = closenote + divstart + line
              teiline = divstart + line

            # elseif


            # kill extraneous chars (pilcrows, spaces and line endings)
            teiline = teiline.replace("¶", "<lb/>")
            # teiline = teiline.replace("〕　", "〕")
            teiline = teiline.replace("　", "")

            # Write line to outfile
            outfile.write(teiline)

            linecounter += 1

    outfile.write("</p>\n</div>\n")

    # Write notesdata list to file
    outfile.write('<div type="notes">\n<note xml:id="%s0">' % (noteprefix))
    for nd in notesdata:
      nd = nd.replace("¶", "<lb/>")
      nd = nd.replace("　", "")
      outfile.write(nd)
    outfile.write("</note>\n</div>\n")

    outfile.write("</div>")
    outfile.close
  # *** End Main Conversion Routine ***
  href.sort()
  date=datetime.datetime.now()
  today=f"{date:%Y-%m-%d}"
  sd = ""
  for h in href:
    sd+=f"<xi:include href='{h}' xmlns:xi='http://www.w3.org/2001/XInclude'/>\n"
  outfilename = bt + ntxtid + ".xml"
  outfile = open(outfilename, "w+")
  out=tei_template.format(sd="<text><body>\n%s</body></text>" % (sd), today=today, txtid=ntxtid, title=title, date=today, branch='hist')
  outfile.write(out)
  outfile.close()

if __name__ == "__main__":

  try:
    txtid=sys.argv[1]
  except:
    print ("Textid should be given as argument.")
    sys.exit()
  ntxtid = txtid.replace("KR", "KX")
  try:
    os.makedirs(ntxtid+"/aux/map")
    os.makedirs(ntxtid+"/doc")
    os.makedirs(ntxtid+"/int")
  except:
    pass
  fileName="/home/chris/projects/hist25/" + txtid
  gjd = {}
  conv(fileName, txtid, gjd)
  save_gjd (ntxtid, 'hist', gjd, "entity")
  save_gjd (ntxtid, 'hist', gjd, "pua")
