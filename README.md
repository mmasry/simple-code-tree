# simple-code-tree

A simple code tree parser that recursively explores a directory of C/CPP files and tries to figure out what includes what.  It also does LLOC counts for each file.
It can't resolve project files at the momment, so assumes that filenames are unique.

```Python
import codetree

# create a source dictionary
d = codetree.create_code_dictionary("c:\\sourcedir", ["exclude-paths-with-this-string"])

# print the lloc for a specific file
print(d["file.cpp"].lloc)

# find all includes that are only included by their own cpp
l = find_strays(d)
```
