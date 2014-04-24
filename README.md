## Git Gutter

A sublime text 2/3 plugin to show an icon in the gutter area indicating whether a line has been inserted, modified or deleted.

### Screenshot:

![screenshot](https://raw.github.com/jisaacks/GitGutter/master/screenshot.png)

### Installation

You can install via [Sublime Package Control](http://wbond.net/sublime_packages/package_control)  
Or you can clone this repo into your *Sublime Text 2/Packages*

*OSX*
```shell
cd ~/Library/Application\ Support/Sublime\ Text\ 2/Packages/
git clone git://github.com/jisaacks/GitGutter.git
```

*Ubuntu*
```shell
cd ~/.config/sublime-text-2/Packages
git clone git://github.com/jisaacks/GitGutter.git
```

*Windows*

GitGutter assumes that the `git` command is available on the command line. If it's not, add the directory containing `git.exe` to your `PATH` environment variable. Then clone the repo:

```dos
cd "%APPDATA%\Sublime Text 2\Packages"
git clone git://github.com/jisaacks/GitGutter.git
```

### Settings
Settings are accessed via the <kbd>Preferences</kbd> > <kbd>Package Settings</kbd> > <kbd>GitGutter</kbd> menu.

Default settings should not be modified, as they are overwritten when GitGutter updates. Instead, you should copy the relevant settings into GitGutter's user settings file.

#### Non Blocking Mode
By default, GitGutter runs in the same thread which can block if it starts to perform slowly. Usually this isn't a problem but depending on the size of your file or repo it can be. If you set `non_blocking` to `true` then GitGutter will run in a seperate thread and will not block. This does cause a slight delay between when you make a modification and when the icons update in the gutter. This is a ***Sublime Text 3 only feature***, ST2 users can turn off live mode if performance is an issue.

#### Debounce Delay
When using non_blocking mode, delay update of gutter icons by the following amount (in milliseconds). Useful for performance issues. Default 1000 (1 second).

#### Live Mode
By default, GitGutter detects changes every time the file is modified. If you experience performance issues you can set it to only run on save by setting `live_mode` to `false`.


#### Untracked Files
GitGutter shows icons for new files and ignored files. These icons will be on everyline. You can toggle the setting `show_markers_on_untracked_file` to turn this feature off. Defaults to true (shows icons). You may need to add scopes to your color scheme (`markup.ignored.git_gutter` and `markup.untracked.git_gutter`) to color the icons.

#### Git path
If git is not in your PATH, you may need to set the `git_binary` setting to the location of the git binary, e.g. in a portable environment;
```json
{
  "git_binary": "E:\\Portable\\git\\bin\\git.exe"
}
```


#### Per-project Settings
Sublime Text supports project-specific settings, allowing `live_mode` to be set differently for different repositories.
To implement, use the <kbd>Project</kbd> > <kbd>Edit Project</kbd> menu and add the `settings` key as shown.
```json
{
    "folders":
    [
        {
            "path": "src"
        }
    ],
    "settings":
    {
        "live_mode": false
    }
}
```

#### Icon Coloring

The colors come from your *color scheme* **.tmTheme** file.

Color schemes that already have support for GitGutter include:

* [Deep Blue See](https://github.com/jisaacks/DeepBlueSee)
* [Flatland](https://github.com/thinkpixellab/flatland)
* [Monokai Extended](https://github.com/jisaacks/sublime-monokai-extended)
* [Perv](https://github.com/jisaacks/Perv-ColorScheme)
* [Tomorrow Theme](https://github.com/chriskempson/tomorrow-theme)
* [Neon Color Scheme](https://github.com/MattDMo/Neon-color-scheme)
* [Underscore Colour Theme](https://github.com/channingwalton/sublime_underscore)
* [Solarized Colour Theme](https://github.com/SublimeColors/Solarized)
* [Baara Dark](https://github.com/jobedom/sublime-baara-dark)
* [Specials Board](https://github.com/lamotta/specialsboard)
* [Oblivion](https://github.com/jbrooksuk/Oblivion)
* [Glacier](http://glaciertheme.com)
* _Contact me if you want your color scheme listed here. Or do a pull request._

If your color scheme file does not define the appropriate colors (or you want to edit them) add an entry that looks like this:

```xml
<dict>
  <key>name</key>
  <string>GitGutter deleted</string>
  <key>scope</key>
  <string>markup.deleted.git_gutter</string>
  <key>settings</key>
  <dict>
    <key>foreground</key>
    <string>#F92672</string>
  </dict>
</dict>
<dict>
  <key>name</key>
  <string>GitGutter inserted</string>
  <key>scope</key>
  <string>markup.inserted.git_gutter</string>
  <key>settings</key>
  <dict>
    <key>foreground</key>
    <string>#A6E22E</string>
  </dict>
</dict>
<dict>
  <key>name</key>
  <string>GitGutter changed</string>
  <key>scope</key>
  <string>markup.changed.git_gutter</string>
  <key>settings</key>
  <dict>
    <key>foreground</key>
    <string>#967EFB</string>
  </dict>
</dict>
<dict>
  <key>name</key>
  <string>GitGutter ignored</string>
  <key>scope</key>
  <string>markup.ignored.git_gutter</string>
  <key>settings</key>
  <dict>
    <key>foreground</key>
    <string>#565656</string>
  </dict>
</dict>
<dict>
  <key>name</key>
  <string>GitGutter untracked</string>
  <key>scope</key>
  <string>markup.untracked.git_gutter</string>
  <key>settings</key>
  <dict>
    <key>foreground</key>
    <string>#565656</string>
  </dict>
</dict>
```
### Jumping Between Changes
There are commands to jump between modifications. The default keybindings for these commands are:

**OSX**

prev: <kbd>command</kbd> + <kbd>shift</kbd> + <kbd>option</kbd> + <kbd>k</kbd>
next: <kbd>command</kbd> + <kbd>shift</kbd> + <kbd>option</kbd> + <kbd>j</kbd>

**Windows**

prev: <kbd>ctrl</kbd> + <kbd>shift</kbd> + <kbd>alt</kbd> + <kbd>k</kbd>
next: <kbd>ctrl</kbd> + <kbd>shift</kbd> + <kbd>alt</kbd> + <kbd>j</kbd>

<br>

------------

### Alternatives

*Don't use Sublime?*
 - [Vim GitGutter](https://github.com/airblade/vim-gitgutter)
 - [Emacs GitGutter](https://github.com/syohex/emacs-git-gutter)

*Don't use Git?*
 - [VcsGutter](https://github.com/bradsokol/VcsGutter)
 - [Modific](https://github.com/gornostal/Modific) *Not a port/fork of __GitGutter__ but similar*
