import sublime, sublime_plugin

class GitGutterCommand(sublime_plugin.TextCommand):
  def run(self, edit):

    self.lines_removed([6,7,8])
    self.lines_added([9,10])
    self.lines_modified([11,12])


  def lines_to_regions(self, lines):
    regions = []
    for line in lines:
      position = self.view.text_point(line-1, 0)
      region   = sublime.Region(position,position)
      regions.append(region)
    return regions

  def lines_removed(self, lines):
    regions = self.lines_to_regions(lines)
    scope   = "markup.deleted"
    icon    = 'bookmark'
    self.view.add_regions('deleted', regions, scope, icon)

  def lines_added(self, lines):
    regions = self.lines_to_regions(lines)
    scope   = "markup.inserted"
    icon    = 'bookmark'
    self.view.add_regions('inserted', regions, scope, icon)

  def lines_modified(self, lines):
    regions = self.lines_to_regions(lines)
    scope   = "markup.changed"
    icon    = 'bookmark'
    self.view.add_regions('changed', regions, scope, icon)
