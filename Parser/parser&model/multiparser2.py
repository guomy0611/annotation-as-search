import os, subprocess

for file in os.listdir("/proj/staniek/NBest/CreateTestdata/traindata2/"):
    filepath=("/proj/staniek/NBest/CreateTestdata/traindata2/"+file)
    print("./Parser3 %s %s"%(filepath, filepath.replace("traindata2", "parseddata2")))
    subprocess.call("./Parser3 %s %s"%(filepath, filepath.replace("traindata2", "parseddata2")), shell=True)
