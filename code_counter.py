# Module that counts non-comment lines of code
# This is best approximated by counting the number of ;
import os
import sys


def countLinesOfCodeInDir(path):
    names = []
    count = 0
    fileCount = 0
    print "Processing, counting .h,.c,.cpp files, counting ; in files"
    for root, dirs, files in os.walk(path):
        for name in files:
            if name.endswith('.h') or name.endswith('.cpp') or name.endswith('.c'):
		currF = open(os.path.join(root,name),'r')
                fileCount = fileCount + 1		
		for line in currF:
                    count = count + line.count(';')
    print "Number of Source Files:", fileCount
    print "Number of LOC:", count


############################################################
#Main script
if len(sys.argv) < 2:
    print "Enter directory path for source code!"
    path = ""
else:
    path = sys.argv[1]

if not os.path.isdir(path):
    print "Invalid directory path"
    exit

countLinesOfCodeInDir(path)



