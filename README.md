# Git Gutter

A [Sublime Text 2/3](http://www.sublimetext.com) plug-in to show information about files in a git repository.


##### Main Features

1. _Gutter Icons_ indicating inserted, modified or deleted lines
2. _Diff Popup_ with details about modified lines
3. _Status Bar Text_ with information about file and repository
4. _Goto Change_ to easily navigate between modified lines

![screenshot](https://user-images.githubusercontent.com/16542113/28744712-f80ea13e-7466-11e7-96ac-51f453fb22b6.gif)

 Icon          | Description
:-------------:|-------------------------
![inserted][]  | inserted line
![changed][]   | modified line
![deleted][]   | deleted region borders
![ignored][]   | ignored file
![untracked][] | untracked file

[changed]: <https://cloud.githubusercontent.com/assets/16542113/23225773/6a0204ac-f933-11e6-9213-c75a33795fec.png>
[deleted]: <https://cloud.githubusercontent.com/assets/16542113/23225777/6a04baf8-f933-11e6-9ce4-2a17fd604f37.png>
[ignored]: <https://cloud.githubusercontent.com/assets/16542113/23225774/6a02719e-f933-11e6-9376-059044379246.png>
[inserted]: <https://cloud.githubusercontent.com/assets/16542113/23225775/6a02a5a6-f933-11e6-8def-a95d6a2bf448.png>
[untracked]: <https://cloud.githubusercontent.com/assets/16542113/23225776/6a0379fe-f933-11e6-8c60-cd751c8ca094.png>


## 💾 Installation

### Package Control

It is highly recommended to install GitGutter with [Package Control](https://packagecontrol.io) as it automatically installs required [dependencies](#dependencies) and keeps all packages up to date.

1. [Install Package Control](https://packagecontrol.io/installation) if you haven't yet.
2. Open the command palette (<kbd>Ctrl+Shift+P</kbd> for Windows/Linux, <kbd>Cmd+Shift+P</kbd> for Mac OS)
3. Search for _Package Control: Install Package_ and hit <kbd>Enter</kbd>.
4. Type `GitGutter` and press <kbd>Enter</kbd> to install it.


##### Pre-Releases

If you are interested in testing bleeding edge features you can set up Package Control to install pre-releases by adding GitGutter to `install_prereleases` key in the `Package Control.sublime-settings`.

```JavaScript
"install_prereleases":
[
  "GitGutter"
],
```


##### GitGutter-Edge

The _GitGutter-Edge_ package is replaced by [Pre-Releases](#pre-releases).

This change was made ...

1. to avoid issues with functions which depend on the package name.
2. because branch based packages are deprecated by Package Control.
3. to have more control about when to publish new features for testing.

👉 If you don't want to wait for [Pre-Releases](#pre-releases) you can pull from master branch directly.


### Manual Installation

You can clone this repository into your _Sublime Text x/Packages_


##### Mac OS

```shell
cd ~/Library/Application\ Support/Sublime\ Text\ 2/Packages/
git clone git://github.com/jisaacks/GitGutter.git
```


##### Linux

```shell
cd ~/.config/sublime-text-2/Packages
git clone git://github.com/jisaacks/GitGutter.git
```


##### Windows

```shell
cd "%APPDATA%\Sublime Text 2\Packages"
git clone git://github.com/jisaacks/GitGutter.git
```

👉 The `git` command must be available on the command line.

👉 You may need to add the directory containing `git.exe` to your `PATH` environment variable.


### Dependencies

Some functions of GitGutter depend on the following external libraries to work properly. They are installed automatically for you by Package Control, so normally don't need to care about. But on setups without Package Control you need to make sure they are installed and available in the global namespace of Sublime Text's python interpreter on your own.

- [markupsafe](https://bitbucket.org/teddy_beer_maniac/sublime-text-dependency-markupsafe)
- [mdpopups](https://github.com/facelessuser/sublime-markdown-popups)
- [pygments](https://github.com/packagecontrol/pygments)
- [python-jinja2](https://bitbucket.org/teddy_beer_maniac/sublime-text-dependency-jinja2)
- [python-markdown](https://github.com/facelessuser/sublime-markdown)

👉 On Mac OS you might need to install the package [SublimeFixMacPath](https://github.com/int3h/SublimeFixMacPath).

👉 To manually install pull from the linked repos into ST's Packages folder.


## 🔫 Troubleshooting


#### Is git working?

The most common reasons for the icons to not show up are:

- GitGutter can't find the `git` executable on [PATH](https://en.wikipedia.org/wiki/PATH_(variable)).
- On Mac OS the "Xcode/iOS license" needs to be aggreed to make git work. 

To check, whether git is found and working properly ...

1. Open the command palette (<kbd>Ctrl+Shift+P</kbd> for Windows/Linux, <kbd>Cmd+Shift+P</kbd> for Mac OS)
2. Search for _GitGutter: Support Info_ and hit <kbd>Enter</kbd>.

An dialog is displayed with version information of Sublime Text and all packages being used by GitGutter. 

If git was found on [PATH](https://en.wikipedia.org/wiki/PATH_(variable)) and is working properly, the dialog contains a line like _git version 2.10.0.windows.1_. Otherwise some more detailed information about the reason for git not to work may be found in the console window, then. If not try again with `"debug": true` added to the GitGutter settings.


#### Git works in shell but is not found by GitGutter!

Some operating systems (especially Mac OS) may not run Sublime Text within the login shell. As a result Sublime Text and all its packages don't have access to some of the user's environment variables including the [PATH](https://en.wikipedia.org/wiki/PATH_(variable)) to git.

In some cases the package providing git, simply required some user confirmation due to license changes and thus simply refuses to run git.

_With [SublimeFixMacPath](https://github.com/int3h/SublimeFixMacPath) package Sublime Text loads the PATH environment from the login shell. If git is working there, it will be found by GitGutter, too, then._

_GitGutter can work with a certain binary, too. Please read the section on the [git_binary](#git-path) setting._


#### GitGutter no longer works after upgrade

_Please check if GitGutter works after restarting Sublime Text._

All modules of GitGutter were moved to `modules` sub directory to present them to Sublime Text as one package to avoid creating multiple instances of some modules and objects and reduce package loading time by about 50%.

GitGutter handles Package Control's `post_upgrade` event to reload all its submodules once after upgrading. In rare cases some modules might not be recovered properly and thus require a restart of ST to make GitGutter work again.


#### GitGutter keeps completely quiet

GitGutter is installed and loads properly without any error messages printed to Sublime Text's console, but keeps completely disabled in some or all repositories. Neither gutter icons nor messages are displayed in the status bar.

GitGutter is designed to keep quiet in the following situations when evaluation is expected useless:

- disabled in _Preferences.sublime-settings_, project settings or view settings (`"git_gutter_enabled": false`)
- disabled in _GitGutter.sublime-settings_ (`"enabled": false`)
- the current view
  - is not attached to a window
  - is read only
  - is a scratch view
  - is a widget (`"is_widget": true`)
  - is a REPL view (`"repl": true`)
  - has "Hexadecimal" encoding

Please check if one of those states was applied to your view by one of your packages.

👉 _ConvertToUTF8_ package is known to mark views as scratch during conversion without reverting that state reliably.



#### GitGutter doesn't recognize working tree

git 2.5+ allows configurations with .git directory not being located in the working tree root. You may also checkout multiple working trees from one repository. No matter which configuration is used, GitGutter expects a `.git` directory or a `.git` file in the root of a working tree to recognize it as such.

If the `.git` directory is not located in the working tree root the following steps are required.

1. Configure the repository to point to the custom working tree by calling
   
   `git config --add core.worktree <path_to_worktree>`

   This step is required to let git use the custom working tree.

2. Create a `.git` file in the root of the working tree which points to the repository's database.
   
   ⓘ _The `.git` file must contain the line `gitdir: <path_to_git_dir>`._

   The file can be created using the following shell commands.

   **Linux / Mac OS**

   ```shell
   echo "gitdir: $(git rev-parse --git-dir)" > .git
   ```

   **Windows**

   ```shell
   for /f %i in ('git rev-parse --git-dir') do set gitdir=%i
   echo gitdir: %gitdir% > .git
   ```


## 🚀 Advanced Features

### Diff Popup

The diff popup appears by hovering the mouse over the gutter changes on Sublime Text 3 or can be called from command palette by `GitGutter: Show Diff Popup` or via a key binding.

ⓘ requires Sublime Text 3 Build 3124+ and mdpopups 2.0.0+

![diff_popup_screenshot](https://user-images.githubusercontent.com/16542113/28744598-804b73fe-7464-11e7-91c6-215a06644181.gif)

 symbol | meaning of the symbol
 :-----:| ---------------------------------------
 ×      | close the popup
 ⤒      | goto to first change
 ↑      | goto to previous change
 ↓      | goto to next change
 ≈, ≉   | enable/disable difference highlighting
 ⎘      | copy the content of the git state
 ⟲      | revert changes to the state in git


### Goto Change

The commands are used to quickly navigate between modifications. The default key bindings for these commands are:

 OS X                          | Windows / Linux             | Description
-------------------------------|-----------------------------|-------------
 <kbd>Cmd+Shift+Option+k</kbd> | <kbd>Ctrl+Shift+Alt+k</kbd> | Goto Previous Change
 <kbd>Cmd+Shift+Option+j</kbd> | <kbd>Ctrl+Shift+Alt+j</kbd> | Goto Next Change

The commands use `"next_prev_change_wrap"` setting by default to decide whether to continue at document boundaries. This behavior and the step size can be customized by command arguments with values other then `None`.

#### Example

```JavaScript
{ "command": "git_gutter_prev_change", "args": {"count": 2, "wrap": False} },
{ "command": "git_gutter_next_change", "args": {"count": 2, "wrap": False} }
```

#### Arguments

arg     | valid range       | description
:------:|:-----------------:|-----------------------------------------------
count   | None, >=1         | number of iterations to find destination hunk
wrap    | None, False, True | enable/disable wrapping at document boundaries


### Copy Content from Commit

The command copies the committed content of the changed hunk under the first cursor to the clipboard. The default key binding for this command is:

 OS X                   | Windows / Linux         | Description
------------------------|-------------------------|-------------
 <kbd>Cmd+Shift+c</kbd> | <kbd>Ctrl+Shift+c</kbd> | Copy Content


### Revert Change to Commit

The command reverts the text under the first cursor to the state in git. The default key binding for this command is:

 Mac OS                        | Windows / Linux             | Description
-------------------------------|-----------------------------|-------------
 <kbd>Cmd+Shift+Option+z</kbd> | <kbd>Ctrl+Shift+Alt+z</kbd> | Revert Change to Commit


### Comparing against different commits/branches/tags

GitGutter compares the working copy against the HEAD by default.

To change the compare option:

1. Open the command palette (<kbd>Ctrl+Shift+P</kbd> for Windows/Linux, <kbd>Cmd+Shift+P</kbd> for Mac OS)
2. Start typing `GitGutter: Compare against`
3. Select one of the 6 options with the keyboard and press <kbd>Enter</kbd>.
4. Choose the branch/tag/commit to compare against.

or just use one of the following key bindings:

 Mac OS                           | Windows / Linux                | Description
----------------------------------|--------------------------------|-------------
 <kbd>Cmd+Shift+Option+c, h</kbd> | <kbd>Ctrl+Shift+Alt+c, h</kbd> | Compare against HEAD
 <kbd>Cmd+Shift+Option+c, b</kbd> | <kbd>Ctrl+Shift+Alt+c, b</kbd> | Compare against particular branch
 <kbd>Cmd+Shift+Option+c, t</kbd> | <kbd>Ctrl+Shift+Alt+c, t</kbd> | Compare against particular tag
 <kbd>Cmd+Shift+Option+c, c</kbd> | <kbd>Ctrl+Shift+Alt+c, c</kbd> | Compare against particular commit
 <kbd>Cmd+Shift+Option+c, f</kbd> | <kbd>Ctrl+Shift+Alt+c, f</kbd> | Compare against particular file commit _(current file's history)_
 <kbd>Cmd+Shift+Option+c, o</kbd> | <kbd>Ctrl+Shift+Alt+c, o</kbd> | Compare against particular origin _(@{upstream})_

👉 The changes apply temporarily to the whole repository.


## ⚙ Settings

Settings are accessed via the <kbd>Preferences</kbd> > <kbd>Package Settings</kbd> > <kbd>GitGutter</kbd> menu.

Default settings should not be modified, as they are overwritten when GitGutter updates. Copy the relevant settings into GitGutter's user settings file instead.


#### Enable/Disable Evaluation

`"enable": true`

GitGutter evaluates changes every time the file is loaded, saved, activated or modified by default. Set `false` to disable evaluation and hide all gutter icons, status message and minimap markers.


#### Debounce Delay

`"debounce_delay": 1000`

Delays update of gutter icons by the following amount (in milliseconds). Useful for performance issues. Default 1000 (1 second).


#### Focus Change Mode

`"focus_change_mode": true`

GitGutter evaluates changes every time a view gets the focus by default. Set `false` to disable evaluation when changing views.

👉 This setting has effect with `"live_mode": false` only.

👉 GitGutter always evaluates changes after _loading_ and _saving_ a document.


#### Live Mode

`"live_mode": true`

GitGutter evaluates changes every time the file is modified by default. Set `false` to disable evaluation after each input.

👉 GitGutter always evaluates changes after _loading_ and _saving_ a document.


#### Hover Diff Popup

`"enable_hover_diff_popup": true`

ⓘ requires Sublime Text 3 Build 3124+ and mdpopups 2.0.0+

GitGutter shows a diff popup, when hovering over changes in the gutter. Set `false` to disable this popup. You can still open it with a key binding and from the command palette.


#### Diff Popup Default Mode

`"diff_popup_default_mode": "default"`

ⓘ requires Sublime Text 3 Build 3124+ and mdpopups 2.0.0+

The popup displays the previous state of the content under the cursor by `"default"` but can be set to `"diff"` to highlight the differences between the git state and the editor state.


#### Diff Popup Appearance

ⓘ requires Sublime Text 3 Build 3124+ and mdpopups 2.0.0+

The popup uses the [mdpopups](https://github.com/facelessuser/sublime-markdown-popups) library and the corresponding settings are global and not only for GitGutter. Syntax highlighting can be set to match the active color scheme by adding `"mdpopups.use_sublime_highlighter": true` to the User settings.

👉 Other settings can be found at [mdpopups settings](http://facelessuser.github.io/sublime-markdown-popups/usage/#global-user-settings) homepage.

👉 User style settings by adding a `gitgutter_popup.css` the User directory.

👉 User style settings are accessible via the settings menu.

#### Diff Popup Protected Regions

```
"diff_popup_protected_regions": [
  "sublime_linter.protected_regions"
],
```

To avoid GitGutter's diff popup from figting with other popups while hovering the gutter a list of protected regions can be created. If the line under the mouse cursor is occupied by one of these regions, no diff popup is displayed.

👉 You will need to figure out the names of the regions to protect.

👉 You can still open the diff popup via key binding or command pallet.


#### Untracked Files

`"show_markers_on_untracked_file": true`

GitGutter shows icons on each line for untracked and ignored files by default. Set to `false` to hide those icons.

You may need to add scopes (`markup.ignored.git_gutter` and `markup.untracked.git_gutter`) to your color scheme to color the icons.


#### Minimap

`"show_in_minimap": 1`

GitGutter shows diffs in the minimap on Sublime Text 3 by default. Change `show_in_minimap` to one of the following values to disable this feature or change the width of the markers.

 value  | description
:------:|-----------------
 =0     | hide markers
 &gt;1  | width of markers
 -1     | highlight full line


#### Git path

`"git_binary": ""`

If `git` is not found on [PATH](https://en.wikipedia.org/wiki/PATH_(variable)) by GitGutter the `git_binary` setting can be set to the location of the git binary. The value may be either a direct string to a git binary:

```JavaScript
"git_binary": "E:\\Portable\\git\\bin\\git.exe"
```

or it may be a dictionary keyed off what sublime.platform() returns, so it may be customized on a per-platform basis:

```JavaScript
"git_binary": {
  "default": "",
  "linux": "/usr/bin/git",
  "windows": "C:/Program Files/Git/cmd/git.exe"
}
```

It is valid to use environment variables in the setting value, and they will be expanded appropriately.

In a POSIX environment you can run `which git` to find the path to git if it is in your path.  On Windows, you can use `where git` to do the equivalent.


#### Git Environment Variables

```
"env": {
  "GIT_OPTIONAL_LOCKS": 0
}
```

With the `"env"` dictionary custom environment variables can be passed to git. The values overwrite the global environment variables Sublime Text is running with.

👉 Keys with value `None` are removed from the local environment.

👉 The `"git_gutter_env"` defined per view or project hides the global `"env"` dictionary.

👉 Make sure to use the correct separator characters of your OS, if you manipulate the `$PATH`.


#### Diff Algorithm

`"diff_algorithm": "patience"`

GitGutter uses the "patience" diff algorithm by default. Set `diff_algorithm` to one of the follwoing values to change this behavior.

value       | description
:----------:|-----------------------------------------------
"default"   | The basic greedy diff algorithm. Currently, this is the default.
"minimal"   | Spend extra time to make sure the smallest possible diff is produced.
"patience"  | Use "patience diff" algorithm when generating patches.
"histogram" | This algorithm extends the patience algorithm to "support low-occurrence common elements".

👉 The value determines which command line argument to pass to `git diff`.


#### Ignore Whitespace

`"ignore_whitespace": "none"`

GitGutter includes all whitespace when evaluating modifications by default. Set `ignore_whitespace` to one of the following values to change this behavior.

value   | description
:------:|-----------------------------------------------
"none"  | don't ignore any whitespace changes
"eol"   | ignore whitespace changes at the end of line
"space" | ignore changed amount of whitespace
"all"   | ignore all whitespace

👉 The value determines which command line argument to pass to `git diff`.


#### Protected Regions

```
"protected_regions": [
  "sublimelinter-warning-gutter-marks",
  "sublimelinter-error-gutter-marks",
  "bookmarks"
],
```

To avoid GitGutter from overriding more important gutter icons a list of protected regions can be created, which GitGutter won't add gutter icons to.

👉 You will need to figure out the names of the regions to protect.


#### Show Status Bar Text

`"show_status_bar_text": true`

GitGutter displays status information about open files in the status bar by default. Set to `false` to hide the information.


#### Status Bar Text Template

```
"status_bar_text": [
  "In {{repo}} on {{branch}}",
  "{% if compare != 'HEAD' %}, Comparing against {{compare}}{% endif %}",
  ", File is {{state}}",
  "{% if deleted != 0 %}, {{deleted}}-{% endif %}",
  "{% if inserted != 0 %}, {{inserted}}+{% endif %}",
  "{% if modified != 0 %}, {{modified}}≠{% endif %}"
]
```

The _Status Bar Text_ is rendered using a fully customizable template from `status_bar_text`. The setting is organized as an array of strings for better readability. It is joined and then passed to [jinja2](http://jinja.pocoo.org/docs/).

GitGutter provides the following variables to be used in the template.

 Variable           | Description
:------------------:|-------------------------------------------------------------
 {{repo}}           | repository name / folder name containing the .git directory
 {{branch}}         | checked out branch you are working on
 {{remote}}         | tracked remote of current branch you are working on or `None`
 {{ahead}}          | number of commits the local branch is ahead of remote
 {{behind}}         | number of commits the local branch is behind remote
 {{added_files}}    | number of untracked files added to working tree
 {{deleted_files}}  | number of files deleted from working tree
 {{modified_files}} | number of modified files in the working tree
 {{staged_files}}   | number of files in the staging area
 {{compare}}        | commit/branch/HEAD the file is compared to
 {{state}}          | One of committed/modified/ignored/untracked
 {{deleted}}        | number of deleted regions
 {{inserted}}       | number of inserted lines
 {{modified}}       | number of modified lines


#### Themes

`"theme": "Default.gitgutter-theme"`

GitGutter provides support for custom gutter icons and diff popup style sheets coming with theme packages. Set `theme` to a valid theme file name to activate a different icon set.

GitGutter includes following themes:

- Bars.gitgutter-theme
- Bars Thin.gitgutter-theme
- Default.gitgutter-theme
- Default HiDPI.gitgutter-theme

To provide a custom theme developers need to add a folder with all required icons and an optional `gitgutter_popup.css` file to their package. An empty JSON file `<ThemeName>.gitgutter-theme` must exist to mark this folder a resource for GitGutter icons.


#### Per-project and Per-syntax Settings

All GitGutter settings can be placed in any of Sublime Text's settings files to provide syntax-, user-, project- or view-specific setups.

The setting keys need to be prefixed using `git_gutter_` to do that.

To modify GitGutter settings for an open Project just open <kbd>Project</kbd> > <kbd>Edit Project</kbd> menu and add the `settings` key as shown.

```JavaScript
{
    "folders":
    [
        {
            "path": "src"
        }
    ],
    "settings":
    {
        // git_binary is the only setting not being prefixed
        "git_binary": "/path/to/project/specific/git"

        // git_gutter settings
        "git_gutter_live_mode": false,
        "git_gutter_ignore_whitespace": "space"
    }
}
```

👉 All correctly prefixed settings can be placed into `Preferences.sublime-settings` instead of `GitGutter.sublime-settings`.

👉 Settings can be modified temporarily per view by calls like `view.settings().set("git_gutter_enable", False)`


## 🖌 Icon Coloring

The colors come from your _color scheme_ **.tmTheme** file.


### Required Color Scheme Entries

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


### Supported Color Schemes

Color schemes that already have support for GitGutter include:

- [Afterglow](https://github.com/YabataDesign/afterglow-theme)
- [Baara Dark](https://github.com/jobedom/sublime-baara-dark)
- [Boxy Theme](https://github.com/ihodev/sublime-boxy)
- [Brackets Color Scheme](https://github.com/jwortmann/brackets-color-scheme)
- [Cobalt2](https://github.com/wesbos/cobalt2)
- [Dark Room](https://github.com/NeilCresswell/themes)
- [Deep Blue See](https://github.com/jisaacks/DeepBlueSee)
- [Desert Night](https://github.com/fgb/desert_night)
- [Flatland](https://github.com/thinkpixellab/flatland)
- [Fox](https://github.com/karelvuong/fox)
- [Grandson of Obsidian](https://github.com/jfromaniello/Grandson-of-Obsidian)
- [Hitoshi](https://github.com/runxel/hitoshi)
- [Monokai Extended](https://github.com/jisaacks/sublime-monokai-extended)
- [Monokai Pro](https://www.monokai.pro)
- [Neon Color Scheme](https://github.com/MattDMo/Neon-color-scheme)
- [Neon](https://github.com/farzher/Sublime-Text-Themes)
- [Oblivion](https://github.com/jbrooksuk/Oblivion)
- [Perv](https://github.com/jisaacks/Perv-ColorScheme)
- [Solarized Colour Theme](https://github.com/SublimeColors/Solarized)
- [Spacegray](https://github.com/kkga/spacegray)
- [Specials Board](https://github.com/lamotta/specialsboard)
- [Tomorrow Theme](https://github.com/chriskempson/tomorrow-theme)
- [Underscore Colour Theme](https://github.com/channingwalton/sublime_underscore)
- [Wildlife](https://github.com/tushortz/wildlife)
- _Contact me if you want your color scheme listed here. Or do a pull request._


## ⮱ Alternatives

Check out the [collection of GitGutter(ish) packages for various editors](https://github.com/gitgutter)
