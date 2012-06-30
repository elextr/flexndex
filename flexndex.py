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

import re, argparse, string, cStringIO
from contextlib import closing

# command line arguments
args = argparse.Namespace()

# predefined attributes
attributes = { 'sp' : ' ', 'nl' : '\n' }

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
            if k not in s.d: s.d[k] = Settings()
            s = s.d[k]
        s.v = value
    def get(self, key, default=None):
        """Key is and iterable, returns a settings object or None
           Key is a string, returns a value or default"""
        s = self
        if isinstance(key, str):
            if key in s.d: return s.d[key].v
            else: return default
        else:
            for k in key:
                if k not in s.d: return None
                s = s.d[k]
            return s
    def keys(self):
        return self.d.keys()
    def sorted_keys(self):
        s = self.d.keys(); s.sort()
        return s
    def key_sorted_values(self):
        return [ self.d[k].v for k in self.sorted_keys() ]
    def value(self):
        return self.v
    def parse(self, file):
        "Parse a settings file object into this Settings object"
        prefix = []; line = file.readline()
        while line :
            line = line.strip()
            if args.verbose > 3: print "Config line:", len(line), line,
            if len(line) > 0 and line[0] != '#':
                if line[0] == '[':
                    prefix = line[1:-1].split('.')
                    if args.verbose > 3: print "=>", prefix
                else:
                    k,v = line.split('=',1)
                    key = list(prefix)
                    key.extend(k.rstrip().split('.'))
                    v = v.strip()
                    while len(v) > 0 and v[-1] == '\\':
                        v = v[:-1]+strip(file.readline())
                    if args.verbose > 3: print "=>", key, '=', v
                    self.set(key, v)
            else:
                if args.verbose > 3: print 'ignored'
            line = file.readline()
    def debug_print(self, leader=''):
        print leader, "=", self.v
        for k in self.d.keys():
            if leader: l = leader + '.' + k
            else: l = k
            self.d[k].debug_print(l)

# return shared prefix of two iterables
def shared_prefix(i1, i2):
    pref = []
    for a,b in zip(i1, i2):
        if a!=b: break
        pref.append(a)
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
# {ixtext} - 'text' defined by target attrlist, or term if no text
# {xxxx} - where xxxx is anything else defined in the target attrlist

class Estyle:
    def __init__(self, settings=Settings()):
        self.text_internal = settings.get('text_internal', '')
        self.link_last = settings.get('link_last', '')
        self.text_last = settings.get('text_last', '')
        self.multi_target = settings.get('multi_target', '')

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
        if args.verbose > 2: settings.debug_print()
        self.complete = settings.get('complete', 'n')
        self.entry_start = settings.get('entry_start', '')
        self.entry_end = settings.get('entry_end', '')
        self.prefix = settings.get('prefix', '')
        self.postfix = settings.get('postfix', '')
        self.empty_message = settings.get('empty_message', 'Empty Index')
        self.levels = []
        l = settings.get(('levels',), None)
        if l is not None:
            self.levels = [ Estyle( l.get((i,)) ) for i in l.sorted_keys() ]
        c = settings.get(('col_start',), None)
        if c is not None: self.col_starts = c.key_sorted_values()
        else: self.col_starts = ['']
        c = settings.get(('col_end',), None)
        if c is not None: self.col_ends = c.key_sorted_values()
        else: self.col_ends = ['']
        c = settings.get(('row_start',), None)
        if c is not None: self.row_starts = c.key_sorted_values()
        else: self.row_starts = ['']
        c = settings.get(('row_end',), None)
        if c is not None: self.row_ends = c.key_sorted_values()
        else: self.row_ends = ['']


# Built-in style definitions

backends = [ 'html', 'xhtml11', 'docbook', 'docbook45' ]
backend_aliases = { 'html' : 'xhtml11', 'docbook' : 'docbook45' }
anchors = { 'xhtml11' : '<a id="ix{ixtgt}"></a>' ,
          'docbook45' : '<anchor id="ix{ixtgt}"/>' }

styles_config = """
[styles.simple-dotted.xhtml11]
levels.1.text_internal = {ixterm}.
levels.1.link_last = <a href="#ix{ixtgt}">{ixterm}</a>
levels.1.text_last = {ixterm}{sp}
levels.1.multi_target = <a href="#ix{ixtgt}">{ixtext} </a>
levels.2.text_internal = {ixterm}.
levels.2.link_last = <a href="#ix{ixtgt}">{ixterm}</a>
levels.2.text_last = {ixterm}{sp}
levels.2.multi_target = <a href="#ix{ixtgt}">{ixtext} </a>
levels.3.text_internal = {ixterm}.
levels.3.link_last = <a href="#ix{ixtgt}">{ixterm}</a>
levels.3.text_last = {ixterm}{sp}
levels.3.multi_target = <a href="#ix{ixtgt}">{ixtext}</a>
entry_start = <p>
entry_end = </p>{nl}

[styles.simple-grouped.xhtml11]
levels.1.text_internal = 
levels.1.link_last = <p><a href="#ix{ixtgt}">{ixterm}</a>
levels.1.text_last = <p>{ixterm}{sp}
levels.1.multi_target = <a href="#ix{ixtgt}">{ixtext}</a>{sp}
levels.2.text_internal = 
levels.2.link_last = <p style="text-indent:2em;"><a href="#ix{ixtgt}">{ixterm}</a>
levels.2.text_last = <p style="text-indent:2em;">{ixterm}{sp}
levels.2.multi_target = <a href="#ix{ixtgt}">{ixtext}</a>{sp}
levels.3.text_internal = 
levels.3.link_last = <p style="text-indent:4em;"><a href="#ix{ixtgt}">{ixterm}</a>
levels.3.text_last = <p style="text-indent:4em;">{ixterm}{sp}
levels.3.multi_target = <a href="#ix{ixtgt}">{ixtext}</a>{sp}
entry_end = </p>{nl}
complete = e

[styles.column-grouped.xhtml11]
levels.1.text_internal = 
levels.1.link_last = <p><a href="#ix{ixtgt}">{ixterm}</a>
levels.1.text_last = <p>{ixterm}{sp}
levels.1.multi_target = <a href="#ix{ixtgt}">{ixtext}</a>{sp}
levels.2.text_internal = 
levels.2.link_last = <p style="text-indent:2em;"><a href="#ix{ixtgt}">{ixterm}</a>
levels.2.text_last = <p style="text-indent:2em;">{ixterm}{sp}
levels.2.multi_target = <a href="#ix{ixtgt}">{ixtext}</a>{sp}
levels.3.text_internal = 
levels.3.link_last = <p style="text-indent:4em;"><a href="#ix{ixtgt}">{ixterm}</a>
levels.3.text_last = <p style="text-indent:4em;">{ixterm}{sp}
levels.3.multi_target = <a href="#ix{ixtgt}">{ixtext}</a>{sp}
prefix=<table width="100%"><tr>
postfix=</tr></table>
col_start.1 = <td valign="top">
col_end.1 = </td>{nl}
row_start.1 =
row_end.1 =</p>{nl}
complete = t

"""

styles = {}

default_style = 'simple-dotted'

inds = {}

# parse attrlist into a pair containing:
# tuple of positional attrs and dict of keyword attrs
# comma and equals can be included by including twice
att_split_re = re.compile(r',(?!,)')
att_key_re = re.compile(r'=(?!=)')
att_rep_re = re.compile(r'([=,])\1')
def attr_tuple(attlist):
    atts = [ x.strip() for x in att_split_re.split(attlist) ]
    if len(atts) == 1 and atts[0] == '':
        return (tuple(), {})
    patts = []; katts = {}
    for a in atts:
        s = [ att_rep_re.sub(r'\1', x) for x in att_key_re.split(a,1) ]
        if len(s) > 1: katts[s[0]] = s[1]
        else: patts.append( s[0] )
    return (tuple(patts), katts)

# output to file o after substituting attributes in strings
# print warning if key not found and leave in output
# accepts a list of mapping objects for subs values searched left to right
# kwargs for subs values, searched before any dicts
# attributes global searched last
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
                s = attributes.get(bit[1])
                if s is not None: o.write(s)
                else:
                    print "Warning: attribute", bit[1], "not found, left in output"
                    o.write('{'+bit[1]+'}')

ix_re = re.compile(r'<!-- ix (?P<target>\S+) <(?P<attrlist>[^>]*)> -->')
ixhere_re = re.compile(r'<!-- ixhere (?P<target>\S+) <(?P<attrlist>[^>]*)> -->')

def pass1():
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

levels_re = re.compile(r'(\d)*-?(\d)*')

# returns tuple:
#   entry list in output order
#   list of tuples of start/end counts
#   list of tuples of per-entry templates, start, end
#   list of tuples per-count templates, start, end
cattr_re = re.compile(r'(?P<num>\d+)(?P<id>(i|l)(r|c))(?P<break>.\d+)?')
def collimate(entries, hereattrs, styleob, lno):
    colattr = hereattrs.get('cols')
    if colattr is None:
        if args.verbose > 2: print "Not collimated"
        return ( entries,
                 [(0, len(entries))],
                 [(styleob.entry_start, styleob.entry_end)],
                 [('', '')] )
    if args.verbose > 2: print "Collimated"
    mo = cattr_re.match(colattr)
    if mo is None:
        print "Error: unrecognised column attribute", colattr, "at line", lno
        return [None, None, None, None]
    cols = int(mo.group('num'))
    # get list of column lengths
    counts = [len(entries)/cols] * cols
    for i in range(len(entries) % cols): counts[i] += 1
    if mo.group('break') is not None:
        blevel = int(mo.group('break')[1:])
        if args.verbose > 1: print "Break at", blevel
    else: blevel = None
    # adjust column lengths for break level
    cincr = 0
    for i in range(cols):
        c = counts[i] + cincr; b = c; cincr = c
        if blevel is not None and i < cols-1: 
            cmax = c + counts[i+1]/2; bmin = c - counts[i]/2;
            if args.verbose > 2: print "c, cmax, bmin", c, cmax, bmin
            while len(entries[c][0]) > blevel and len(entries[b][0]) > blevel:
                c += 1; b -= 1
                if args.verbose > 2: print "c,b",c,b
                if c >= cmax and b <= bmin :
                    c = cincr
                    break
            else:
                if len(entries[b][0]) <= blevel: c = b
        if args.verbose > 2: print "c=",c
        counts[i] = c
    # get increments and style pairs dependent on id
    id = mo.group('id')
    if id == 'lc':
        prev = 0; count_pairs = []
        for i in counts:
            count_pairs.append((prev, i-1))
            prev = i
        estyles = zip(styleob.row_starts, styleob.row_ends)
        cstyles = zip(styleob.col_starts, styleob.col_ends)
    elif id == 'lr':
        pass
    elif id == 'ic':
        pass
    elif id == 'ir':
        pass
    if args.verbose > 2:
        print "    Column lengths", count_pairs
        print "    Entry Styles", estyles
        print "    Count styles", cstyles
    return [entries, count_pairs, estyles, cstyles]
    
def pass2():
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
                # decode the ixhere comment and attributes
                hereindex = inds.get(m.group('target'), {})
                selargs, hereattrs = attr_tuple(m.group('attrlist'))
                style = hereattrs.get('style', default_style)
                if style not in styles :
                    print 'Warning: index style', style,
                    print "not found, using default, at line ", lno
                    style = default_style
                styleob = styles[style].get(args.backend)
                if styleob is None:
                    print "Warning: backend", args.backend,
                    print "not found for style", style, ", index omitted",
                    print "at line", lno
                    continue
                subout(o, styleob.prefix, hereattrs )
                #get terms
                terms = hereindex.keys()
                if args.verbose > 2 : print 'Terms in index', terms
                if len(terms) == 0:
                    subout(o, styleob.empty_message, hereattrs)
                    continue
                # select only terms matching the arguments
                if len(selargs) > 0:
                    terms = [ x for x in terms if x[0:len(selargs)] == selargs ]
                terms.sort()
                # generate missing entries if needed
                if styleob.complete.startswith('e') or styleob.complete.startswith('t'):
                    entries = []; lastentry = []
                    for entry in terms:
                        pref_len = len(shared_prefix(entry, lastentry))
                        while pref_len+1 < len(entry):
                            entries.insert(0, [entry[:pref_len+1], {}, False])
                            pref_len += 1
                        if styleob.complete.startswith('t') and len(hereindex[entry]) > 1:
                            for t in hereindex[entry].items():
                                entries.insert(0, [list(entry), {t[0] : t[1]}, True])
                        else:
                            entries.insert(0, [list(entry), hereindex[entry], False])
                        lastentry = entry
                    entries.reverse()
                else:
                    entries = [ [list(x), hereindex[x], False] for x in terms ]
                # filter out by levels
                if 'levels' in hereattrs:
                    minl, maxl = levels_re.match(hereattrs['levels']).groups()
                    if maxl: maxl = int(maxl)
                    else: maxl = 1000
                    if minl: minl = int(minl)-1
                    else: minl = 0
                    entries = [ x for x in entries if len(x[0]) > minl and len(x[0]) < maxl ]
                else:
                    minl = 0
                # collimate
                entries, counts, estyles, cstyles = collimate(entries, hereattrs, styleob, lno)
                if entries is None: continue
                elen = len(estyles); clen = len(cstyles)
                # iterate through entries
                count = 0; count_min, count_max = counts.pop(0)
                count_no = 0; entry_no = 0;
                for entry, tgt, mte in entries:
                    if count == count_min:
                        subout(o, cstyles[count_no][0], hereattrs)
                    subout(o, estyles[entry_no][0], hereattrs )
                    # output internal levels from minimum
                    for term, tstyle in zip(entry[minl:-1], styleob.levels):
                        subout(o, tstyle.text_internal, hereattrs, ixterm=term)
                    # output the last level as link or multi target
                    if len(entry) <= len(styleob.levels):
                        tstyle = styleob.levels[len(entry)-1]
                        lt = len(tgt)
                        if lt == 1 and not mte:
                            # single target, make the last term text a link
                            rn, tgt_attrs = tgt.items()[0]
                            txt = tgt_attrs.get('text', entry[-1])
                            subout(o, tstyle.link_last, tgt_attrs, hereattrs,
                                ixterm=entry[-1], ixtgt=rn, ixtext=txt)
                        else:
                            # no target, output last term as text
                            subout(o, tstyle.text_last, hereattrs, ixterm=entry[-1])
                        if lt > 1 or mte:
                            # multiple targets, iterate through the multi targets
                            for t in tgt.items():
                                txt = t[1].get('text', entry[-1])
                                subout(o, tstyle.multi_target, t[1], hereattrs,
                                    ixterm = entry[-1], ixtgt=t[0], ixtext=txt)
                        subout(o, estyles[entry_no][1], hereattrs)
                        entry_no = (entry_no + 1) % elen
                        if count == count_max:
                            subout(o, cstyles[count_no][1], hereattrs)
                            if len(counts) == 0: break
                            count_min, count_max = counts.pop(0)
                        count += 1
                        count_no = (count_no + 1) % clen
                    else:
                        print "Warning, not enough style levels for target terms", entry
                subout(o, styleob.postfix, hereattrs)
            upto = 0
            for m in ix_re.finditer(line):
                if args.verbose > 1 : print 'Found ix in: ', line,
                ic += 1
                a, tgt_attrs = attr_tuple(m.group('attrlist'))
                o.write(line[upto:m.end()])
                upto = m.end()
                text = tgt_attrs.get('text', a[-1])
                subout(o, anchors[args.backend], tgt_attrs, ixtext=text, ixtgt=str(rno))
                rno += 1
            o.write( line[upto:] )
    if args.verbose > 0: print 'Pass 2 found', ic, 'ix entries', hc, 'ixhere entries'

def main():
    global args
    p = argparse.ArgumentParser(description='Flexible index generator')
    p.add_argument('infile', help='Input File')
    p.add_argument('outfile', help='Output File')
    p.add_argument('--verbose','-v', action='count')
    p.add_argument('--backend', '-b', default='xhtml11')
    p.add_argument('--config', '-c', action='append')
    p.add_argument('--version', action='version', version='flexndex.0.1alpha')
    args = p.parse_args()
    args.backend = backend_aliases.get(args.backend, args.backend)
    conf_settings = Settings()
    # TODO attributes anchors and default style from config
    with closing(cStringIO.StringIO(styles_config)) as fo:
        conf_settings.parse(fo)
    if args.config:
        for f in args.config:
            with open(f,'r') as fo:
                conf_settings.parse(fo)
    if args.verbose >2: conf_settings.debug_print()
    sts = conf_settings.get(('styles',))
    for s in sts.keys():
        if args.verbose > 1: print "Got style", s,
        st = sts.get((s,))
        for b in st.keys():
            if args.verbose >1: print "backend", b,
            if s not in styles: styles[s] = {}
            styles[s][b] = Style(st.get((b,)))
        if args.verbose > 1: print
    pass1()
#    print inds
    pass2()
    return 0

if __name__ == '__main__':
    main()

