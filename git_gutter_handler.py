import git_helper
import sublime
import subprocess
import tempfile
import re

class GitGutterHandler:
  def __init__(self, view):
    self.view = view
    self.git_temp_file = tempfile.NamedTemporaryFile()
    self.buf_temp_file = tempfile.NamedTemporaryFile()
    self.git_tree = git_helper.git_tree(self.view)
    self.git_path = git_helper.git_file_path(self.view, self.git_tree)

  def reset(self):
    if self.git_path:
      self.view.run_command('git_gutter')

  def get_git_path(self):
    return self.git_path

  def update_buf_file(self):
    chars = self.view.size() 
    region = sublime.Region(0,chars)
    contents = self.view.substr(region).encode("utf-8")
    f = open(self.buf_temp_file.name,'w')
    f.write(contents)
    f.close()

  def update_git_file(self):
    self.git_temp_file.truncate()
    args = ['git','--git-dir='+self.git_tree+'/.git','--work-tree='+self.git_tree,'show','head:'+self.git_path]
    subprocess.call(args, stdout=self.git_temp_file, stderr=subprocess.STDOUT)

  def process_diff(self,diff_str):
    print diff_str

    inserted = []
    modified = []
    deleted  = []

    lines = diff_str.splitlines()
    for line in lines:
      m = re.match("(\d+),?(\d*)(.)(\d+),?(\d*)", line)
      if not m:
        continue
      kind = m.group(3)
      original_line_start = int(m.group(1))
      if len(m.group(2)) > 0:
        original_line_end = int(m.group(2))
      else:
        original_line_end = original_line_start
      line_start = int(m.group(4))
      if len(m.group(5)) > 0:
        line_end = int(m.group(5))
      else:
        line_end = line_start

      print 'kind: '+kind

      if kind == 'c':
        modified += range(line_start,line_end) + [line_start]
      elif kind == 'a':
        inserted += range(line_start,line_end) + [line_start]
      elif kind == 'd':
        deleted.append(line_start+1)

    print inserted
    print modified
    print deleted

    return (inserted, modified, deleted)

  def diff(self):
    if self.git_path:
      self.update_git_file()
      self.update_buf_file()

      args = ['diff',self.git_temp_file.name,self.buf_temp_file.name]
      proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
      results = proc.stdout.read()

      return self.process_diff(results)
    else:
      return ([],[],[])