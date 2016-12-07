import os
import subprocess
import evaluator
for file in os.listdir("/proj/staniek/NBest/CreateTestdata/parseddata/"):
    parsedpath="/proj/staniek/NBest/CreateTestdata/parseddata/"+file
    goldpath="/proj/staniek/NBest/CreateTestdata/golddata/"+file
    evalu=evaluator.Evaluator(parsedpath, goldpath)
    evalu.evaluate()