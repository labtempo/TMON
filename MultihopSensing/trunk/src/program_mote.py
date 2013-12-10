'''
Easier mote installation and maintenance.
'''
import sys, os, re
from SharedLibs.tools import execCmd

TOSROOT = os.environ["TOSROOT"]
PLATFORM = 'iris'
USB_COMMUNICATION = 3
slot = 0

DEFAULT_MAKE_CMD = "make %s" % (PLATFORM)
MULTIHOPSENSING_MAKE_CMD = "SENSORBOARD=mda100 %s" % (DEFAULT_MAKE_CMD)

GOLDEN_IMAGE_PATH = "%s/apps/tests/deluge/GoldenImage" % (TOSROOT)
MULTIHOPSENSING_PATH = "/home/giulio/workspace/MultihopSensing/src"

DEFAULT_UPLOAD_CMD = "tos-deluge serial@/dev/ttyUSB%d:57600 -i %d %s/build/%s/tos_image.xml"
UPLOAD_GOLDEN_IMAGE = DEFAULT_UPLOAD_CMD % (USB_COMMUNICATION, slot, GOLDEN_IMAGE_PATH, PLATFORM)
slot +=1
UPLOAD_MULTIHOPSENSING = DEFAULT_UPLOAD_CMD % (USB_COMMUNICATION, slot, MULTIHOPSENSING_PATH, PLATFORM)
slot +=1


def print_cmd(cmd, msg, result):
    print "*" * 30
    print msg
    print "*" * 30
    print ">>", cmd
    print result    


def run_cmd(cmd, msg):
    result = execCmd(cmd.split())
    print_cmd(cmd, msg, result)
    return result


def compile_golden_image():
    os.chdir(GOLDEN_IMAGE_PATH)        
    result = run_cmd(DEFAULT_MAKE_CMD, "Compiling Golden Image") 


def compile_multihopsensing_image():
    os.chdir(MULTIHOPSENSING_PATH)        
    result = run_cmd(MULTIHOPSENSING_MAKE_CMD, "Compiling MultihopSensing Image") 


def upload_golden_image():    
    result = run_cmd(UPLOAD_GOLDEN_IMAGE, "Installing Golden Image")    
    return True


def upload_multihopsensing():    
    result = run_cmd(UPLOAD_MULTIHOPSENSING, "Installing MultihopSensing")        
    return True


def setup_deluge():
    compile_golden_image()
    compile_multihopsensing_image()
    
    if upload_golden_image():
        upload_multihopsensing()


def main(args):
    if len(args) < 2:
        print "python %s [setup_deluge]" % (args[0])
        exit()
        
    command = args[1].strip()
    if command == "setup_deluge":
        setup_deluge()
    else:
        print "Unrecognized command"
        exit()


if __name__ == "__main__":
    main(sys.argv)