# simple-code-tree

A simple code tree parser that recursively explores a directory of C/CPP files and tries to figure out what includes what.  It also does LLOC counts for each file.
It can't resolve project files at the momment, so assumes that filenames are unique.

,,,Python
# create a source dictionary
d = codetree.create_code_dictionary("c:\\sourcedirectory", ["exclude-paths-with-this-string"])

# look at the attributes for a specific file
print(d["file.cpp"].lloc)

# find all the includes that are only included by a c/cpp with the same name
l = find_strays(d)
,,,
