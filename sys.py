def run_and_return(*args):
  proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  return proc.stdout.read()