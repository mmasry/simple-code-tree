import os
import re

HEADER_EXTENSIONS = [".h", ".hpp"]
SOURCE_EXTENSIONS = HEADER_EXTENSIONS + [ ".cpp", ".c", ".cxx"]

class SourceInfo:
    name = ""
    prefix = ""
    extension = ""
    path = ""
    lloc = 0
    includeList = []
    includedByList = []

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
    
def get_immediate_subdirectories(dir_path):
    """
    Returns the immediate subdirectories of the given directory. 

    :param str dir_path: a directory path string
    :returns list: a list of subdiretory path strings
    """

    return [ os.path.join(dir_path,name) for name in os.listdir(dir)
            if os.path.isdir(os.path.join(dir_path, name))]
 
def print_subdir_info(dir_path, excludes):
    """
    Prints information in subdirectories
    :param str dir_path: a directory path string
    :param list excludes: a list of directory names (e.g. "svn") to avoid visiting
    """

    from os.path import join, getsize

    for root, dirs, files in os.walk(dir_path):
        dirs.remove(excludes)  # don't visit excluded directories
        print(root, "consumes", end=" ")
        print(sum(getsize(join(root, name)) for name in files), end=" ")
        print("bytes in", len(files), "non-directory files")
        

def find_extensions(files, extensions):
    return [ name for name in files if os.path.splitext(name)[1] in extensions]

def remove_strings(strings, excludes):
    """
    Removes strings containing exclude substrings from a list

    :param list strings: the list of strings
    :param list excludes: the list of exclusion substrings
    :returns list: a list of all the everything in strings that doesn't contain the 
        exlcusion substrings
    """
    
    outList = []
    for s in strings:
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

def create_empty_source_dictionary(source_paths):
    """
    Creates an empty dictionary from a list of source files.  Hashing is done
    on the filename (w/ extension) only, not the full path.

    :param list source_paths: a list of source files (full path)
    :returns source_dictionary: an empty, initialized source dictionary
    """
    
    source_dictionary = {}
    for sourcePath in source_paths:
       
        sourceFile = os.path.basename(sourcePath)
        filePrefix, fileExt = os.path.splitext(sourceFile)

        # prepare a structure for the header
        struct = SourceInfo()
        struct.path = sourcePath
        struct.name = sourceFile
        struct.prefix = filePrefix
        struct.extension = fileExt

        #hash on the header name (including exetnsion)
        source_dictionary[sourceFile] = struct
        
    return source_dictionary

def update_source_dictionary(source_dictionary, path):
    """
    Update the source dictionary by processing a new source file.  Updates are
    done in place.

    :param string path: The path to the source file
    :param dictionary source_dictionary: the source dictionary.
    """

    included_files = extract_includes(path)
    if included_files == []:
        return

    # get the file name (no extension) for the file that contained the includes
    sourceFile = os.path.basename(path)

    try:
        fileName, fileExt = os.path.splitext(sourceFile)
    except AttributeError:
        print("Ignored", path, "[attribute error]")
        return

    sourceStruct = source_dictionary.get(sourceFile)
    if sourceStruct is None:
        return

    # update the stats for each included header
    for includeFile in included_files:
        sourceStruct.includeList.append(includeFile)

        # assign this to a dictionary
        includeStruct = source_dictionary.get(includeFile)

        # don't increment the count if the filename is the same as
        # the header name (e.g. if the include is referenced in the
        # corresponding c file
        if includeStruct is not None:
            includeStruct.includedByList.append(path)
        
        #source_dictionary[includeFile] = includeStruct

    #source_dictionary[sourceFile] = sourceStruct

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
    path_list = find_files(dirName, SOURCE_EXTENSIONS, excludes)

    # create the header dictionary from the list of header files
    if len(path_list)==0:
        return

    source_dictionary = create_empty_source_dictionary(path_list)
 
    # we're going to look through all of the header and code files
    # for includes of each header file name in the file and update the
    # info for each header file in the dictionary
    for file in path_list:
         update_source_dictionary(source_dictionary, file)

    return source_dictionary           

def find_strays(source_dictionary):
    """
    Looks through the source dictionary for occurences of strays: a header not 
    included by anything other than an identically named cpp file, and the cpp
    file itself.

    :param dict source_dictionary: the source dictionary created by create_source_dictionary
    :returns list: the list of stray headers and cpp paths, sorted by path
    """

    NUM_INCLUDES = 0
    
    # find strays and append to the list
    itemList = []
    for val in source_dictionary.values():
        itemList.append(val)

    # sort the list by pathname
    l= sorted(itemList, key = lambda x: (x.count, x.pathName) )  

    count = 0
    for o in l:
        if o.count == NUM_INCLUDES:
            print(o.pathName,"->",o.occurences)
            count=count+1

    print(count," stray headers out of ",len(l)," [",round(count/len(l)*100,2),"%]",sep='')
    return l

def test():
    d = create_source_dictionary("d:\\code\\dev-vr-v3\\core")
    find_strays(d)
    
