import os
import shutil

currentDir=os.getcwd()
shutil.rmtree(currentDir)
os.mkdir(currentDir)
