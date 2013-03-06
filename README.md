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
git clone git@github.com:jisaacks/GitGutter.git
```

*Ubuntu*
```shell
cd ~/.config/sublime-text-2/Packages
git clone git@github.com:jisaacks/GitGutter.git
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

#### Live Mode
By default, GitGutter detects changes every time the file is modified. If you experience performance issues you can set it to only run on save by setting `live_mode` to `false`.

#### Git path
If git is not in your PATH, you may need to set the `git_binary` setting to the location of the git binary, e.g. in a portable environment;
```js
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

The colors come from your *color scheme* **.tmTheme** file. If your color scheme file does not define the appropriate colors (or you want to edit them) add an entry that looks like this:

```xml
<dict>
  <key>name</key>
  <string>diff.deleted</string>
  <key>scope</key>
  <string>markup.deleted</string>
  <key>settings</key>
  <dict>
    <key>foreground</key>
    <string>#F92672</string>
  </dict>
</dict>
<dict>
  <key>name</key>
  <string>diff.inserted</string>
  <key>scope</key>
  <string>markup.inserted</string>
  <key>settings</key>
  <dict>
    <key>foreground</key>
    <string>#A6E22E</string>
  </dict>
</dict>
<dict>
  <key>name</key>
  <string>diff.changed</string>
  <key>scope</key>
  <string>markup.changed</string>
  <key>settings</key>
  <dict>
    <key>foreground</key>
    <string>#967EFB</string>
  </dict>
</dict>
```  

<br>

------------

### Alternatives

*Don't use Sublime?*
 - [Vim GitGutter](https://github.com/airblade/vim-gitgutter)
 - [Emacs GitGutter](https://github.com/syohex/emacs-git-gutter)

*Don't use Git?*
 - [VcsGutter](https://github.com/bradsokol/VcsGutter)
 - [Modific](https://github.com/gornostal/Modific) *Not a port/fork of __GitGutter__ but similar*
