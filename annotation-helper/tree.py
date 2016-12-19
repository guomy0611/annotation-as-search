'''
Module to work with CONLL parses by allowing to ask and answer questions
about the parse trees, allowing to filter a parse forest until only
one parse tree remains.
'''

from collections import Counter
from subprocess import call
import sys
import re

class Tree(object):
    '''
    Class to contain the complete CONLL parse of a sentence and many methods
    to work with it.
    '''

    def __init__(self, head=8, dep=10):
        '''
        Initialize the Tree with an empty list later containing the CONLL-Tuples
        and an empty dictionary later containing the position -> word mapping.
        '''
        self.nodes = []
        self.dictio = dict()
        self.tuples = None
        self.head = head
        self.dep = dep
        self.format = None

    @classmethod
    def from_string(cls, tree_string):
        '''
        Initialize a tree object from an already formatted conll string.
        '''
        tree = cls()
        lines = [
            line.strip()
            for line in tree_string.split('\n')
            # Ignore empty lines and lines starting with '#'
            if not re.match(r'(^\s*$)|(^#.*$)', line)
            ]
        for line in lines:
            tree.add(line)

        return tree

    def add(self, conll_line):
        '''
        Gets a CONLL-Line, splits it and then converts it into a tuple to
        be added into the list. Also puts a new entry into the dictionary
        containing the position -> word mapping of this line.
        '''
        conll_parts = conll_line.strip().split('\t')
        self.nodes.append(tuple(conll_parts))

        # fills mapping position -> word
        self.dictio[conll_parts[0]] = conll_parts[1]

    def contains(self, tup):
        '''
        Checks if a 3-tuple (for example ('Es1', 'ist2', 'SB') ) is contained
        in this tree.
        '''
        return tup in self.get()

    def overlap(self, other):
        '''
        Returns the number of triples contained in the tree and a given
        other tree.
        '''
        return len(set(self.get())&set(other.get()))

    def get(self):
        '''
        Gets a list of 3-tuples from the list containing the CONLL-tuples.
        '''
        #print(self.dictio)
        if self.tuples is not None: return self.tuples
        self.tuples={(self.dictio[x[0]]+"-"+x[0], #Look up the index
                 #in the dictionary, take the word and add the
                 #the index to the word.
                 self.dictio[x[self.head]]+"-"+x[self.head] if x[self.head] != "0" else "Root-0",
                 #Look up the index of the target word in the dictionary
                 #take the word and add the index to it.
                 x[self.dep]) for x in self.nodes}
                 #Last element of the tuple is the relation type.
        return self.tuples

    def to_conll(self):
        '''
        Returns a complete CONLL Representation of the parse contained
        in this object.
        '''
        return "\n".join("\t".join(x) for x in self.nodes)

    def to_latex(self):
        '''
        Writes latex to a hard-coded latexfile and then generates a
        parse visualization from it.
        '''
        string = """\\documentclass[dvisgm]{minimal}
                \\usepackage{tikz-dependency}
                \\begin{document}
                \\begin{dependency}
                \\begin{deptext}[column sep=0.2cm]\n"""
        string += " \\& ".join(self.dictio[str(key)] for key in \
                   sorted([int(x) for x in self.dictio.keys()]))+"\\\\ \n"
        string += "\\end{deptext}\n"
        for value in self.nodes:
            if value[8] == "0":
                string += "\\deproot{"+str(value[0])+"}{root}\n"
            else:
                string += "\\depedge{"+str(value[0])+"}{"+str(value[8])+"}\
                            {"+value[10]+"}\n"
        string += """\\end{dependency}
                   \\end{document}"""
        open("test10.tex", "w").write(string)
        print(string)
        call(["latex", "test10.tex"])
        call(["dvisvgm", "test10.dvi"])

    def as_dict(self):
        return {'nodes': self.nodes}

class Forest(object):
    '''
    A Forest object is there to deal with multiple tree objects.
    '''

    def __init__(self):
        '''
        Forest is there to contain many tree objects.
        '''
        self.trees = []
        self.originaltrees = None
        self.answeredtuples=[]

    @classmethod
    def from_string(cls, forest_string):
        '''
        Initialize a forest object from a long string formatted like a conll
        file.
        '''
        forest = cls()
        for tree_string in forest_string.split('\n\n'):
            forest.add(Tree.from_string(tree_string))
        return forest

    def solved(self):
        '''
        True if the forest clears and only one tree remains.
        '''
        return len(self.trees) == 1

    def add(self, finishedtree):
        '''
        Adds a filled tree into the parse forest.
        '''
        self.trees.append(finishedtree)

    def get_dict(self):
        '''
        Returns a list containing 3-tuples and their counts.
        Example: ('Es1', 'ist2', 'SB'): 540
        '''
        return Counter([x for tree in self.trees for x \
                           in tree.get()]).most_common()

    def question(self):
        '''
        Chooses the tuple minimizing the equation:
                      lambda x: abs(x[1]-length/2
        This is the tuple having the best chance to halve
        the search space.
        '''
        length = len(self.trees)
        return min(self.get_dict(), key=lambda x: abs(x[1]-length/2))[0]

    def filter(self, asked_tuple, boolean):
        '''
        Wrapper around the _filter method that adds asked_tuples to a
        list of answered tuples. This list can then be used by the undo
        method.
        '''
        if self.originaltrees is None:
            self.originaltrees = self.trees[:]
        self.answeredtuples.append((asked_tuple, boolean))
        self._filter(asked_tuple, boolean)

    def _filter(self, asked_tuple, boolean):
        '''
        Filters the treelist based on a tuple and a boolean value.
        if True: keeps all the lists where the tuple is contained.
        if False: keeps all the list where the tuple isnt.
        '''
        self.trees = [tree for tree in self.trees
            if tree.contains(asked_tuple) == boolean]

    def undo(self, n=1):
        '''
        Restore the state the forest was in n questions earlier.
        '''
        self.answeredtuples = self.answeredtuples[:-n]
        self.trees = (
            self.originaltrees[:]
            if self.originaltrees is not None
            else self.trees[:]
            )
        for question, answer in self.answeredtuples:
            self._filter(question, answer)

    def get_fixed_edges(self):
        '''
        Function that returns the tuples that are fixed (additional
        answers wont change them).
        '''
        length = len(self.trees)
        return [x for x,y in self.get_dict() if y==length]

    def get_fixed_nodes(self):
        '''
        Find the nodes that exist in every tree and return them as a list.
        This method assumes that all trees in the forest have the same number
        of nodes.
        '''
        fixed_nodes = []
        if len(self.trees) == 0:
            return fixed_nodes

        for node_index in range(len(self.trees[0].nodes)):
            for tree in self.trees:
                if tree.nodes[node_index] != self.trees[0].nodes[node_index]:
                    break
            else:
                fixed_nodes.append(self.trees[0].nodes[node_index])

        return fixed_nodes

if __name__ == "__main__":
    tree = Tree()
    forest = Forest()
    for line in open(sys.argv[1]):
        if line == "\n":
            forest.add(tree)
            tree = Tree()
            continue
        tree.add(line)
    while len(forest.trees) != 1:
        question = forest.question()
        print(" ".join(x[1] for x in forest.trees[0].nodes))
        answer = input(question)
        if answer == "j":
            forest.filter(question, True)
        else:
            forest.filter(question, False)
        if len(forest.trees) == 1:
            forest.trees[0].to_latex()
            print(forest.trees[0].to_conll())
