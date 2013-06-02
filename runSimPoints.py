"""
   Takes simpoints metadata and initiates marss86 to simulate each simpoint for benchmark
   	Assumptions:
		- simpoint interval is 100 M
		- checkpoints are already created for SPEC CPU 2006 INT benchmarks 
		- checkpoints wer created using -m 4096 flag
		- qemu img filename is ubunty-natty.qcow2 
			
	Arguments:
		- simconfig file name
		- benchmark name
		- array of simpoints
		- output path		
"""

#harcodeded paths
MARSS_PATH="/home/jerry/marss.dramsim"
MARSS_QEMU_PATH="/home/jerry/marss.dramsim/qemu"
MARSS_IMG_PATH="/home/jerry/marss.dramsim/img"
SIMCONFIG_PATH="/home/jerry/marss.dramsim/machines"

#simconfig prefixes
FAST_FWD_PREFIX="-fast-fwd-user-insns "
STATS_FILE_PREFIX="-yamlstats "
LOG_FILE_PREFIX="-logfile "

simpoints = []

import os, sys
import fileinput
import subprocess
import argparse
#parse input parameters
def processOptions():
  
  argparser = argparse.ArgumentParser(description= \
      "Parse arguments for marss simulation of simpoints")

  input_group = argparser.add_argument_group('Input')
  input_group.add_argument('--simconfig_filename', required=True, metavar='FILE',
      help='simconfig file name.')
  input_group.add_argument('--benchmark', required=True, metavar='BENCH',
      help='Name of specint 06  benchmark to simulate',
      choices =['astar','bzip2','gcc','gobmk','hmmer','h264ref','libquantum','mcf','omnetpp','perlbench','sjeng','xalancbmk'])
  input_group.add_argument('--simpoints', required=True, nargs='+',type=int, metavar='ARR',
      help='Array of simpoints to simulate')
  input_group.add_argument('--out_path', required=True, metavar='DIR',
                           help='Output path')
                         
  args = argparser.parse_args()
  return args

"""
update simconfig file for
	- fast fwd instructions
	- statsfile path
	- logfile path 
""" 
def updatesimconfig(simpoint,simconfigfile,outdir):

  #part 1: fast forward instructions 
  fastfwd = simpoint+"00000000\n" #simpoint x 100M to get number of insns to fast foward 
  fastfwd_line = FAST_FWD_PREFIX + str(fastfwd) 
    

  #part2: stats file path

  if not os.path.isdir(outdir): #sanity check
   sys.exit("Invalid output directory\n")  
  outfile = simpoint+".stats\n"
  outfile = os.path.join(outdir,outfile) 
  out_line = STATS_FILE_PREFIX+outfile

 
  #part 3
  logfile = simpoint+".log\n" 
  logfile = os.path.join(outdir,logfile)
  log_line = LOG_FILE_PREFIX+logfile



  #putting it all together
  try:
    for line in fileinput.input(simconfigfile,inplace=1):
      if line.startswith(FAST_FWD_PREFIX):
        line = line.replace(line,fastfwd_line)
      elif line.startswith(STATS_FILE_PREFIX):
         line = line.replace(line,out_line)
      elif line.startswith(LOG_FILE_PREFIX):
          line = line.replace(line,log_line)
      sys.stdout.write(line)
  except:
    sys.exit("could not update simconfig file: ", simconfig)



def runmarss(simpoint,simconfig,benchmark,outdir):
  filename ="marsslog_"+simpoint+".log"
  filename = os.path.join(outdir,filename)
  statusFile = open(filename,'w')
  marsspath = os.path.join(MARSS_QEMU_PATH,"qemu-system-x86_64")
  imgpath = os.path.join(MARSS_IMG_PATH,"ubuntu-natty.qcow2")
  drive_str = "cache=unsafe,"+"file="+imgpath 

  print drive_str, " ", marsspath
  try:
    marss86Run = subprocess.Popen([marsspath,"-simconfig", simconfig, "-m", "4096","-drive",drive_str,"-loadvm", benchmark],\
     		stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in marss86Run.stdout:
      #TODO: Check for local ip of vnc or terminal viewer, and launch process to view running of simulation 
      statusFile.write(line)
      marss86Run.wait()
    statusFile.close()
  except:
    print("Could not run marss86 for simpoint: ", simpoint)


#main function
if __name__ == "__main__":
  args = processOptions()
  simconfig = os.path.join(SIMCONFIG_PATH,args.simconfig_filename)   
  if len(args.simpoints) == 0:
    sys.exit("No simpoints passed")

  #first, move to MARSS_PATH dir because qemu has some dependecies (i.e. bios.bin) whose paths are hardcoded based on the installation path
  os.chdir(MARSS_PATH) #this path should be asserted. hardcode it
  
  for i in range(0,len(args.simpoints)):
    #build simconfig file path 
    simconfig = os.path.join(SIMCONFIG_PATH,args.simconfig_filename)
    if not os.path.isfile(simconfig):
      sys.exit("Invalid path for simconfig file")

    #update simconfig file to fast forward insns and change log and yaml out files for current simpoint   
    updatesimconfig(str(args.simpoints[i]), simconfig,args.out_path)
    
    #run mars for this checkpoint
    runmarss(str(args.simpoints[i]),simconfig,str(args.benchmark),args.out_path) 

#done
