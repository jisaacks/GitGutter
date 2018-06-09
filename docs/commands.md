# Commands-API

## Goto Previous/Next Change

 Command                   | Description
---------------------------|-------------
`"git_gutter_prev_change"` | Goto Previous Change
`"git_gutter_next_change"` | Goto Next Change


### Arguments

Argument | Values      | Default | Description
:-------:|:-----------:|:-------:|--------------------------------------
count    | >=1         |    1    | The number of iterations to find destination hunk
wrap     | False, True |  True   | enable/disable wrapping at document boundaries


### Example

Jump forward to the next but one change and stop if no more changes follow up to the end of file.

**Macro**

```JSON
{ 
    "command": "git_gutter_next_change", 
    "args": {
        "count": 2, 
        "wrap": false
    }
}
```

**Plugin**

```python
view.run_command(
    "git_gutter_next_change", 
    {
        "args": {
            "count": 2, 
            "wrap": False
        }
    }
)
```
