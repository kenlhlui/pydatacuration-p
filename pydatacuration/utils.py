import os
# Export the structure ('tree') of a directory as plain text
def list_files(startpath):
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print('{}{}/'.format(indent, os.path.basename(root)))
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print('{}{}'.format(subindent, f))

# Create a new directory contains log files created
def log_files_dir():
    log_files_dir_path = r'./log_files' 
    if not os.path.exists(log_files_dir_path):
        os.makedirs(log_files_dir_path)
    return log_files_dir_path