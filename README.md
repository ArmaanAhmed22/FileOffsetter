## The "FileOffsetter" Tool
This is the beginning of a versatile tool that can be used to offset regions - for now numbers - of files' names.

Do:
```bash
	./offset.py -h
```
to get started and learn how to use it!

The match (the part you want to offset) looks like this: `[n#]`, where n represents the place of the digit you want to offset (the ones place is `1` (or empty by default); the tens place is `2`, etc). Add this to the `-m` flag to dictate the where exactly you want to offset and what you want to offset.

`-m hello_[2#].txt` says you want to only consider files looking like `hello_\d+.txt` and you specifically want to offset the tens place of the number represented by `\d+`  

**NOTE**: This tool is not <em>yet</em> completed. For the Regex generalization, you can't use wildcards or unknown quantifiers (e.g. '+'). 
