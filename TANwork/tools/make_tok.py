#!/usr/bin/env python
# coding: utf-8

# In[1]:
from lxml import etree
from difflib import *
import re

def isKanji(c):
    kanji='[\u3400-\u4DFF\u4e00-\u9FFF\uF900-\uFAFF\uFE30-\uFE4F\U00020000-\U0002A6DF\U0002A700-\U0002B73F\U0002B740-\U0002B81F\U0002B820-\U0002F7FF]'
    return re.match(kanji, c)
    

def getrefs(el, refs=[]):
    p = el.getparent()
    n = etree.QName(p.tag).localname
    if not(p is None) and n == 'div' :
        refs.append(p.attrib['n'])
        getrefs(p, refs)
    return " ".join(reversed(refs))

def make_seg(src, ns={"tan":"tag:textalign.net,2015:ns"}):
    s1 = []
    tree=etree.parse(src)
    root = tree.getroot()
    for div in root.findall("./tan:body//tan:div", ns):
        r = getrefs(div, [div.attrib['n']])
        if div.text is None:
            continue
        toks = [char for char in div.text if isKanji(char)]
        for i, tok in enumerate(toks):
            s1.append((tok, r, i+1,))
    return s1

    
src='KR6c0128.zho.T.2019.xml'
trg="KR6c0128.zho.TKD.1967.xml"
s1=make_seg(src)
s2=make_seg(trg)
s=SequenceMatcher()
s.set_seq1([a[0] for a in s1])
s.set_seq2([a[0] for a in s2])
o=s.get_opcodes()
# proof of concept
for tag, i1, i2, j1, j2 in o:
    if tag == 'delete':
        print ("<align>\n<tok src='%s' ref='%s - %s'/>\n</align>" % ('src', s1[i1][1], s1[i2][1]))
    elif tag == 'replace':
        print ("<align>\n<tok src='%s' ref='%s' pos='%s'/>\n<tok src='%s' ref='%s' pos='%s'/></align><!-- rep %s %s -->" % ('src', s1[i1][1], s1[i1][2], 'trg', s2[j1][1], s2[j1][2], s1[i1][0], s2[j1][0]))
    elif tag == 'equal':
        j=j1
        for i in range(i1, i2):
            print ("<align>\n<tok src='%s' ref='%s' pos='%s'/>\n<tok src='%s' ref='%s' pos='%s'/></align><!-- eq %s %s -->" % ('src', s1[i][1], s1[i][2], 'trg', s2[j1][1], s2[j][2], s1[i][0], s2[j][0]))
            j+=1
    elif tag == 'insert':
        print ("<align>\n<tok src='%s' ref='%s - %s'/>\n</align>" % ('trg', s2[j1][1], s2[j2-1][1]))
