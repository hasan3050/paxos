import sys;
import os;
import re;

def process_argv(argv):
    options = {};
    while argv:
        if argv[0].find('--',0,2) != -1:
            options[argv[0][2:]] = argv[1];
        elif argv[0].find('-',0,1) != -1:
            options[argv[0][1:]] = argv[1];
        argv = argv[1:];
    return options;
def is_valid_ip(ip):
    if re.match(r'^((\d{1,2}|1\d{2}|2[0-4]\d|25[0-5])\.){3}(\d{1,2}|1\d{2}|2[0-4]\d|25[0-5])$', ip):
        return True;
    else:
        return False;