#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  untitled.py
#  
#  Copyright 2012 Lex <lex@fred5>
#  
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#  
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following disclaimer
#    in the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#  
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#  OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#  THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#  

import re, argparse, string

# Settings file, hierarchical keys, values text only
#
# all lines are stripped first, whitespace around the = is stripped
# blank lines are ignored
# lines can be:
# #         starts a comment line
# key=value where key is a dot separated list of key levels
#           and value can be extended by ending lines with \
# [prefix]  is a prefix to put before following keys
# keys can contain anything except =, . # and [], values anything

class Settings:
    def __init__(self):
        self.d = {}
        self.v = None
    def set(self, key, value):
        "Key is iterable of key hierarchy, makes missing levels, set value"
        s = self
        for k in key:
            if k not in s.d: s.d[k] = settings()
            s = s.d[k]
        s.v = value
    def get(self, key, default=None):
        "Key is iterable of key hierarchy, returns a settings object"
        s = self
        for k in key:
            if k not in s.d: return default
            s = s.d[k]
        return s
    def keys(self):
        return s.d.keys()
    def sorted_keys(self):
        s = s.d.keys(); s.sort()
        return s
    def value(self):
        return v
    def parse(self, file):
        "Parse a settings file into this object"
        prefix = []; line = file.readline()
        while line :
            line = strip(line)
            if len(line) > 0 and line[0] != '#':
                if line[0] == '[':
                    prefix = line[1:-1].split('.')
                else:
                    k,v = line[1:-1].split('=')
                    key = prefix
                    key.extend(k.rstrip().split('.'))
                    v = v.strip()
                    while len(v) > 0 and v[-1] == '\\':
                        v = v[:-1]+strip(file.readline())
                    self.set(key, v)

# return count of shared prefix of two iterables
def shared_prefix(i1, i2):
    pref = 0
    for a,b in zip(i1, i2):
        if a!=b: break
        pref += 1
    return pref

# Layout of entry style in class Estyle
#
# text_internal - use this markup if not last
# link_last - use this markup if single target is available and last
# text_last - use this markup if single target is not available and last
# multi_target - use this markup for each if multiple targets are available
#
# Substitutions in the markups:
#
# {ixterm} - index term
#
# in link_last or multi_target only
#
# {ixtgt} - index term target number
# {tgt_text} - 'text' defined by target attrlist, or term if no text
# {xxxx} - where xxxx is anything else defined in the target attrlist

class Estyle:
    def __init__(self, settings=Settings()):
        self.text_internal = settings.get('text_internal')
        self.link_last = settings.get('link_last')
        self.text_last = settings.get('text_last')
        self.multi_target = settings.get('multi_target')          

# Layout of info in class Style
#
# levels - list of Estyles for each level
# entry_start - markup/text before entry, for grouped array indexed by level
# entry_end - markup/text after entry, for grouped array indexed by level
# prefix - markup/text before the index
# postfix - markup/text after the index
# empty_message - message if no entries, default 'Index Empty'

class Style:
    def __init__(self, settings=Settings()):
        self.complete = settings.get('complete', 'n')
        self.entry_start = settings.get('entry_start', '')
        self.entry_end = settings.get('entry_end', '')
        self.prefix = settings.get('prefix', '')
        self.postfix = settings.get('postfix', '')
        self.empty_message = settings.get('empty_message', 'Empty Index')
        self.levels = []
        l = settings.get('levels', None)
        if l is not None:
            for i in l.sorted_keys():
                self.levels.append( Estyle( l.get(i) ) )

# Built-in style definitions

backends = [ 'html', 'xhtml11', 'docbook', 'docbook45' ]
backend_aliases = { 'html' : 'xhtml11', 'docbook' : 'docbook45' }
anchors = { 'xhtml11' : '<a id="ix{ixtgt}"></a>' ,
          'docbook45' : '<anchor id="ix{ixtgt}"/>' }

xhtml_dotted_1 = Estyle()
xhtml_dotted_1.text_internal = '{ixterm}.'
xhtml_dotted_1.link_last = '<a href="#ix{ixtgt}">{ixterm}</a> '
xhtml_dotted_1.text_last = '{ixterm} '
xhtml_dotted_1.multi_target = '<a href="#ix{ixtgt}">[{tgt_text}] </a>'
xhtml_dotted_2 = Estyle()
xhtml_dotted_2.text_internal = '{ixterm}.'
xhtml_dotted_2.link_last = '<a href="#ix{ixtgt}">{ixterm}</a> '
xhtml_dotted_2.text_last = '{ixterm} '
xhtml_dotted_2.multi_target = '<a href="#ix{ixtgt}">[{tgt_text}] </a>'
xhtml_dotted_3 = Estyle()
xhtml_dotted_3.text_internal = '{ixterm}.'
xhtml_dotted_3.link_last = '<a href="#ix{ixtgt}">{ixterm}</a> '
xhtml_dotted_3.text_last = '{ixterm} '
xhtml_dotted_3.multi_target = '<a href="#ix{ixtgt}">[{tgt_text}]</a>'
xhtml_dotted = Style()
xhtml_dotted.levels = [ xhtml_dotted_1, xhtml_dotted_2, xhtml_dotted_3 ]
xhtml_dotted.entry_end = '<br/>'
dotted_styles = { 'xhtml11' : xhtml_dotted }

xhtml_grouped_1 = Estyle()
xhtml_grouped_1.text_internal = ''
xhtml_grouped_1.link_last = '<p><a href="#ix{ixtgt}">[{ixterm}]</a>'
xhtml_grouped_1.text_last = '<p>{ixterm} '
xhtml_grouped_1.multi_target = '<a href="#ix{ixtgt}">[{tgt_text}] </a>'
xhtml_grouped_2 = Estyle()
xhtml_grouped_2.text_internal = ''
xhtml_grouped_2.link_last = \
    '<p style="text-indent:2em;"><a href="#ix{ixtgt}">[{ixterm}]</a>'
xhtml_grouped_2.text_last = '<p style="text-indent:2em;">{ixterm} '
xhtml_grouped_2.multi_target = '<a href="#ix{ixtgt}">[{tgt_text}] </a>'
xhtml_grouped_3 = Estyle()
xhtml_grouped_3.text_internal = ''
xhtml_grouped_3.link_last = \
    '<p style="text-indent:4em;"><a href="#ix{ixtgt}">{ixterm}</a>'
xhtml_grouped_3.text_last = '<p style="text-indent:4em;">{ixterm} '
xhtml_grouped_3.multi_target = '<a href="#ix{ixtgt}">[{tgt_text}]</a>'
xhtml_grouped = Style()
xhtml_grouped.levels = [ xhtml_grouped_1, xhtml_grouped_2, xhtml_grouped_3 ]
xhtml_grouped.entry_end = '</p>\n'
xhtml_grouped.complete = 'y'
grouped_styles = { 'xhtml11' : xhtml_grouped }

styles = { 'dotted' : dotted_styles, 'simple-grouped' : grouped_styles }

default_style = 'dotted'

inds = {}

# parse attrlist into a pair containing:
# tuple of positional attrs and dict of keyword attrs
def attr_tuple(attlist):
    atts = [ x.strip() for x in attlist.split(',') ]
    if len(atts) == 1 and atts[0] == '':
        return (tuple(), {})
    patts = []; katts = {}
    for a in atts:
        s = a.split('=',1)
        if len(s) > 1: katts[s[0]] = s[1]
        else: patts.append( a )
    return (tuple(patts), katts)

# output to file o after substituting attributes in strings
# print warning if key not found and leave in output
# accepts a list of mapping objects for subs values searched left to right
# kwargs for subs values, searched before any dicts
fmt = string.Formatter()
def subout(o, sstr, *dicts, **kwargs):
    bits = fmt.parse(sstr)
    for bit in bits:
        if bit[0]: o.write(bit[0])
        if bit[1] is not None:
            s = kwargs.get(bit[1])
            if s is not None:
                o.write(s)
                continue
            for d in dicts:
                s = d.get(bit[1])
                if s is not None:
                    o.write(s)
                    break
            else:
                print "Warning: keyword", bit[1], "not found, left in output"
                o.write('{'+bit[1]+'}')

# output an uncolumnated index
def uncoledout(o, k, styleob, hereattrs, tgts, comp):
    subout(o, styleob.prefix, hereattrs )
    entry = []
    for tentry in k :
        pref_len = shared_prefix(entry, tentry)
        done = False
        while not done:
            if comp and pref_len+1 < len(tentry):
                tgt = {}
                entry = entry[:pref_len]; entry.append(tentry[pref_len])
                pref_len += 1
            else:
                tgt = tgts[tentry]
                entry = list(tentry)
                done = True
            subout(o, styleob.entry_start, hereattrs )
            for term, tstyle in zip(entry[:-1], styleob.levels):
                subout(o, tstyle.text_internal, hereattrs, ixterm=term)
            if len(entry) <= len(styleob.levels):
                tstyle = styleob.levels[len(entry)-1]
                lt = len(tgt)
                if lt == 1:
                    rno, tgt_attrs = tgt.items()[0]
                    txt = tgt_attrs.get('text', entry[-1])
                    subout(o, tstyle.link_last, tgt_attrs, hereattrs,
                        ixterm=entry[-1], ixtgt=rno, tgt_text=txt)
                else:
                    subout(o, tstyle.text_last, hereattrs, ixterm=entry[-1])
                if lt > 1:
                    for t in tgt.items():
                        txt = t[1].get('text', entry[-1])
                        subout(o, tstyle.multi_target, t[1], hereattrs, 
                            ixterm = entry[-1], ixtgt=t[0], tgt_text=txt)
                subout(o, styleob.entry_end, hereattrs)
            else:
                print "Warning, not enough style levels for target terms", entry
    subout(o, styleob.postfix, hereattrs)
    
ix_re = re.compile(r'<!-- ix (?P<target>\w+) <(?P<attrlist>[^>]*)> -->')
ixhere_re = re.compile(r'<!-- ixhere (?P<target>\w+) <(?P<attrlist>[^>]*)> -->')
    
def pass1(args):
    if args.verbose > 1 : print "Pass 1"
    ic = 0
    with open(args.infile, 'r') as f:
        rno = 0
        for line in f:
            for m in ix_re.finditer(line):
                if args.verbose > 1 : print 'Found ix in: ', line,
                ic += 1
                tgt = m.group('target')
                if tgt not in inds: inds[tgt] = {}
                a, d = attr_tuple(m.group('attrlist'))
                if a not in inds[tgt]:
                    inds[tgt][a] = {}
                inds[tgt][a][str(rno)] = d
                rno += 1
    if args.verbose > 0 : print 'Pass 1 found', ic, 'ix entries'

def pass2(args):
    if args.verbose > 1 : print "Pass 2"
    ic = 0; hc = 0
    with open(args.infile, 'r') as f, open(args.outfile,'w') as o:
        rno = 0; lno = 0
        for line in f:
            lno += 1
            m = ixhere_re.search(line)
            if m is not None:
                if args.verbose > 1 : print 'Found ixhere in: ', line,
                hc += 1
                tgts = inds.get(m.group('target'), {})
                a, hereattrs = attr_tuple(m.group('attrlist'))
                k = tgts.keys()
                if 'levels' in hereattrs:
                    #TODO levels max, min
                    l = int(hereattrs['levels'])
                    k = [ x for x in k if len(x) <= l ]
                if len(a) > 0:
                    k = [ x for x in k if x[0:len(a)] == a ]
                if len(k) == 0:
                    subout(o, styleob.empty_message, hereattrs)
                    continue
                k.sort()
                style = hereattrs.get('style', default_style)
                if style not in styles :
                    print 'Warning: index style', style, 
                    print "not found, using default, at line ", lno
                    style = default_style
                styleob = styles[style].get(args.backend)
                if styleob is not None:
                    uncoledout(o, k, styleob, hereattrs, tgts, styleob.complete.startswith('y'))
                else:
                    print "Warning: backend", args.backend,
                    print "not found for style", style, ", index omitted",
                    print "at line", lno
            upto = 0
            for m in ix_re.finditer(line):
                if args.verbose > 1 : print 'Found ix in: ', line,
                ic += 1
                a, tgt_attrs = attr_tuple(m.group('attrlist'))
                o.write(line[upto:m.end()])
                upto = m.end()
                text = tgt_attrs.get('text', a[-1])
                subout(o, anchors[args.backend], tgt_attrs, tgt_text=text, ixtgt=str(rno))
                rno += 1
            o.write( line[upto:] )
    if args.verbose > 0: print 'Pass 2 found', ic, 'ix entries', hc, 'ixhere entries'

def main():
    p = argparse.ArgumentParser(description='Flexible index generator')
    p.add_argument('infile', help='Input File')
    p.add_argument('outfile', help='Output File')
    p.add_argument('--verbose','-v', action='count')
    p.add_argument('--backend', '-b', default='xhtml11')
    p.add_argument('--config', '-c', action='append')
    p.add_argument('--version', action='version', version='flexndex.0.1alpha')
    args = p.parse_args()
    args.backend = backend_aliases.get(args.backend, args.backend)
    #TODO load configs
    pass1(args)
#    print inds
    pass2(args)
    return 0

if __name__ == '__main__':
    main()

