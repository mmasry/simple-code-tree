# simple-code-tree

A simple code tree parser that recursively explores a directory of C/CPP files and tries to figure out what includes what.  It also does LLOC counts for each file.
It can't resolve project files at the momment, so assumes that filenames are unique.

```Python
d = codetree.create_code_dictionary("c:\\sourcedirectory", ["exclude-paths-with-this-string"])
print(d["file.cpp"].lloc)
l = find_strays(d)
```
