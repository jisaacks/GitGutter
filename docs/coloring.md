# Coloring

The colors of gutter icons and the line annotation come from your _color scheme_ file.


## Sublime Text Color Scheme Format

`<Name>.sublime-color-scheme`

ⓘ _requires Sublime Text 3 Build 3152+_

If a color scheme file does not define the appropriate colors (or you want to edit them) ...

1. Create a _Packages/User/`<Name>`.sublime-color-scheme_ file.
2. Copy and paste the following rules into that file.
3. Set `"color_scheme"` user setting to _`<Name>`.sublime-color-scheme_.

!!! Info "Tip"

    1. **Step 3** can be ommitted if the overridden color scheme is a _*.sublime-color-scheme_ file.

    2. Sublime Text's _UI: Select Color Scheme_ command can be used to activate the color scheme.

    3. If _UI: Select Color Scheme_ is not available or the overridden color scheme is of the old `*.tmTheme` format use [Theme Menu Switcher](https://packagecontrol.io/packages/Themes%20Menu%20Switcher) to select the _Packages/User/`<Name>`.sublime-color-scheme_.


### User Defined Color Scheme

```JSON
{
    "rules":
    [
        {
            "scope": "markup.deleted.git_gutter",
            "foreground": "#F92672"
        },
        {
            "scope": "markup.changed.git_gutter",
            "foreground": "#967EFB"
        },
        {
            "scope": "markup.inserted.git_gutter",
            "foreground": "#A6E22E"
        },
        {
            "scope": "markup.ignored.git_gutter",
            "foreground": "#565656"
        },
        {
            "scope": "markup.untracked.git_gutter",
            "foreground": "#565656"
        },
        {
            "scope": "comment.line.annotation.git_gutter",
            "foreground": "#eee",
        }
    ]
}
```


## TextMate Color Scheme Format

`<Name>.tmTheme`

ⓘ _required for Sublime Text 2 or Sublime Text 3 before Build 3151_

If a color scheme file does not define the appropriate colors (or you want to edit them) ...

1. Copy the original color scheme to _Packages/User/`<Name>`.tmTheme_.
2. Add and modify the [required color scheme entries](#required-color-scheme-entries) listed below.
3. Set `"color_scheme"` user setting to the modified file or use [Theme Menu Switcher](https://packagecontrol.io/packages/Themes%20Menu%20Switcher) to activate it.

!!! warning "Caution"

    The duplicated user file will override any updates of the original color scheme. Therefore it is recommended to use [Sublime Text Color Scheme](#sublime-text-color-scheme-format) format if possible.


### Required Color Scheme Entries

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
<dict>
  <key>name</key>
  <string>GitGutter line annotation</string>
  <key>scope</key>
  <string>comment.line.annotation.git_gutter</string>
  <key>settings</key>
  <dict>
    <key>foreground</key>
    <string>#eee</string>
  </dict>  
</dict>
```


## Supported Color Schemes

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
