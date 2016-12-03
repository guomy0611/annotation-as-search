'''
Class containing a Evaluator class which automates
the question answering by looking up the correct
answer in a gold parse.
'''
import tree

class Evaluator(object):
    '''
    Class to automatically answer questions given a file with 
    kbest parses and a file containing the goldparse.
    '''
    def __init__(self, file_with_kbest, goldfile):
        '''
        Initialize the object
        '''
        self.file_with_kbest = file_with_kbest
        self.goldfile = goldfile
        self.initialize()
    def initialize(self):
        '''
        Read the files and construct Tree and Forest objects.
        Gets called by __init__
        '''
        self.goldtree=tree.Tree()
        for line in open(self.goldfile):
            if line == "\n":
                self.goldtree.add(line)
        self.forest = tree.Forest()
        temptree = tree.Tree()
        for line in open(self.file_with_kbest):
            if line == "\n":
                self.forest.add(temptree)
                temptree = tree.Tree()
                continue
            temptree.add(line)
    def evaluate(self):
        '''
        Evaluates a forest with the given goldparse and returns
        some statistics, like number of guesses needed, the number
        of times no tree was left,
        labelled attachment score when only 1 tree is left from
        forest and the minimum edit distance when only 1 tree is left.
        '''
        count = 0
        while len(self.forest.liste) != 1:
            count += 1
            print(count)
            question = self.forest.question()
            print(question)
            print(question in self.goldtree.get())
            if question in self.goldtree.get():
                self.forest.filter(question, True)
            else:
                self.forest.filter(question, False)
            if len(self.forest.liste) == 1:
                print(self.forest.liste[0])
        print(count)


if __name__ == "__main__":
    eval = Evaluator("conll_for_micha.conll", "conll_gold.conll")
    eval.evaluate()
