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

def mk_ds_dir():
    dir_path_list = [r'./dataset', r'./dataset/files', r'./dataset/metadata']
    for dir_path in dir_path_list:
        os.makedirs(dir_path, exist_ok=True)

def mk_temp_dir():
    temp_data_dir = r'./temp_data'
    os.makedirs(temp_data_dir, exist_ok=True)