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


def mk_log_dir():
    log_files_dir_path = r'./log_files/temp_data'
    os.makedirs(log_files_dir_path, exist_ok=True)

