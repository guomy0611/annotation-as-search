'''
Class containing a Evaluator class which automates
the question answering by looking up the correct
answer in a gold parse.
'''
import tree, sys

class Evaluator(object):
    '''
    Class to automatically answer questions given a file with
    kbest parses and a file containing the goldparse.
    '''
    def __init__(self, file_with_kbest, goldfile, nbest=1000):
        '''
        Initialize the object
        '''
        self.file_with_kbest = file_with_kbest
        self.goldfile = goldfile
        self.nbest=nbest
        self.initialize()
    def initialize(self):
        '''
        Read the files and construct Tree and Forest objects.
        Gets called by __init__
        '''
        self.goldtree = tree.Tree(8, 10)
        for line in open(self.goldfile):
            if line != "\n":
                self.goldtree.add(line)
        self.forest = tree.Forest()
        temptree = tree.Tree(9, 11)
        count=0
        for line in open(self.file_with_kbest):
            if line == "\n":
                self.forest.add(temptree)
                count+=1
                temptree = tree.Tree(9, 11)
                if count > self.nbest: break
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
        while len(self.forest.trees) != 1:
            count += 1
            question = self.forest.question()
            if question in self.goldtree.get():
                self.forest.filter(question, True)
            else:
                self.forest.filter(question, False)
            if len(self.forest.trees) == 1:
                break
            if len(self.forest.trees)==0:
                print(self.nbest, len(self.goldtree.get()), #Number of tokens 
		      count, 0, len(self.goldtree.get()), 1, 1, self.goldfile.split(".")[0].split("/")[-1]) 
		#how many guesses, Labeled attachment count, number of edits, countvariable, error
        print(self.nbest, len(self.goldtree.get()), count, #Tokennumber and number of guesses
                self.forest.trees[0].overlap(self.goldtree), #Labaled Attachment Count
                len(self.goldtree.get())-self.forest.trees[0].overlap(self.goldtree), #Minimum Edit Distance
                1, 0, self.goldfile.split(".")[0].split("/")[-1]) #1 to later know the length, 0 meaning 0 errors


if __name__ == "__main__":
    evaluator = Evaluator(sys.argv[1], sys.argv[2])
    evaluator.evaluate()
