import os, sys
import subprocess
import argparse

"""
#Python script to process marss86 yaml stats file to McPat to generate power and area statistics
	 - xml file with configurations for processor is already available 
 	 - yaml stats file(s) from marss86 simulation(s) is/are available 
 	 
       Script take yaml stats file along with configuration xml file, process it through marss2mcpat.py, 
       generates temp.xml and input temp.xml to mcpat binary to output power and area numbers
"""
# Can process single or multiple marss86 yaml stats files
# All stats files in a directory must end with the '.stats' extension'

#hardcoded paths to marss2mcpat and mcpat binary
MARSS_2_MCPAT_PATH = "/home/prism/marss.dramsim/scripts/marss2mcpat.py" 
MCPAT_PATH = "/home/prism/mcpat/mcpat"

"""
 Arguments:
    --num_core # Number of cores simulated
     --cpu_mode # Mode to collect [kernel, user, total]
     --freq # Processor frequency 
     --machine # OoO or In-Order
     --xml_in machine confiuration
     --marss Path to marss file(s)      
     --out  Path to output power file(s)    
"""
simStats = list() #global var of lis of marss files to process


def processOptions():

  argparser = argparse.ArgumentParser(description= \
      "Parse Marss results to mcpat input")

  input_group = argparser.add_argument_group('Input')
  input_group.add_argument('--marss', required=True, metavar='FILE/DIR',
      help='Statistics output by a MARSS simulation run')
  input_group.add_argument('--xml_in', required=True, metavar='FILE',
      help='McPAT configuration for a processor')
  input_group.add_argument('--cpu_mode', required=True, metavar='MODE',
      help='Mode for stats {user, kernel, total}',
      choices=['user', 'kernel', 'total'])
  input_group.add_argument('--num_core', required=True, metavar='NCORE',
                           help='Number of cores')
  input_group.add_argument('--freq', required=True, metavar='FREQ',
                           help='Clock rate',
                           choices=['1000', '1600','2000', '3333', '4000'])
  input_group.add_argument('--machine', required=True, metavar='TYPE',
                           help='Machine type (ooo 0; inorder 1)',
                           choices=['0', '1'])
  input_group.add_argument('--out', required=True, metavar='DIR',
                           help='Directory of output power file(s)')
                          
  args = argparser.parse_args()
  return args


def fillSimStats(BENCH_PATH):
  if os.path.isfile(BENCH_PATH):
    simStats.append(BENCH_PATH)
  elif os.path.isdir(BENCH_PATH):
    for filename in os.listdir(BENCH_PATH): 
      if filename.endswith(".stats"): 
        simStats.append(filename)
  else:
    print "Invalid marss stat files\n"
    sys.exit(-1)

#Main function 


def processFiles(BENCH_PATH,cpu_mode,num_core,freq,machine,xml_in,OUTPUT_PATH):


  #remove any outstanding temp.xml
  if os.path.isfile("temp.xml"):
    os.remove("temp.xml")
  #for each file in simStats, call marss2mcpat to createe temp.xml
  for i in range(0,len(simStats)):
    print "Creating XML for ",  simStats[i]
    try:
      stats = os.path.join(BENCH_PATH,simStats[i])  
      makeXML = subprocess.Popen(["python",str(MARSS_2_MCPAT_PATH), '--cpu_mode', str(cpu_mode), '--num_core', str(num_core),\
      '--freq', str(freq),'--machine',str(machine), '--marss', str(stats), '--xml_in', str(xml_in),  '-o', 'temp.xml']) 
      makeXML.wait()
      #By now, temp.xml is created, now send it to McPat for processing
    except:
      print "Could not call marss2mcpat.py for ", simStats[i]
      #sys.exit(-1)
      continue
    
    #for each temp.xml file create, call mcpat to create power file  
    print "\nCalling mcpath for", simStats[i]
    try:
      outFileName = list()
      temp =  simStats[i].split('/') #hack to remove absolute path in case of single file
      temp = temp[len(temp) -1] 
      outFileName.append(temp.split('.')[0])
      outFileName.append("_power")
      outFileName = ''.join(outFileName)
      outFileName = os.path.join(OUTPUT_PATH,outFileName) 
      outFile = open(outFileName, 'w') 
      makeMcPat = subprocess.Popen([MCPAT_PATH, '-infile','temp.xml','-print_level','1','-opt_for_clk','1'], \
      stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
      for line in makeMcPat.stdout: 
        outFile.write(line)
        makeMcPat.wait()
      outFile.close()
    except:
      print "Coulnd not call Mcpat for ", simStats[i]   
      #sys.exit(-1)

  print "\nComplete\n"

if __name__ == "__main__":
  args = processOptions()
  fillSimStats(args.marss) 
  if len(simStats) == 0:
    print "No stats to process.. Exiting!"
    sys.exit(-1)
 
  processFiles(args.marss,args.cpu_mode,args.num_core,args.freq,args.machine,args.xml_in, args.out)  
