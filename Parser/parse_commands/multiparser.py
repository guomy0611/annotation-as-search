import os, subprocess

for file in os.listdir("/proj/staniek/NBest/CreateTestdata/traindata/"):
    filepath=("/proj/staniek/NBest/CreateTestdata/traindata/"+file)
    print("./Parser2 %s %s"%(filepath, filepath.replace("traindata", "parseddata")))
    subprocess.call("./Parser2 %s %s"%(filepath, filepath.replace("traindata", "parseddata")), shell=True)
