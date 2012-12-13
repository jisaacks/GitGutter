import git_helper
import sublime
import subprocess
import re
from view_collection import ViewCollection

class GitGutterHandler:
  def __init__(self, view):
    self.view = view
    self.git_temp_file = ViewCollection.git_tmp_file(self.view)
    self.buf_temp_file = ViewCollection.buf_tmp_file(self.view)
    if self.on_disk():
      self.git_tree = git_helper.git_tree(self.view)
      self.git_dir  = git_helper.git_dir(self.git_tree)
      self.git_path = git_helper.git_file_path(self.view, self.git_tree)

  def on_disk(self):
    # if the view is saved to disk
    return self.view.file_name() != None

  def reset(self):
    if self.on_disk() and self.git_path:
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
    # the git repo won't change that often
    # so we can easily wait 5 seconds
    # between updates for performance
    if ViewCollection.git_time(self.view) > 5:
      self.git_temp_file.truncate()
      args = ['git','--git-dir='+self.git_dir,'--work-tree='+self.git_tree,'show','HEAD:'+self.git_path]
      try:
        subprocess.call(args, stdout=self.git_temp_file)
        ViewCollection.update_git_time(self.view)
      except Exception:
        pass

  def process_diff(self,diff_str):
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

      if kind == 'c':
        modified += range(line_start,line_end+1)
      elif kind == 'a':
        inserted += range(line_start,line_end+1)
      elif kind == 'd':
        if line == 1:
          deleted.append(line_start)
        else:
          deleted.append(line_start+1)

    return (inserted, modified, deleted)

  def diff(self):
    if self.on_disk() and self.git_path:
      self.update_git_file()
      self.update_buf_file()

      args = ['diff',self.git_temp_file.name,self.buf_temp_file.name]
      proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
      results = proc.stdout.read()

      return self.process_diff(results)
    else:
      return ([],[],[])
