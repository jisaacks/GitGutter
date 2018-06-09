# Troubleshooting


## Is git working?

The most common reasons for the icons to not show up are:

- GitGutter can't find the `git` executable on [PATH](https://en.wikipedia.org/wiki/PATH_(variable)).
- On Mac OS the "Xcode/iOS license" needs to be agreed to make git work.

To check, whether git is found and working properly ...

1. Open the command palette via _Main > Tools > Command Palettee ..._ or key binding <kbd>Ctrl + Shift + P</kbd> for Windows/Linux or <kbd>⌘ + ⇧ + P</kbd> for Mac OS
2. Search for _GitGutter: Support Info_ and hit <kbd>Enter</kbd>.

A dialog is displayed with version information of Sublime Text and all packages being used by GitGutter.

If git was found on [PATH](https://en.wikipedia.org/wiki/PATH_(variable)) and is working properly, the dialog contains a line like _git version 2.10.0.windows.1_. Otherwise some more detailed information about the reason for git not to work may be found in the console window, then. If not try again with `"debug": true` added to the GitGutter settings.


## Git works in shell but is not found by GitGutter!

Some operating systems (especially Mac OS) may not run Sublime Text within the login shell. As a result Sublime Text and all its packages don't have access to some of the user's environment variables including the [PATH](https://en.wikipedia.org/wiki/PATH_(variable)) to git.

In some cases the package providing git, simply required some user confirmation due to license changes and thus simply refuses to run git.

_With [SublimeFixMacPath](https://github.com/int3h/SublimeFixMacPath) package Sublime Text loads the PATH environment from the login shell. If git is working there, it will be found by GitGutter, too, then._

_GitGutter can work with a certain binary, too. Please read the section on the [git_binary](#git-path) setting._


## GitGutter no longer works after upgrade

_Please check if GitGutter works after restarting Sublime Text._

All modules of GitGutter were moved to `modules` sub directory to present them to Sublime Text as one package to avoid creating multiple instances of some modules and objects and reduce package loading time by about 50%.

GitGutter handles Package Control's `post_upgrade` event to reload all its submodules once after upgrading. In rare cases some modules might not be recovered properly and thus require a restart of ST to make GitGutter work again.


## GitGutter keeps completely quiet

GitGutter is installed and loads properly without any error messages printed to Sublime Text's console, but keeps completely disabled in some or all repositories. Neither gutter icons nor messages are displayed in the status bar.

GitGutter is designed to keep quiet in the following situations when evaluation is expected useless:

- disabled in _Preferences.sublime-settings_, project settings or view settings (`"git_gutter_enabled": false`)
- the current view
  - shows a file which is not part of a git working tree
  - is not attached to a window
  - is read only
  - is a scratch view
  - is a widget (`"is_widget": true`)
  - is a REPL view (`"repl": true`)
  - has "Hexadecimal" encoding

Please check if one of those states was applied to your view by one of your packages.

!!! info "debug"

    With `"debug": true` the reason for GitGutter to keep quite is printed to console.

!!! warning "known issues"

    _ConvertToUTF8_ package is known to mark views as scratch during conversion without reverting that state reliably.


## GitGutter doesn't recognize working tree

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
