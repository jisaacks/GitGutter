# Settings

Package settings are accessed via Main Menu or Command Palette.

Control                        | Description
-------------------------------|---------------------------------------------
**Menu**                       | Main > Preferences > Package Settings > GitGutter
**Command Palette**            | Preferences: GitGutter Settings

!!! warning

    Default settings should not be modified, as they are overwritten when GitGutter updates. Copy the relevant settings into GitGutter's user settings file instead.

## Syntax, User, Project and View Settings

All GitGutter settings can be placed in any of [Sublime Text's settings files](https://www.sublimetext.com/docs/3/settings.html) to provide syntax-, user-, project- or view-specific setups.

The setting keys found in the [GitGutter.sublime-settings](https://github.com/jisaacks/GitGutter/blob/master/GitGutter.sublime-settings) need to be prefixed using `git_gutter_` to do that. Each of those settings overrides the value from the GitGutter.sublime-settings.

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

!!! info "Preferences"

    All correctly prefixed settings can be placed into `Preferences.sublime-settings` instead of `GitGutter.sublime-settings`.

!!! info "Plugin-API"

    Settings can be modified temporarily per view by calls like `view.settings().set("git_gutter_enable", False)`

## General

### Enable or Disable Evaluation

```JSON
"git_gutter_enable": true
```

GitGutter evaluates changes every time the file is loaded, saved, activated or modified by default. Set `false` to disable evaluation and hide all gutter icons, status message and minimap markers.

!!! warning "Caution"

    This setting must be set as syntax- user- project- or view-specific setting! It is ignored when put into _GitGutter.sublime-settings_.


### Git Binary

```JSON
"git_binary": ""
```

GitGutter looks for the git binary in the [PATH](https://en.wikipedia.org/wiki/PATH_(variable)) environment variable by default.

The setting can be used to

1. specify the path to a custom git installation which is not registered to [PATH](https://en.wikipedia.org/wiki/PATH_(variable)).
2. run git via **W**indows **S**ubsystem for **L**inux (WSL) on Windows 10 by setting up a unix like path.

The value may be either a direct string to a git binary:

###### Windows

```JSON
"git_binary": "E:\\Portable\\git\\bin\\git.exe"
```

###### Linux/OSX/WSL

```JSON
"git_binary": "/usr/bin/git"
```

or it may be a dictionary keyed off what sublime.platform() returns, so it may be customized on a per-platform basis:

```JSON
"git_binary": {
    "default": "",
    "linux": "/usr/bin/git",
    "osx":  "/usr/bin/git",
    "windows": "C:/Program Files/Git/cmd/git.exe"
}
```

!!! info "Tips"

    1. It is valid to use environment variables in the setting value, and they will be expanded appropriately.
    2. In a POSIX environment you can run `which git` to find the path to git if it is in your path. On Windows, you can use `where git` to do the equivalent.


### Environment Variables

```JSON
"env": {
    "GIT_OPTIONAL_LOCKS": 0
}
```

With the `"env"` dictionary custom environment variables can be passed to git. The values overwrite the global environment variables Sublime Text is running with.

!!! info "Tips"

    1. Keys with value `None` are removed from the local environment.
    2. The `"git_gutter_env"` defined per view or project hides the global `"env"` dictionary.
    3. Make sure to use the correct separator characters of your OS, if you manipulate the `$PATH`.


### Compare Against

```JSON
"compare_against": "HEAD"
```

GitGutter compares the content of the view against the HEAD of the checked out branch by default. To change this default behaviour the `compare_against` setting can be changed to any tag, branch or commit hash git understands.

!!! info "Tips"

    This setting is overridden by the [Compare Against Command](usage.md#comare-against-)


### Diff Algorithm

```JSON
"diff_algorithm": "patience"
```

Set `diff_algorithm` to one of the following values to change this behaviour.

value       | description
:----------:|-----------------------------------------------
"default"   | The basic greedy diff algorithm. Currently, this is the default.
"minimal"   | Spend extra time to make sure the smallest possible diff is produced.
"patience"  | Use "patience diff" algorithm when generating patches.
"histogram" | This algorithm extends the patience algorithm to "support low-occurrence common elements".


### Ignore Whitespace

```JSON
"ignore_whitespace": "none"
```

GitGutter includes all whitespace when evaluating modifications by default. Set `ignore_whitespace` to one of the following values to change this behaviour.

value   | description
:------:|-----------------------------------------------
"none"  | don't ignore any whitespace changes
"cr"    | ignore the carriage return at the end of lines (git 2.18+)
"eol"   | ignore whitespace changes at the end of lines
"space" | ignore changed amount of whitespace
"all"   | ignore all whitespace


## Diff Gutter

### Debounce Delay

```JSON
"debounce_delay": 1000
```

Delays update of gutter icons by the following amount (in milliseconds). Useful for performance issues. Default 1000 (1 second).


### Focus Change Mode

```JSON
"focus_change_mode": true
```

GitGutter evaluates changes every time a view gets the focus by default. Set `false` to disable evaluation when changing views.

!!! info "Tips"

    This setting has effect with `"live_mode": false` only.

    GitGutter always evaluates changes after _loading_ and _saving_ a document.


### Live Mode

```JSON
"live_mode": true
```

GitGutter evaluates changes every time the file is modified by default. Set `false` to disable evaluation after each input.

!!! info "Tips"

    GitGutter always evaluates changes after _loading_ and _saving_ a document.


### Protected Regions

To avoid GitGutter from overriding more important gutter icons a list of protected regions can be created, which GitGutter won't add gutter icons to.

```JSON
"protected_regions": [
    "sublimelinter-warning-gutter-marks",
    "sublimelinter-error-gutter-marks",
    "bookmarks"
],
```

!!! info "Tips"

    You will need to figure out the names of the regions to protect.


### Show Markers on Untracked Files

```JSON
"show_markers_on_untracked_file": true
```

GitGutter shows icons on each line for untracked and ignored files by default. Set to `false` to hide those icons.

!!! warning "Scopes"

    You may need to add scopes (`markup.ignored.git_gutter` and `markup.untracked.git_gutter`) to your color scheme to color the icons.


### Show Markers in Minimap

```JSON
"show_in_minimap": 1
```

GitGutter shows diffs in the minimap on Sublime Text 3 by default. Change `show_in_minimap` to one of the following values to disable this feature or change the width of the markers.

 value  | description
:------:|-----------------
 =0     | hide markers
 &gt;1  | width of markers
 -1     | highlight full line


### Themes

```JSON
"theme": "Default.gitgutter-theme"
```

GitGutter provides support for custom gutter icons and diff popup style sheets coming with theme packages. Set `theme` to a valid theme file name to activate a different icon set.

GitGutter includes following themes:

- Bars.gitgutter-theme
- Bars Thin.gitgutter-theme
- Default.gitgutter-theme
- Default HiDPI.gitgutter-theme (_for ST2 and old ST3 dev builds_)

!!! info "Custom Themes"
    
    To provide a custom theme developers need to add a folder with all required icons and optionally a `gitgutter_popup.css` file to their package. An empty JSON file `<ThemeName>.gitgutter-theme` must exist to mark this folder a resource for GitGutter icons.


## Diff Popup

ⓘ _requires Sublime Text 3 Build 3124+ and mdpopups 2.0.0+_

### Enable Hover

```JSON
"enable_hover_diff_popup": true
```

GitGutter shows a diff popup, when hovering over changes in the gutter. Set `false` to disable the hovering feature.

!!! info "Tips"

    You can still open it with a [key binding or command palette](/usage.md#show-diff-popup).


### Default Mode

```JSON
"diff_popup_default_mode": "default"
```

The popup displays the previous state of the content under the cursor by `"default"` but can be set to `"diff"` to highlight the differences between the git state and the editor state.


### Protected Regions

```JSON
"diff_popup_protected_regions": [
    "sublime_linter.protected_regions"
],
```

To avoid GitGutter's diff popup from figting with other popups while hovering the gutter a list of protected regions can be created. If the line under the mouse cursor is occupied by one of these regions, no diff popup is displayed.

!!! info "Tips"

    1. You will need to figure out the names of the regions to protect.

    2. You can still open it with a [key binding or command palette](/usage.md#show-diff-popup).


### Stylesheet

The default style of the _Diff Popup_ is defined by _mdpopups_´s **default.css** and GitGutter´s **gitgutter_popup.css**. Both try their best to adapt the popup´s apeareance to the active color scheme automatically.

The apeareance can be customized by

1. an embedded stylesheet in the color scheme
2. editing the _Packages/User/mdpopups.css_
3. editing the _Packages/User/gitgutter_popup.css_


!!!info "Edit gitgutter_popup.css"

    GitGutter´s style settings are accessible via
    
    1. **Menu:** Main > Preferences > Package Settings > GitGutter > Popup Stylesheet
    
    2. **Command Palette**: Preferences: GitGutter Popup Stylesheet


### Syntax Highlighting

The popup uses the [mdpopups](https://github.com/facelessuser/sublime-markdown-popups) library to render its content, which includes syntax highlighting.

Please refer to [mdpopups settings documentation](http://facelessuser.github.io/sublime-markdown-popups/usage/#global-user-settings) for settings to change this behaviour.


## Line Annotation

The active line of the active view is annotated with information about who changed it when. Its behaviour and the look & feel can be modified with the following settings.


### Show Line Annotation

```JSON
"show_line_annotation": "auto"
```

ⓘ _requires Sublime Text 3 Build 3124+_

GitGutter displays information about the author of a change right next to the line using a phantom text if word wrapping is disabled. The behaviour can be modified by setting `show_line_annotation` to one of the following values:

 Value   | Description
:-------:|--------------------------------------------------
 "auto"  | show line annotation if word wrap is disabled (default)
 true    | always show line annotation
 false   | never show line annotation


### Line Annotation Template

```JSON
"line_annotation_text": "{{line_author}} ({{line_author_age}}) · {{line_summary}}"
```

The _Line Annotation_ is rendered by [jinja2](http://jinja.pocoo.org/docs/) using a fully customizable template from the `line_annotation_text` setting. 

!!! info "disable jinja2"

    Set `"line_annotation_text": null` to disable [jinja2](http://jinja.pocoo.org/docs/) engine.
    
    The message is formatted with a fixed template which is also used if [jinja2](http://jinja.pocoo.org/docs/) is not available.

!!! info "multiline templates"

    The setting can organized as an array of strings for better readability. It is joined and then passed to [jinja2](http://jinja.pocoo.org/docs/).
    
    **Example**
    
    ```JSON
    "line_annotation_text": [
        "{{line_author}}",
        " ({{line_author_age}})",
        " · {{line_summary}}"
    ]
    ```

The following variables can be used to customize the template:

 Variable                  | Description
:-------------------------:|--------------------------------------------------
 `{{line_author}}`         | the author, who introduced the change
 `{{line_author_mail}}`    | the e-mail address of the author
 `{{line_author_age}}`     | the time elapsed since the change
 `{{line_author_time}}`    | the time string of the change
 `{{line_author_tz}}`      | the timezone string of the change
 `{{line_commit}}`         | the hash of the changing committing
 `{{line_committer}}`      | the committer, who added the change to the repo
 `{{line_committer_mail}}` | the e-mail address of the committer
 `{{line_committer_age}}`  | the time elapsed since the change
 `{{line_committer_time} ` | the time string of commit
 `{{line_committer_tz} `   | the timezone string of commit
 `{{line_summary}}`        | the first line of the commit message
 `{{line_previous}}`       | the hash of the previous commit


### Line Annotation Ruler

```JSON
"line_annotation_ruler": false
```

The _Line Annotation_ is aligned to the end of a line with a predefined distance by default. To align the Line Annotation to the first ruler instead, you can set `line_annotation_ruler` to `1`. A value of `2` aligns the text to the second ruler if available and so forth.


### Line Annotation Inore Whitespace

```JSON
"line_annotation_ignore_whitespace": false
```

Line annotations display any change including whitespace by default. Set to `true` to ignore whitespace when comparing the parent’s version and the child’s to find where the lines came from.


## Status Bar Text

### Show Status Bar Text

```JSON
"show_status_bar_text": true
```

GitGutter displays status information about open files in the status bar by default. Set to `false` to hide the information.


### Status Bar Text Template

```JSON
"status_bar_text": [
    "{% if repo and branch %}",
    "{{repo}}/{{branch}}",
    "{% if added_files + deleted_files + modified_files > 0 %}*{% endif %}",
    "{% if compare not in ('HEAD', branch, None) %}, Comparing against {{compare}}{% endif %}",
    "{% if state %}, File is {{state}}{% endif %}",
    "{% if deleted > 0 %}, {{deleted}}-{% endif %}",
    "{% if inserted > 0 %}, {{inserted}}+{% endif %}",
    "{% if modified > 0 %}, {{modified}}≠{% endif %}",
    "{% if line_author and line_author_age %}, ⟢ {{line_author}} ({{line_author_age}}){% endif %}",
    "{% endif %}"
]
```

The _Status Bar Text_ is rendered using a fully customizable template from `status_bar_text`. The setting is organized as an array of strings for better readability. It is joined and then passed to [jinja2](http://jinja.pocoo.org/docs/).

!!! info "disable jinja2"

    Set `"line_annotation_text": null` to disable [jinja2](http://jinja.pocoo.org/docs/) engine.
    
    The message is formatted with a fixed template which is also used if [jinja2](http://jinja.pocoo.org/docs/) is not available.

The following variables can be used to customize the template:

 Variable                  | Description
:-------------------------:|-------------------------------------------------------------
 `{{repo}}`                | repository name / folder name containing the .git directory
 `{{branch}}`              | checked out branch you are working on
 `{{remote}}`              | tracked remote of current branch you are working on or `None`
 `{{ahead}}`               | number of commits the local branch is ahead of remote
 `{{behind}}`              | number of commits the local branch is behind remote
 `{{added_files}}`         | number of untracked files added to working tree
 `{{deleted_files}}`       | number of files deleted from working tree
 `{{modified_files}}`      | number of modified files in the working tree
 `{{staged_files}}`        | number of files in the staging area
 `{{compare}}`             | commit/branch/HEAD the file is compared to
 `{{state}}`               | One of committed/modified/ignored/untracked
 `{{deleted}}`             | number of deleted regions
 `{{inserted}}`            | number of inserted lines
 `{{modified}}`            | number of modified lines
 `{{line_author}}`         | the author, who introduced the change
 `{{line_author_mail}}`    | the e-mail address of the author
 `{{line_author_age}}`     | the time elapsed since the change
 `{{line_author_time}}`    | the time string of the change
 `{{line_author_tz}}`      | the timezone string of the change
 `{{line_commit}}`         | the hash of the changing committing
 `{{line_committer}}`      | the committer, who added the change to the repo
 `{{line_committer_mail}}` | the e-mail address of the committer
 `{{line_committer_age}}`  | the time elapsed since the change
 `{{line_committer_time} ` | the time string of commit
 `{{line_committer_tz} `   | the timezone string of commit
 `{{line_summary}}`        | the first line of the commit message
 `{{line_previous}}`       | the hash of the previous commit
