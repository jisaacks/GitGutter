import git_helper
import sublime
import subprocess
import tempfile

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
    # TODO: actually parse diff_str to get values below
    inserted = [4,5,6]
    modified = [1,2,3]
    deleted  = [10,12]
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