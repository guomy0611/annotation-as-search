#!/usr/bin/env python3
# -*- coding: utf-8

# Finish-Dependency-Parser imports
import codecs
import sys
import os
import collections


try:
    import argparse
except ImportError:
    import compat.argparse as argparse

SCRIPTDIR=os.path.dirname(os.path.abspath(__file__))

def read_conll(inp,maxsent=1):
    '''
    Read conll format sentences.
    Read the conll format sentences as a string passed as argument. The sentences
    have to be seperated by a blank line. If no sentence is not passed
    as argument, read the sentences from stdin.

    arguments:
        inp:
            conll format sentence of type string
        maxsent:
            number of sentences read at maximum
    '''

    if isinstance(inp,str):
        f=inp.split('\n')
    else:
        f=codecs.getreader("utf-8")(sys.stdin.buffer) # read stdin
    count=0
    sent=[]
    comments=[]
    for line in f:
        line=line.strip()
        if not line:
            if sent:
                count+=1
                yield sent, comments
                if maxsent!=0 and count>=maxsent:
                    break
                sent=[]
                comments=[]
        elif line.startswith("#"):
            if sent:
                raise ValueError("Missing newline after sentence")
            comments.append(line)
            continue
        else:
            sent.append(line.split("\t"))
    else:
        if sent:
            yield sent, comments


header='<div class="conllu-parse">\n'
footer='</div>\n'

def sort_feat(f):
    #CoNLL-U requirement -> turn off when no longer required by the visualizer
    if f=="_":
        return f
    new_list=[]
    for attr_val in f.split("|"):
        if "=" in attr_val:
            attr,val=attr_val.split("=",1)
        else:
            attr,val=attr_val.split("_",1)
        attr=attr.capitalize()
        val=val.capitalize()
        val=val.replace("_","")
        new_list.append(attr+"="+val)
    return "|".join(sorted(new_list))

Format=collections.namedtuple(
                            'Format',
                            ['ID','FORM','LEMMA','CPOS','POS','FEAT',
                            'HEAD','DEPREL','DEPS','MISC']
                            )
f_09=Format(0,1,2,4,4,6,8,10,None,None)
f_u=Format(0,1,2,3,4,5,6,7,8,9)

#         0  1    2     3       4  5    6    7      8    9     10     11
#conll-u  ID FORM LEMMA CPOS   POS FEAT HEAD DEPREL DEPS MISC
#conll-09 ID FORM LEMMA PLEMMA POS PPOS FEAT PFEAT  HEAD PHEAD DEPREL PDEPREL _ _

def get_col(cols,idx):
    if idx is None:
        return "_"
    else:
        return cols[idx]

def visualize(args, complete=0):
    ''' visualise tree in html '''
    data_to_print=""
    for sent,comments in read_conll(args.input,args.max_sent):
        tree=header
        if comments:
            tree+="\n".join(comments)+"\n"
        for line in sent:
            if len(line)==10: #conll-u
                f=f_u
            else:
                f=f_09
            line[f.FEAT]=sort_feat(line[f.FEAT])
            # take idx,token,lemma,pos,pos,feat,deprel,head
            l="\t".join(get_col(line,idx) for idx in [
                                            f.ID, f.FORM, f.LEMMA, f.CPOS,
                                            f.POS, f.FEAT, f.HEAD, f.DEPREL,
                                            f.DEPS, f.MISC
                                            ])
            tree+=l+"\n"
        tree+="\n" #conll-u expects an empty line at the end of every tree
        tree+=footer
        data_to_print+=tree
    if not complete:
        with codecs.open(os.path.join(
                                SCRIPTDIR,
                                "templates",
                                "simple_brat_viz.html"
                                ),
                                "r",
                                "utf-8"
                        ) as template:
            data=template.read().replace("CONTENTGOESHERE",data_to_print,1)
            with open("templates/options.html") as options:
                final_part = options.read()
    else:
        print("complete")
        with codecs.open(os.path.join(
                                SCRIPTDIR,
                                "templates",
                                "simple_brat_viz_complete_sentence.html"
                                ),
                                "r",
                                "utf-8"
                        ) as template:
            data=template.read().replace("CONTENTGOESHERE",data_to_print,1)
            with open("templates/options_final.html") as options:
                final_part = options.read()
    data = data.replace("OPTIONSGOHERE", final_part)
    return data
 


if __name__==u"__main__":

    description = 'Trains the parser in a multi-core setting.'
    parser = argparse.ArgumentParser(description)
    g=parser.add_argument_group("Input/Output")
    g.add_argument(
                    'input',
                    nargs='?',
                    help='Parser output file name, or nothing for reading on stdin'
                )
    g.add_argument(
                    '--max_sent',
                    type=int,
                    default=0,
                    help='How many trees to show? 0 for all. (default %(default)d)'
                )
    args = parser.parse_args()
    visualize(args)

