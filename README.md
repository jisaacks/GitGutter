## Git Gutter

A sublime text 2 plugin to show an icon in the gutter area indicating whether a line has been inserted, modified or deleted.

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

GitGutter assumes that the `git` and `diff` command is availible on the command line. Since the MSI installer for Git on Windows only adds the `cmd` directory of your Git installation to the `PATH` environment variable by default, GitGutter may not work out of the box. In this case you have to add the `bin` directory of your Git installation to the `PATH` environment variable.

For example:
```dos
 %PATH%;C:\Program Files (x86)\Git\bin;C:\Program Files (x86)\Git\cmd
```

### Settings

By default it is set to live mode, which runs everytime the file is modified. If you experience performance issues you can set it to only run on save by adding an entry to your **Preferences.sublime-text** file, just set:

```json
"git_gutter_live_mode": false
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


