import subprocess

def run_and_return(*args):
  proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  return proc.stdout.read()

def out(outfile, *args):
  subprocess.call(args, stdout=outfile, stderr=subprocess.STDOUT)