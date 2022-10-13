#!/usr/bin/env python
# coding: utf-8

# # This NB is for developing a post processing tool for tei2py
# The tool will try to split the root text and the commentary in files where the commentary is indented by one space.
# 

# In[1]:


import sys, os, re
kanji = "[一-龯]"


# None = undefined, root = in root text, comm = in commentary
def proc_lines(ls, fid):
    ols=[]
    xid = fid.split("_")
    xid.insert(1, "tls")
    sf = "None"
    tag = ""
    stage = "None"
    pcnt = 0
    ccnt = 0
    for p, l in enumerate(ls):
        a = re.findall("^\s+", l)
        if len(a) > 0:
            if len(a[0]) == 1:
                stage = "comm"
            else:
                stage = "None"
        elif re.match(kanji, l[0]):
            s=re.match(kanji, l[0]).string
            if len(s) > 0:
                stage = "root"
            else:
                stage = "None"
        else:
            stage = "None"
        if (stage != sf):
            if stage == "comm":
                ccnt += 1
                tag = '</p><p xml:id="%s-c%3.3da" type="commentary">' % ("%s" % ("_".join(xid)), ccnt )
            elif stage == "root":
                pcnt += 1
                tag = '</p><p xml:id="%s-p%3.3da" type="root">' % ("%s" % ("_".join(xid)), pcnt )
            else:
                tag = ''
        else:
            tag = ''
        if (stage == "comm"):
            ols.append("%s%s" % (tag, l[1:-1]))
        else:
            ols.append("%s%s" % (tag, l[:-1]))
        sf = stage
    return ols


# In[6]:


# first build the data structures, than put them in tags.
def proc_lines2(ls):
    ols=[]
    sf = "None"
    stage = "None"
    ols.append([stage, []])
    for p, l in enumerate(ls):
        a = re.findall("^\s+", l)
        if len(a) > 0:
            if len(a[0]) == 1:
                stage = "comm"
            else:
                stage = "None"
        elif re.match(kanji, l[0]):
            s=re.match(kanji, l[0]).string
            if len(s) > 0:
                stage = "root"
            else:
                stage = "None"
#        else:
#            stage = "None3"
        if (stage != sf):
            ols.append([stage, []])
        if (stage == "comm"):
            ols[-1][-1].append(l[:-1].replace("\u3000", ""))
        else:
            ols[-1][-1].append(l[:-1])
        sf = stage
    return ols


# In[9]:


def proc_x(x, fid):
    out=[]
    xid = fid.split("_")
    xid.insert(1, "tls")
    counter = {'comm':0,'root':0, 'None': 0}
    for i, l in enumerate(x):
        flag = l[0]
        if flag == 'None':
            onr = "".join(l[1])
#            if (i==0):
#                onr = onr + "</p>"
            if onr.startswith("<"):
                out.append(onr)
            else:
                counter[flag] += 1
                cid = "%s-%3.3d" % ("_".join(xid), counter[flag])
                #out.append('<p xml:id="%spp"><seg xml:id="%sss">%s</seg></p>' % (cid, cid, onr))
                out.append('<seg xml:id="%sss">%s</seg>' % (cid, onr))
        elif flag == "root":
            counter[flag] += 1
            onr = "".join(l[1])
            cid = "%s-%3.3d" % ("_".join(xid), counter[flag])
#            osr = '<p xml:id="%sp"><seg state="locked" type="root" xml:id="%sps">%s</seg></p>' % (cid, cid, onr)
            osr = '<seg state="locked" type="root" xml:id="%sps">%s</seg>' % (cid, onr)
            if i+1 < len(x) and x[i+1][0] == "comm":
                fl1 = x[i+1][0]
                counter[fl1] += 1
                nid = "%s-%3.3d" % ("_".join(xid), counter[fl1])
#                osc = '<p xml:id="%sc"><seg state="locked" type="comm" xml:id="%scs">%s</seg></p>' % (nid, nid, "".join(x[i+1][1]))
                osc = '<seg state="locked" type="comm" xml:id="%scs">%s</seg>' % (nid, "".join(x[i+1][1]))
#                out.append('<div type="root-comm">\n%s\n%s</div>' % (osr, osc))
                out.append('\n%s\n%s' % (osr, osc))
            elif onr.endswith("</div>"):
#                osc = '<p xml:id="%sc"><seg state="locked" type="comm" xml:id="%scs">%s' % (cid, cid, onr)
                osc = '<seg state="locked" type="comm" xml:id="%scs">%s' % (cid, onr)
                out.append(osc.replace("</p>", "</seg></p>"))
            else:
                out.append(osr)
        elif flag == "comm":
            if x[i-1][0] == 'root':
                pass
            else:
                counter[flag] += 1
                cid = "%s-%3.3d" % ("_".join(xid), counter[flag])
                osr = '<p xml:id="%sc"><seg state="locked" type="comm" xml:id="%scs">%s</seg></p>' % (cid, cid, "".join(l[1]))
    return out


if __name__ == '__main__':

    try:
        txtid=sys.argv[1]
    except:
        print ("Textid should be given as argument.")
        sys.exit()


    ind = "/home/chris/00scratch/newkrp/code/%s/int/%s_master" % (txtid, txtid)
    tgt = "%s/new/" % (ind)
    os.makedirs(tgt, exist_ok=True)
    infs = os.listdir(ind)
    infs.sort()
    infs = [a for a in infs if  a.endswith("xml")]


    for fn in infs:
        f = "%s/%s" % (ind, fn)
        ls = open(f).readlines()
        if "_" in fn:
            x = proc_lines2(ls)
            out=proc_x(x, fn[:-4])
        else:
            print(fn)
            out = ls
        of=open("%s%s" % (tgt, fn), "w")
        of.write("".join(out))
        of.close()


# In[12]:
