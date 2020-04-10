# -*- coding: utf-8 -*-
# KR to TEI format.
#
import re, os, sys, requests, datetime
from github import Github
from dotenv import load_dotenv
load_dotenv()

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
<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="{txtid}">
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
  <sourceDoc>
      {sd}
  </sourceDoc>
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
def parse_text(lines, md=False):
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
        l = re.sub("&([^;]+);", "<g ref='#\\1'/>", l)
        if md:
            pass
            #l=re.sub("¶", f"<!-- ¶ -->", l)
        else:
            if not re.match("^</surface>", l) and len(l) > 0:
                l="<line xml:id='%s.%2.2d'>%s</line>\n" % (pbxmlid, lcnt,l)
            #l=re.sub("¶", f"\n<lb n='{lcnt}'/>", l)
        # if l == "":
        #     np.append(nl)
        #     nl=[]
        # else:
        if md:
            l=l+"\n"
        nl.append(l)
    np.append(nl)    
    lx['TEXT'] = np
    return lx

def save_text_part(lx, txtid, branch, path):
    try:
        os.makedirs(txtid + "/xml/" + branch)
    except:
        pass
    fname = "%s/xml/%s/%s.xml" % (txtid, branch, path[:-4])
    of=open(fname, "w")
    of.write("<surfaceGrp xmlns='http://www.tei-c.org/ns/1.0' xml:id='%s'>\n<surface type='dummy'>" % (path[:-4]))
    for page in lx["TEXT"]:
        for line in page:
            of.write(line)
    of.write("</surface>\n</surfaceGrp>\n")

def convert_text(txtid, user='kanripo'):
    gh=Github(at)
    hs=gh.get_repo(f"{user}/{txtid}")
    #get the branches
    branches=[a.name for a in hs.get_branches() if not a.name.startswith("_")]
    res=[]
    for branch in branches:
        try:
            os.mkdirs(txtid+ "/xml/" + branch)
        except:
            pass
        flist = [a.path for a in hs.get_contents("/", ref=branch)]
        pdic = {}
        md = False
        xi=[]
        for path in flist:
            if path.startswith(txtid):
                r=requests.get(f"https://raw.githubusercontent.com/{user}/{txtid}/{branch}/{path}")
                if r.status_code == 200:
                    cont=r.content.decode(r.encoding)
                    if "<md:" in cont:
                        md = True
                    lines=cont.split("\n")
                    lx = parse_text(lines, md)
                    save_text_part(lx, txtid, branch, path)
                else:
                    return "No valid content found."
                pdic[path] = lx
        
        date=datetime.datetime.now()
        today=f"{date:%Y-%m-%d}"
        sd=""
        for f in pdic.keys():
            fn = f[:-4]
            #b=pdic[f]
            sd+=f"<xi:include href='{fn}.xml' xmlns:xi='http://www.w3.org/2001/XInclude'/>\n"
        lx=pdic[f]
        fname = f"{txtid}/xml/{branch}/{txtid}.xml"
        out=tei_template.format(sd=sd, today=today, user=user, txtid=txtid, title=lx['TITLE'], date=lx['DATE'], branch=branch)
        of=open(fname, "w")
        of.write(out)
        of.close()

if __name__ == '__main__':

    txtid="KR3a0007"
    try:
        os.mkdirs(txtid+"/xml")
    except:
        pass
    convert_text(txtid)
