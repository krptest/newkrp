# -*- coding: utf-8 -*-
# Hist to TEI format.
#
import re, os, sys, requests, datetime
from github import Github
from dotenv import load_dotenv
load_dotenv()

puamagic = 1069056
if os.path.exists('../../.env'):
    print('Importing environment from .env...')
    for line in open('.env'):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]

at=os.environ.get('at')
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

def get_property(p_in):
    p = p_in[2:]
    pp = p.split(": ")
    if pp[0] in ["DATE", "TITLE"]:
        return (pp[0], pp[1])
    elif pp[0] == "PROPERTY":
        p1 = pp[1].split()
        return (p1[0], " ".join(p1[1:]))
    return "Bad property: %s" % (p_in)

# loop through the lines and return a dictionary of metadata and text content
# gjd is the dictionary to hold gaiji encountered, md is wether we want to care about <md: style tags.
# here we parse the text into paragraphs, instead of surface elements
def parse_text_to_p(lines, gjd, md=False):
    lx={'TEXT' : []}
    lcnt=0
    nl=[]
    np=[]
    pbxmlid=""
    for l in lines:
        l=re.sub("¶", "<lb/>", l)
        lcnt += 1
        if l.startswith("#+"):
            p = get_property(l)
            lx[p[0]] = p[1]
            continue
        elif l.startswith("#"):
            continue
        elif "<pb:" in l:
            pbxmlid=re.sub("<pb:([^_]+)_([^_]+)_([^>]+)>", "\\1_\\2_\\3", l)
            l=re.sub("<pb:([^_]+)_([^_]+)_([^>]+)>", "<pb ed='\\2' n='\\3' xml:id='\\1_\\2_\\3'/>", l)
            lcnt = 0
        if "<md:" in l:
            l=re.sub("<md:([^_]+)_([^_]+)_([^>]+)>", "", l)
        if "&KR" in l:
            # only for the sideeffect
            re.sub("&KR([^;]+);", lambda x : gjd.update({"KR%s" % (x.group(1)) : "%c" % (int(x.group(1)) + puamagic)}), l)
        l = re.sub("&KR([^;]+);", lambda x : "%c" % (int(x.group(1)) + puamagic ), l)
        # if md:
        #     pass
        #     #l=re.sub("¶", f"<!-- ¶ -->", l)
        # else:
        l = l.replace("(", "<note>")
        l = l.replace(")", "</note>")
        if not re.match("^</p>", l) and len(l) > 0:
            l="%s\n" % (l)
        if l == "":
            np.append(nl)
            nl=[]
        else:
            if md:
                l=l+"\n"
        nl.append(l)
    np.append(nl)
    lx['TEXT'] = np
    return lx

# loop through the lines and return a dictionary of metadata and text content
# gjd is the dictionary to hold gaiji encountered, md is wether we want to care about <md: style tags.
# 
def parse_text(lines, gjd, md=False):
    lx={'TEXT' : []}
    lcnt=0
    nl=[]
    np=[]
    pbxmlid=""
    for l in lines:
        l=re.sub("¶", "", l)
        lcnt += 1
        if l.startswith("#+"):
            p = get_property(l)
            lx[p[0]] = p[1]
            continue
        elif l.startswith("#"):
            continue
        elif "<pb:" in l:            
            np.append(nl)
            nl=[]
            pbxmlid=re.sub("<pb:([^_]+)_([^_]+)_([^>]+)>", "\\1_\\2_\\3", l)
            l=re.sub("<pb:([^_]+)_([^_]+)_([^>]+)>", "</surface>\n<surface xml:id='\\1_\\2_\\3-z'>\n<pb ed='\\2' n='\\3' xml:id='\\1_\\2_\\3'/>", l)
#            l=re.sub("<pb:([^_]+)_([^_]+)_([^>]+)>", "</div></div><div type='p' n='\\3'><div type='l' n='x'>", l)
            lcnt = 0
        if "<md:" in l:
            l=re.sub("<md:([^_]+)_([^_]+)_([^>]+)>", "<!-- md: \\1-\\2-\\3-->", l)
        #l = re.sub("&([^;]+);", "<g ref='#\\1'/>", l)
        if "&KR" in l:
            # only for the sideeffect
            re.sub("&KR([^;]+);", lambda x : gjd.update({"KR%s" % (x.group(1)) : "%c" % (int(x.group(1)) + puamagic)}), l)
        l = re.sub("&KR([^;]+);", lambda x : "%c" % (int(x.group(1)) + puamagic ), l)
        # if md:
        #     pass
        #     #l=re.sub("¶", f"<!-- ¶ -->", l)
        # else:
        l = l.replace("(", "<note>")
        l = l.replace(")", "</note>")
        if not re.match("^</surface>", l) and len(l) > 0:
            l="<line xml:id='%s.%2.2d'>%s</line>\n" % (pbxmlid, lcnt,l)
            #l=re.sub("¶", f"\n<lb n='{lcnt}'/>", l)
        # if l == "":
        #     np.append(nl)
        #     nl=[]
        # else:
        # if md:
        #     l=l+"\n"
        l = l.replace("KR", "KX")
        nl.append(l)
    np.append(nl)    
    lx['TEXT'] = np
    return lx

def save_text_part(lx, txtid, branch, path):
    path = path.replace("KR", "KX")
    if re.match("^[A-Z-]+$", branch):
        bt = "/doc/"
    else:
        bt = "/int/"
    try:
        os.makedirs(txtid + bt + branch)
    except:
        pass
    fname = "%s%s%s/%s.xml" % (txtid, bt, branch, path[:-4])
    of=open(fname, "w")
    localid=path[:-4].split("_")
    localid.insert(1, branch)
    #localid = localid.replace("KR", "KX")
    if bt == "/int/":
        of.write("<div xmlns='http://www.tei-c.org/ns/1.0'><p xml:id='%s'>" % ("_".join(localid)))
    else:
        of.write("<surfaceGrp xmlns='http://www.tei-c.org/ns/1.0' xml:id='%s'>\n<surface type='dummy'>" % ("_".join(localid)))
    for page in lx["TEXT"]:
        for line in page:
            line = line.replace("KR", "KX")
            of.write(line)

    if bt == "/int/":
        of.write("</p></div>\n")
    else:
        of.write("</surface>\n</surfaceGrp>\n")

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
    
def convert_text(txtid, user='kanripo'):
    txin="/home/chris/Dropbox/hist25/%s" % (txtid)
    txtid = txtid.replace("KR", "KX")
    branches=['ZHSJ']
    res=[]
    for branch in branches:
        if re.match("^[A-Z-]+$", branch):
            bt = "/doc/"
        else:
            bt = "/int/"
        try:
            os.makedirs(txtid+ bt + branch)
        except:
            pass
        flist = [a for a in os.listdir(txin) if a.endswith(".txt")]
        flist.sort()
        pdic = {}
        md = False
        xi=[]
        gjd = {}
        for fn in flist:
            path="%s/%s" % (txin, fn)
            cont=open(path, "r").read()
            if "<md:" in cont:
                md = True
            lines=cont.split("\n")
            if bt == "/int/":
                lx = parse_text_to_p(lines, gjd, md)
            else:
                lx = parse_text(lines, gjd, md)
            save_text_part(lx, txtid, branch, fn)
            pdic[fn] = lx
        date=datetime.datetime.now()
        today=f"{date:%Y-%m-%d}"
        sd=""
        save_gjd (txtid, branch, gjd, "entity")
        save_gjd (txtid, branch, gjd, "g")
        for f in pdic.keys():
            fn = f[:-4]
            fn = fn.replace("KR", "KX")
            #b=pdic[f]
            sd+=f"<xi:include href='{fn}.xml' xmlns:xi='http://www.w3.org/2001/XInclude'/>\n"
        lx=pdic[f]
        lx['DATE'] = today
        fname = f"{txtid}{bt}{branch}/{txtid}.xml"
        if bt == "/int/":
            out=tei_template.format(sd="<text><body>\n%s</body></text>" % (sd), today=today, user=user, txtid=txtid, title=lx['TITLE'], date=lx['DATE'], branch=branch)
        else:
            out=tei_template.format(sd="<sourceDoc>\n%s</sourceDoc>" % (sd), today=today, user=user, txtid=txtid, title=lx['TITLE'], date=lx['DATE'], branch=branch)
        of=open(fname, "w")
        of.write(out)
        of.close()

if __name__ == '__main__':

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
    convert_text(txtid)
