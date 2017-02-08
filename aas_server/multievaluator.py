import os
import subprocess
import evaluator
for i in list(range(10, 100, 10))+list(range(100, 1001, 100)):
    for file in sorted(os.listdir("/proj/staniek/NBest/CreateTestdata/parseddata/"), key=lambda x: int(x.split('.')[0])):
        parsedpath="/proj/staniek/NBest/CreateTestdata/parseddata/"+file
        goldpath="/proj/staniek/NBest/CreateTestdata/golddata/"+file
        evalu=evaluator.Evaluator(parsedpath, goldpath, nbest=i)
        evalu.evaluate()