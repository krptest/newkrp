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
tei_template="""
<?xml version="1.0" encoding="UTF-8"?>
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
            <p></p>
         </sourceDesc>
      </fileDesc>
  </teiHeader>
  <text xml:lang="{lang}">
      {front}<body>
      {body}
      </body>{back}
  </text>
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
    for l in lines:
        if l.startswith("#+"):
            p = get_property(l)
            lx[p[0]] = p[1]
            continue
        elif l.startswith("#"):
            continue
        elif "<pb:" in l:
            l=re.sub("<pb:([^_]+)_([^_]+)_([^>]+)>", "<pb ed='\\2' n='\\3' xml:id='\\1-\\2-\\3'/>", l)
#            l=re.sub("<pb:([^_]+)_([^_]+)_([^>]+)>", "</div></div><div type='p' n='\\3'><div type='l' n='x'>", l)
            lcnt = 0
        if "<md:" in l:
            l=re.sub("<md:([^_]+)_([^_]+)_([^>]+)>", "<!-- md: \\1-\\2-\\3-->", l)
        lcnt += 1
        if md:
            pass
            #l=re.sub("¶", f"<!-- ¶ -->", l)
        else:
            l=re.sub("¶", f"\n<lb n='{lcnt}'/>", l)
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
    
def convert_text(txtid, user='kanripo'):
    gh=Github(at)
    hs=gh.get_repo(f"{user}/{txtid}")
    #get the branches
    branches=[a.name for a in hs.get_branches() if not a.name.startswith("_")]
    res=[]
    for branch in branches:
        flist = [a.path for a in hs.get_contents("/", ref=branch)]
        pdic = {}
        md = False
        for path in flist:
            if path.startswith(txtid):
                r=requests.get(f"https://raw.githubusercontent.com/{user}/{txtid}/{branch}/{path}")
                if r.status_code == 200:
                    cont=r.content.decode(r.encoding)
                    if "<md:" in cont:
                        md = True
                    lines=cont.split("\n")
                    lx = parse_text(lines, md)
                else:
                    return "No valid content found."
                pdic[path] = lx
            
        date=datetime.datetime.now()
        today=f"{date:%Y-%m-%d}"
        front=""
        back=""
        body=""
        jcnt = 0
        for b in pdic:
            jcnt += 1
            s=f"<div type='j' n='{jcnt}'>\n"
            if "LASTPB" in pdic[b]:
                lp=pdic[b]['LASTPB']
                pb=lp[4:-1].split("_")[-1]
            else:
                pb="0"
            s+= f"<div type='p' n='{pb}'>"
            pcnt = 0
            lcnt = 0
            for lx in pdic[b]['TEXT']:
                pcnt += 1
                # this is for the paragraph, but for the time being, we will ignore the paragraphs
                #s+=f"<div type='p' n='{pcnt}'>"
                s+="\n<!-- new para -->\n" 
                # lcnt = 0
                for l in lx:
                    lcnt +=1
                    l=re.sub("<lb[^>]+>", "", l)
                    s+=f"<div type='l' n='{lcnt}'>{l}</div>"
                    if "type='p'" in l:
                        lcnt = 0
                #s+="</div>"
            s+="</div>"
            s+="</div>"
            body += s
        lx=pdic[b]
        fname = f"{txtid}.{lang}.{branch}.2019.xml"
        out=tei_template.format(body=body, front=front, back=back, today=today, user=user, txtid=txtid, title=lx['TITLE'], date=lx['DATE'], branch=branch, lang=lang)
        of=open(fname, "w")
        of.write(out)
        of.close()

if __name__ == '__main__':

    txtid="KR3a0007"
    convert_text(txtid)
