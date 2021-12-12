
MAIN_INIT_CMDS = [
    'echo "On the main pi, initting main"',
    'cd Desktop/PenO3-CW4A1/programs/non_multi_threaded',
    'python3 main_v9.py']

HELPER_INIT_CMDS = [
    'echo "On the main pi, initting main"', 
    'cd Desktop/PenO3-CW4A1/venv/bin',
    'source activate',
    'cd ../../programs/non_multi_threaded',
    'python3 helper_v6.py']

def gen_command_files(maincmds, helpercmds, use_keypnt, res, blend_frac, x_t, pc_ip):
    import os.path
    CURRENT_DIR = str(os.path.dirname(os.path.realpath(__file__))).replace("\\", "/")
    DIRS = CURRENT_DIR.split("/")
    for i, s in enumerate(DIRS):
        if s == "PenO3-CW4A1":
            REPO_ROOT = "/".join(DIRS[:i+1])
    CMD_FILE_SAVE_DIR = REPO_ROOT + "/programs/non_multi_threaded/"
    print(CMD_FILE_SAVE_DIR)

    sp = '" "'
    argstr = ' "' +  str(use_keypnt) + sp + str(res[0])+","+str(res[1]) + sp + str(blend_frac) + sp + str(x_t) + sp + pc_ip + '"'
    
    maincmds[-1] += argstr
    maincmds = [x+'\n' for x in maincmds]
    with open(CMD_FILE_SAVE_DIR + 'main_init2.txt', mode='w') as f:
        f.writelines(maincmds)

    helpercmds[-1] += argstr
    helpercmds = [x + '\n' for x in helpercmds]
    with open(CMD_FILE_SAVE_DIR + 'helper_init2.txt', mode='w') as f:
        f.writelines(helpercmds)


