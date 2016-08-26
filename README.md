# Git Gutter

A sublime text 2/3 plugin to show an icon in the gutter area indicating whether a line has been inserted, modified or deleted.

### Screenshot:

![screenshot](https://raw.github.com/jisaacks/GitGutter/master/screenshot.png)

### Installation

You can install via [Sublime Package Control](http://wbond.net/sublime_packages/package_control):

  * [GitGutter](https://sublime.wbond.net/packages/GitGutter) - Release based
  * [GitGutter-Edge](https://sublime.wbond.net/packages/GitGutter-Edge) - Stick with master branch (at your own peril)

Or you can clone this repo into your *Sublime Text x/Packages*:

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

```shell
cd "%APPDATA%\Sublime Text 2\Packages"
git clone git://github.com/jisaacks/GitGutter.git
```

On OS X you might need to install the package [SublimeFixMacPath](https://github.com/int3h/SublimeFixMacPath).

## It's not working!?

The most common reason for the icons to not show up is likely a problem with GitGutter finding the `git` executable on your [path](https://en.wikipedia.org/wiki/PATH_(variable)). Please read the section on the [git_binary](#git-path) setting for how to fix that.  

## Advanced Features

### Diff Popup

![diff_popup_screenshot](https://cloud.githubusercontent.com/assets/12573621/17908698/ccbecd24-6981-11e6-8f56-edd0faaed9ec.png)

| symbol | meaning if the symbol              |
| ---    | ---                                |
| ×      | close the popup                    |
| ⤒      | jump to first change               |
| ↑      | jump to previous change            |
| ↓      | jump to next change                |
| ⎘      | copy the content of the git state  |
| ⟲      | revert changes to the state in git |

The diff popup appears if you hover the mouse of the gutter changes. However this functionality is only enabled in Build `3116` or newer *(which is currently only in the dev builds)*. If you are using an older Sublime Text 3 version you can also show the diff popup from the command palette or via a keybinding.

### Comparing against different commits/branches/tags

By default, Git Gutter compares your working copy against the HEAD. You can change this behaviour through the ST command palette. The following options are available:

- Compare against HEAD
- Compare against particular branch
- Compare against particular tag
- Compare against specific commit

To change the compare option:

- Open the command palette (`Ctrl-Shift-P` for Windows/Linux, `Cmd-Shift-P` for Mac)
- Start typing `GitGutter`
- You'll see the 4 options listed above, select one with the keyboard.
- Choose the branch/tag/commit to compare against.

### Jumping Between Changes

There are commands to jump between modifications. The default keybindings for these commands are:

| OS X | Windows / Linux | Description |
|------|-----------------|-------------|
| <kbd>Command</kbd>+<kbd>Shift</kbd>+<kbd>Option</kbd>+<kbd>k</kbd> | <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Alt</kbd>+<kbd>k</kbd> | Previous |
| <kbd>Command</kbd>+<kbd>Shift</kbd>+<kbd>Option</kbd>+<kbd>j</kbd> | <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Alt</kbd>+<kbd>j</kbd> | Next |


## Settings
Settings are accessed via the <kbd>Preferences</kbd> > <kbd>Package Settings</kbd> > <kbd>GitGutter</kbd> menu.

Default settings should not be modified, as they are overwritten when GitGutter updates. Instead, you should copy the relevant settings into GitGutter's user settings file.

#### Non Blocking Mode
When set to `true` then GitGutter will run in a seperate thread and will not block. This does cause a slight delay between when you make a modification and when the icons update in the gutter.

#### Debounce Delay
When using non_blocking mode, delay update of gutter icons by the following amount (in milliseconds). Useful for performance issues. Default 1000 (1 second).

#### Live Mode
By default, GitGutter detects changes every time the file is modified. If you experience performance issues you can set it to only run on save by setting `live_mode` to `false`.

#### Hover Diff Popup
*This hover feature is only available in Build 3116 and newer.*
GitGutter shows a diff popup, when hovering over changes in the gutter. Set `enable_hover_diff_popup` to `false`, if you want to disable this popup. You can still open it with a keybinding and from the command panel.

#### Diff Popup appearance
*The diff popup is only available in Sublime Text 3*
The popup uses the [mdpopups library](https://github.com/facelessuser/sublime-markdown-popups) and the corresponding settings are global and not only for GitGutter. You can change the syntax highlighting style to the same as Sublime Text by adding `"mdpopups.use_sublime_highlighter": true` to your User settings. Other settings can be found [here](http://facelessuser.github.io/sublime-markdown-popups/usage/#global-user-settings).

#### Untracked Files
GitGutter shows icons for new files and ignored files. These icons will be on every line. You can toggle the setting `show_markers_on_untracked_file` to turn this feature off. Defaults to true (shows icons). You may need to add scopes to your color scheme (`markup.ignored.git_gutter` and `markup.untracked.git_gutter`) to color the icons.

#### Minimap
GitGutter will show diffs in the minimap on Sublime Text 3. This can be disabled by setting `show_in_minimap` to `false`.

#### Git path
If `git` is not found by GitGutter you may need to set the `git_binary` setting to the location of the git binary.  The value may be either a direct string to a git binary:
```javascript
{
  "git_binary": "E:\\Portable\\git\\bin\\git.exe"
}
```

Or it may be a dictionary keyed off what sublime.platform() returns, so it may be customized on a per-platform basis:
```javascript
"git_binary": {
  "default": "",
  "linux": "/usr/bin/git",
  "windows": "C:/Program Files/Git/cmd/git.exe"
}
```

It is valid to use environment variables in the setting value, and they will be expanded appropriately.

In a POSIX environment you can run `which git` to find the path to git if it is in your path.  On Windows, you can use `where git` to do the equivalent.

#### Protected Regions
Is GitGutter blocking SublimeLinter or other icons? You can prevent this by adding which regions you would like GitGutter to not override:
```javascript
"protected_regions": ["region", "names"]
```
You will need to figure out the names of the regions you are trying to protect.

#### Status Bar Text

You can turn off the status bar text by changing `"show_status": "default"` to `"show_status": "none"`.

#### Per-project Settings
Sublime Text supports project-specific settings, allowing `live_mode` to be set differently for different repositories.
To implement, use the <kbd>Project</kbd> > <kbd>Edit Project</kbd> menu and add the `settings` key as shown.
```javascript
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

* [Afterglow](https://github.com/YabataDesign/afterglow-theme)
* [Baara Dark](https://github.com/jobedom/sublime-baara-dark)
* [Brackets Color Scheme](https://github.com/jwortmann/brackets-color-scheme)
* [Cobalt2](https://github.com/wesbos/cobalt2)
* [Dark Room](https://github.com/NeilCresswell/themes)
* [Deep Blue See](https://github.com/jisaacks/DeepBlueSee)
* [Desert Night](https://github.com/fgb/desert_night)
* [Flatland](https://github.com/thinkpixellab/flatland)
* [Fox](https://github.com/karelvuong/fox)
* [Grandson of Obsidian](https://github.com/jfromaniello/Grandson-of-Obsidian)
* [Hitoshi](https://github.com/runxel/hitoshi)
* [Monokai Extended](https://github.com/jisaacks/sublime-monokai-extended)
* [Neon Color Scheme](https://github.com/MattDMo/Neon-color-scheme)
* [Neon](https://github.com/farzher/Sublime-Text-Themes)
* [Oblivion](https://github.com/jbrooksuk/Oblivion)
* [Perv](https://github.com/jisaacks/Perv-ColorScheme)
* [Solarized Colour Theme](https://github.com/SublimeColors/Solarized)
* [Spacegray](https://github.com/kkga/spacegray)
* [Specials Board](https://github.com/lamotta/specialsboard)
* [Tomorrow Theme](https://github.com/chriskempson/tomorrow-theme)
* [Underscore Colour Theme](https://github.com/channingwalton/sublime_underscore)
* [Wildlife](https://github.com/tushortz/wildlife)
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

## Alternatives

Check out the [collection of GitGutter(ish) packages for various editors](https://github.com/gitgutter)