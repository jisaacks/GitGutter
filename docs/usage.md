# Usage

In order to enable your favourite work flow all major functions GitGutter has to offer are available via

- Main Menu
- Command Palette
- Key Bindings


!!! info "Command Palette"

    1. Open the command palette via _Main > Tools > Command Palette ..._ or key binding <kbd>Ctrl + Shift + P</kbd> for Windows/Linux or <kbd>⌘ + ⇧ + P</kbd> for Mac OS
    2. Start typing `GitGutter:`
    3. Select one of the listed commands with the keyboard and press <kbd>Enter</kbd>.


## Disable Evaluation

GitGutter tries best it can to decide automatically [when to keep quiet](troubleshooting.md#gitgutter-keeps-completely-quiet).

To manually disable GitGutter for a certain View use:

Control                        | Description
-------------------------------|---------------------------------------------
**Menu**                       | Main > View > GitGutter > Enabled for View


## Compare Against ...

GitGutter compares the working copy against the HEAD commit of the checked out branch by default.

To temporarily change the compare target for the whole repository use:

Control                        | Description
-------------------------------|---------------------------------------------
**Menu**                       | Main > View > GitGutter > Compare Against `<target>`
**Command Palette**            | GitGutter: Compare Against `<target>`
**Key Bindings Linux/Windows** | <kbd>Ctrl + Shift + Alt + c, `<key>`</kbd>
**Key Bindings OSX**           | <kbd>⌘ + ⇧ + ⌥ + c, `<key>`</kbd>

When using key bindings press one of the following keys after <kbd>Ctrl + Shift + Alt + c</kbd> to change the compare target.

`<key>`      | `<target>`
-------------| ----------------------------------------
<kbd>h</kbd> | HEAD
<kbd>b</kbd> | branch
<kbd>t</kbd> | tag
<kbd>c</kbd> | commit
<kbd>f</kbd> | file commit (_current file's history_)
<kbd>o</kbd> | origin (_@{upstream}_)


## Show Diff Popup

The _Diff Popup_ appears by hovering the mouse over the gutter area of Sublime Text or can be called from command palette or via a key binding.

ⓘ _requires Sublime Text 3 Build 3124+ and mdpopups 2.0.0+_

Control                        | Description
-------------------------------|---------------------------------------------
**Mouse**                      | Hover the gutter area of a changed line
**Menu**                       | Main > View > GitGutter > Diff Popup
**Command Palette**            | GitGutter: Show Diff Popup
**Key Bindings Linux/Windows** | <kbd>Ctrl + Shift + Alt + c, Ctrl + D</kbd>
**Key Bindings OSX**           | <kbd>⌘ + ⇧ + ⌥ + c, ⌘ + D</kbd>


## Goto Change

The commands are used to quickly navigate between modifications.

The `"next_prev_change_wrap"` setting controls whether to continue at document boundaries or not.

The default step size of 1 can be customized by command arguments. You'd need to create your own custom key bindings to make use of it.


### Previous Change

Control                        | Description
-------------------------------|---------------------------------------------
**Menu**                       | Main > Goto > Goto Previous Change
**Command Palette**            | GitGutter: Goto Previous Change
**Diff Popup**                 | **↑** toolbar button
**Key Bindings Linux/Windows** | <kbd>Ctrl + Shift + Alt + k</kbd>
**Key Bindings OSX**           | <kbd>⌘ + ⇧ + ⌥ + k</kbd>


### Next Change

Control                        | Description
-------------------------------|---------------------------------------------
**Menu**                       | Main > Goto > Goto Next Change
**Command Palette**            | GitGutter: Goto Next Change
**Diff Popup**                 | **↓** toolbar button
**Key Bindings Linux/Windows** | <kbd>Ctrl + Shift + Alt + j</kbd>
**Key Bindings OSX**           | <kbd>⌘ + ⇧ + ⌥ + j</kbd>


## Copy Content from Commit

The command copies the committed content of the changed hunk under the first cursor to the clipboard. The default key binding for this command is:

Control                        | Description
-------------------------------|---------------------------------------------
**Menu**                       | Main > Edit > Copy Content from Commit
**Command Palette**            | GitGutter: Copy Content from Commit
**Diff Popup**                 | **⎘** toolbar button
**Key Bindings Linux/Windows** | <kbd>Ctrl + Shift + c</kbd>
**Key Bindings OSX**           | <kbd>⌘ + ⇧ c</kbd>


## Revert Change to Commit

The command reverts the text under the first cursor to the state in git. The default key binding for this command is:

Control                        | Description
-------------------------------|---------------------------------------------
**Menu**                       | Main > Edit > Revert Change to Commit
**Command Palette**            | GitGutter: Revert Change to Commit
**Diff Popup**                 | **⟲** toolbar button
**Key Bindings Linux/Windows** | <kbd>Ctrl + Shift + Alt + z</kbd>
**Key Bindings OSX**           | <kbd>⌘ + ⇧ + ⌥ + z</kbd>
