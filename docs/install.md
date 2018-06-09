# Installation

## Package Control

It is highly recommended to install GitGutter with [Package Control](https://packagecontrol.io) as it automatically installs required [dependencies](#dependencies) and keeps all packages up to date.

1. [Install Package Control](https://packagecontrol.io/installation) if you haven't yet.
2. Open the command palette (<kbd>Ctrl+Shift+P</kbd> for Windows/Linux, <kbd>Cmd+Shift+P</kbd> for Mac OS)
3. Search for _Package Control: Install Package_ and hit <kbd>Enter</kbd>.
4. Type `GitGutter` and press <kbd>Enter</kbd> to install it.


### Pre-Releases

If you are interested in testing bleeding edge features you can set up Package Control to install pre-releases by adding GitGutter to `install_prereleases` key in the `Package Control.sublime-settings`.

```JSON
"install_prereleases":
[
  "GitGutter"
],
```


### GitGutter-Edge

The _GitGutter-Edge_ package is replaced by [Pre-Releases](#pre-releases).

This change was made ...

1. to avoid issues with functions which depend on the package name.
2. because branch based packages are deprecated by Package Control.
3. to have more control about when to publish new features for testing.

!!! info "Tip"

    If you don't want to wait for [Pre-Releases](#pre-releases) you can pull from master branch directly.


## Manual Installation

You can clone this repository into your _Sublime Text x/Packages_


##### Mac OS

```shell
cd ~/Library/Application\ Support/Sublime\ Text\ 3/Packages/
git clone git://github.com/jisaacks/GitGutter.git
```


##### Linux

```shell
cd ~/.config/sublime-text-3/Packages
git clone git://github.com/jisaacks/GitGutter.git
```


##### Windows

```shell
cd "%APPDATA%\Sublime Text 3\Packages"
git clone git://github.com/jisaacks/GitGutter.git
```

!!! info "Tips"

    The `git` command must be available on the command line.

    You may need to add the directory containing `git.exe` to your `PATH` environment variable.


## Dependencies

Some functions of GitGutter depend on the following external libraries to work properly. They are installed automatically for you by Package Control, so normally don't need to care about. But on setups without Package Control you need to make sure they are installed and available in the global namespace of Sublime Text's python interpreter on your own.

- [markupsafe](https://bitbucket.org/teddy_beer_maniac/sublime-text-dependency-markupsafe)
- [mdpopups](https://github.com/facelessuser/sublime-markdown-popups)
- [pygments](https://github.com/packagecontrol/pygments)
- [python-jinja2](https://bitbucket.org/teddy_beer_maniac/sublime-text-dependency-jinja2)
- [python-markdown](https://github.com/facelessuser/sublime-markdown)

!!! info "Mac OS"

    On Mac OS you might need to install the package [SublimeFixMacPath](https://github.com/int3h/SublimeFixMacPath) if you are using Sublime Text 2 or one of the early Sublime Text 3 dev builds.

!!! info "Manual Install"

    To manually install pull from the linked repos into ST's Packages folder.
