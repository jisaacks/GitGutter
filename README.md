## VCS Gutter

A Sublime Text 2 plugin to show an icon in the gutter area indicating whether a line has been inserted, modified or deleted relative to the version of the file in the local source
code repository. Supports Git and Mercurial.

VCS Gutter builds on the original work by [jisaacks](https://github.com/jisaacks)
on [GitGutter](https://github.com/jisaacks/GitGutter).

### Screenshot:

![screenshot](https://raw.github.com/bradsokol/VcsGutter/master/screenshot.png)

### Installation

You can install via [Sublime Package Control](http://wbond.net/sublime_packages/package_control)  
Or you can clone this repo into your *Sublime Text 2/Packages*

*Mac OS X*
```shell
cd ~/Library/Application\ Support/Sublime\ Text\ 2/Packages/
git clone git@github.com:bradsokol/VcsGutter.git
```

*Ubuntu*
```shell
cd ~/.config/sublime-text-2/Packages
git clone git@github.com:bradsokol/VcsGutter.git
```

*Windows*

VcsGutter assumes that the `git`, `hg`, `svn` and `diff` commands are availible on the command line. The installers for these tools may not add the directory containing the executables to the PATH environment variable. If not, you must add the appropriate directory to your PATH variable.

For example:
```dos
 %PATH%;C:\Program Files (x86)\Git\bin;C:\Program Files (x86)\Git\cmd
```

### Settings

By default it is set to live mode, which runs everytime the file is modified. If you experience performance issues you can set it to only run on save by adding an entry to your **Preferences.sublime-text** file, just set:

```json
"vcs_gutter_live_mode": false
```

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


