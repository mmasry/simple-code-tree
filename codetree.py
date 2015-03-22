import os
import re

headerExtensions = [".h", ".hpp"]
sourceExtensions = headerExtensions + [ ".cpp", ".c", ".cxx"]

class SourceInfo:
    name = ""
    fullPath = ""

    lloc = 0
    includeList = []
    includedByList = []

def get_immediate_subdirectories(dir):
    return [ os.path.join(dir,name) for name in os.listdir(dir)
            if os.path.isdir(os.path.join(dir, name))]
 
def get_all_subdirectories(dir, extensions):
    from os.path import join, getsize
    for root, dirs, files in os.walk(path):
        print(root, "consumes", end=" ")
        print(sum(getsize(join(root, name)) for name in files), end=" ")
        print("bytes in", len(files), "non-directory files")
        if 'svn' in dirs:
            dirs.remove('svn')  # don't visit SVN directories

def find_extensions(files, extensions):
    return [ name for name in files if os.path.splitext(name)[1] in extensions]

def remove_strings(stringList, excludes):
    """
    Removes strings containing exclude substrings from a list

    :param list stringList: the list of strings
    :param list excludes: the list of exclusion substrings
    :returns list: a list of all the strings in stringList that do not contain the
        exlcusion substrings
    """
    
    outList = []
    for s in stringList:
        for e in excludes:
            if e in s:
                break
        else:
            outList.append(s)
    return outList
    
    
def find_files(path, extensions, excludes = []):
    """
    Finds all files in the path with a specified set of extensions (recursive).

    :param str path: the path
    :param list extensions: a list of filename extensions to include
    :param list excludes: an optional list of strings. File paths that contain the
        extension strings will be excluded.
    :returns list: a list of all files (full path) with the specified extensions.
    """
    
    from os.path import join, getsize
    
    fileList = []
    for root, dirs, files in os.walk(path):
        newFiles = [ name for name in files if os.path.splitext(name)[1] in extensions]
        fileList.extend([join(root,name) for name in newFiles] )

    fileList = remove_strings(fileList, excludes)
    return fileList

def get_filename_from_string(path, lower=True):
    """
    Extracts the filename from a path string

    :param str path:  the path
    :returns str: the filename (name+extension) string
    """
    
    prog = re.compile('[a-zA-Z0-9_]+[.][a-zA-Z0-9_]+')
    match = prog.search(path)
    if match is not None:
        if lower == True:
            return match.group().lower()
        else:
            return match.group()
    else:
        return None

def extract_includes(file):
    """
    Finds the includes in a source file file by looking for #include lines.
    Leading whitespace is ignored.

    :param string file: the filename
    :returns list: a list of files (filename only) included in the file
    """
    count = 0
    includeList = [];

    # have to wrap this in a try-catch block to catch
    # unicode issues
    try: 
        with open(file, 'r') as f:
            for s in f:
                s = s.strip()
                if s.startswith("#include"):
                    count = count + 1
                    headerName = get_filename_from_string(s)
                    if headerName is not None:
                        includeList.append(headerName)
    except UnicodeDecodeError:
        f.closed
        print("Ignored", file, "[unicode error]")
        return [];

    f.closed
    return includeList

def create_empty_source_dictionary(sourcePathList):
    """
    Creates an empty dictionary from a list of source files.  Hashing is done
    on the filename (w/ extension) only, not the full path.

    :param list sourceList: a list of source files (full path)
    :returns dictionary: an empty, initialized source dictionary
    """
    
    source_dictionary = {}
    for sourcePath in sourcePathList:
        # prepare a structure for the header
        struct = SourceInfo()
        struct.pathName = sourcePath
        struct.count = 0
        struct.occurences = []
              
        #extract just the header's name, no extension, from the path
        sourceFile = get_filename_from_string(sourcePath)
        fileName, fileExt = os.path.splitext(sourceFile)

        struct.name = fileName

        #hash on the header name (including exetnsion)
        source_dictionary[sourceFile] = struct
        
    return source_dictionary

def update_source_dictionary(path, sourceDict):
    """
    Update the source dictionary by processing a new source file.  Updates are
    done in place.

    :param string path: The path to the source file
    :param dictionary sourceDict: the source dictionary.
    """

    includeHeaderList = extract_includes(path)
    if includeHeaderList == []:
        return
 
    # get the file name (no extension) for the file that contained the includes
    fileName = get_filename_from_string(path)

    try:
        filePrefix, fileExt = os.path.splitext(fileName)
    except AttributeError:
        print("Ignored", path, "[attribute error]")
        return

    # update the stats for each included header
    for includedFile in includeHeaderList:
        #print(includedFile)
        # assign this to a dictionary
        sourceStruct = sourceDict.get(includedFile)

        # don't increment the count if the filename is the same as
        # the header name (e.g. if the include is referenced in the
        # corresponding c file
        if sourceStruct is not None and sourceStruct.name != filePrefix:
            sourceStruct.count = sourceStruct.count+1
            sourceStruct.occurences.append(path)
            sourceDict[includedFile] = sourceStruct
    

def create_source_dictionary(dirName, excludes = []):
    """
    Searches through a directory (recursive) looking for relationships between 
    headers and cpp files.  Stores these relationships in a dictionary hashed on
    the filename. 
    
    :param string dirName: The directory to search for source files
    :param list excludes: Paths or filenames containing these strings will be excluded.
        Useful for removing directories named *test*, for example.
    :returns dict: A dictionary hashed on the filename. Entries are of type SourceInfo
    """

    # find all the headers in the directory (full paths)
    sourcePaths = find_files(dirName, sourceExtensions, excludes)

    # create the header dictionary from the list of header files
    if len(sourcePaths)==0:
        return

    sourceDict = create_empty_source_dictionary(sourcePaths)
 
    # we're going to look through all of the header and code files
    # for includes of each header file name in the file and update the
    # info for each header file in the dictionary
    for file in sourcePaths:
        update_source_dictionary(file, sourceDict)

    return sourceDict           

def find_strays(dictionary):
    """
    Looks through the source dictionary for occurences of strays: a header not 
    included by anything other than an identically named cpp file, and the cpp
    file itself.

    :param dict dictionary: the source dictionary
    :returns list: the list of stray headers and cpp paths, sorted by path
    """

    num_includes = 1
    
    # find strays and append to the list
    itemList = []
    for val in dictionary.values():
        itemList.append(val)

    # sort the list by pathname
    l= sorted(itemList, key = lambda x: (x.count, x.pathName) )  

    count = 0
    for o in l:
        if o.count == num_includes:
            print(o.pathName,"->",o.occurences)
            count=count+1

    print(count," stray headers out of ",len(l)," [",round(count/len(l)*100,2),"%]",sep='')
    return
    
