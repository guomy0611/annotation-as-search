import os, subprocess

for file in os.listdir("/proj/staniek/NBest/CreateTestdata/traindata3/"):
    filepath=("/proj/staniek/NBest/CreateTestdata/traindata3/"+file)
    print("./Parser4 %s %s"%(filepath, filepath.replace("traindata3", "parseddata3")))
    subprocess.call("./Parser4 %s %s"%(filepath, filepath.replace("traindata3", "parseddata3")), shell=True)
