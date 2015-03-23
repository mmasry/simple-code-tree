import os
import re

HEADER_EXTENSIONS = [".h", ".hpp"]
SOURCE_EXTENSIONS = HEADER_EXTENSIONS + [ ".cpp", ".c", ".cxx"]

class SourceInfo:
    def __init__(self):
        self.name = ""
        self.prefix = ""
        self.extension = ""
        self.path = ""
        self.line_count = 0
        self.includeList = []
        self.includedByCount = 0
        self.includedByList = []
        
class FileInfo:
    def __init__(self):
        self.line_count = 0
        self.included_files = []        


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

def process_file(file_path):
    """
    Finds the includes in a source file file by looking for #include lines.
    Leading whitespace is ignored.  Also does a line count for non-comment
    lines

    :param string file_path: the file path
    :returns FileInfo: a class that stores the list of includes and the line count
    """
    file_info = FileInfo()

    # have to wrap this in a try-catch block to catch
    # unicode issues
    count = 0

    try: 
        with open(file_path, 'r') as f:
            for s in f:
                # count the lines
                count = count + s.count(';')
                
                # find the includes
                s = s.strip()
                if s.startswith("#include"):
                    headerName = get_filename_from_string(s)
                    if headerName is not None:
                        file_info.included_files.append(headerName)

    except UnicodeDecodeError:
        print("Ignored", file_path, "[unicode error]")

    f.closed                        
    file_info.line_count = count

    return file_info

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

def update_source_dictionary(source_dictionary, file_path):
    """
    Update the source dictionary by processing a new source file.  Updates are
    done in place.

    :param string path: The path to the source file
    :param dictionary source_dictionary: the source dictionary.
    """

    file_info = process_file(file_path)
    if file_info.included_files == []:
        return

    # get the file name (no extension) for the file that contained the includes
    file_name = os.path.basename(file_path)

    sourceStruct = source_dictionary.get(file_name)
    if sourceStruct is None:
        return

    sourceStruct.includeList = file_info.included_files
    sourceStruct.line_count = file_info.line_count

    # update the stats for each included header
    for f in file_info.included_files:
    
        # assign this to a dictionary
        include_struct = source_dictionary.get(f)

        # don't increment the count if the filename is the same as
        # the header name (e.g. if the include is referenced in the
        # corresponding c file
        if include_struct is not None:
            include_struct.includedByList.append(file_name)
        
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

    # update the convenience count
    for val in source_dictionary.values():
        val.includedByCount = len(val.includedByList)

    return source_dictionary           

def find_strays(source_dictionary):
    """
    Looks through the source dictionary for occurences of strays: a header not 
    included by anything other than an identically named cpp file, and the cpp
    file itself.

    :param dict source_dictionary: the source dictionary created by create_source_dictionary
    :returns list: the list of stray headers and cpp paths, sorted by path
    """

    # find strays and append to the list
    itemList = []
    for val in source_dictionary.values():
        itemList.append(val)

    # sort the list by pathname
    l= sorted(itemList, key = lambda x: (x.includedByCount, x.path) )  

    count = 0
    line_count = 0
    total_line_count = 0

    for o in l:
        # keep track of all lines
        total_line_count = total_line_count + o.line_count

        if o.includedByCount == 1 and source_dictionary[o.includedByList[0]].prefix==o.prefix:
            print(o.path,"->",source_dictionary[o.includedByList[0]].path)
            count=count+2
            
            # add in the strays' line counts
            line_count = line_count + o.line_count + source_dictionary[o.includedByList[0]].line_count

    print(count, " stray files out of ", len(l)," [",round(count/len(l)*100,2),"%]",sep='')
    print(line_count, " stray lloc out of ", total_line_count, " [", round(line_count/total_line_count*100,2),"%]",sep='')

    return l

def test():
    d = create_source_dictionary("c:\\code\\dev-vr-v3", ["stdafx.h", "stdafx.cpp"])
    if d is None:
        return

    find_strays(d)
    
