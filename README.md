<p align="center">
  <img src="diffcast/images/icon.png" />
</p>


# DiffCast

***Hands-free Programming Screencasts from Python source files.***

Provided with a series of Python files, DiffCast automatically generates coding
demos/screencasts using human-like edits. Designed for creating reproducible
tutoring examples, library demos or demonstrating code to a class.

Avoid distracting typos, reduce video editing time, narrate code changes without "umms and aaahss",
make screencast creation more accessible for people with disabilities. Regular editing speed makes demos easier to follow.

<video src="https://user-images.githubusercontent.com/126239/151336478-82f31091-5138-42b2-8fe5-6e3fd5cdfc72.mp4"></video>

## What?

Programming screencasts are a popular way to teach programming and demo tools. Typically people will open up their favorite editor and record themselves tapping away. But this has a few problems. A good setup for coding isn't necessarily a good setup for video -- with text too small, a window too big, or too many distractions. Typing code in live means inevitable mistakes, even more so if you're narrating what you're doing at the same time. Mistakes means more time editing or confusion for the people watching.

**DiffCast** is an attempt to eliminate that, by generating screencasts from *testable* fully-working examples you prepare ahead of time. The editor view is configured to be large & easily readable in video, without messing with your IDE settings. Edits happen at a regular speed, without mistakes, making them easy to follow. Each _diffcast_ is completely reproducible, with the same files producing the same output every time.

## Install

* [Windows Installer](https://github.com/mfitzp/diffcast/releases/download/v0.0.1/DiffCast.exe)
* [macOS Installer](https://github.com/mfitzp/diffcast/releases/download/v0.0.1/DiffCast.dmg)

## Demos

Below are some examples of screencasts created using DiffCast. These are short examples, to keep things readable but there is no limit to the number of transition files you can use, or how long the resulting DiffCast can be.

### Simple demo

_Shorter demo, using the 4 demoN.py files in /demos._

Give the following 4 files 

```python
print('Hello, world!')
```

```python
name = input('What is your name?\n')
print(f'Hello, {name}!')
```

```python
friends = ['Emelia', 'Jack', 'Bernardina', 'Jaap']

name = input('What is your name?\n')

if name in friends:
    print(f'Hello, {name}!')
else:
    print("I don't know you.")
```

```python
friends = ['Emelia', 'Jack', 'Bernardina', 'Jaap']

while True:
    name = input('What is your name?\n')
    
    if name in friends:
        print(f'Hello, {name}!')
    else:
        print("I don't know you.")
        friends.append(name)
```

**DiffCast** will produce the following screencast.

<video src="https://user-images.githubusercontent.com/126239/151181856-5484da69-12dd-4f20-b652-3c55aeb2da73.mp4"></video>

### Longer demo

_Longer demo, using the 6 windows_N.py files in /demos. Demonstrates more complex edits, whitespace padding._
<video src="https://user-images.githubusercontent.com/126239/151128026-531c46db-30cb-466a-a836-8818718a2b13.mp4"></video>


## Interface

DiffCast costs of two windows -- (1) the code viewer and (2) the controller.

![diffcast-demo-windows](https://user-images.githubusercontent.com/126239/151141472-ee71096a-d9d1-4843-9614-aef323e398ec.png)

Configure the size of the code viewer component.

![diffcast-demo-size](https://user-images.githubusercontent.com/126239/151141490-ddc18d73-1116-478d-a848-a1dccecd2cbe.png)

Add your intermediate files for generating the DiffCast from & then select the file in the list to start from.

![diffcast-demo-files](https://user-images.githubusercontent.com/126239/151141504-084c6789-6be7-4151-977f-a32b44cbf62c.png)

Clicking *Start* will start playing a DiffCast from the currently selected file. The first file will be loaded *as-is* and then edited until it matches the 2nd file, and then 3rd file and so on. You can *Stop* the DiffCast at any time. The *Prev* and *Next* buttons can be used to create DiffCasts stepping manually forwards (or backwards) through the changes, for example if you are demonstrating to a class.

![diffcast-demo-controls](https://user-images.githubusercontent.com/126239/151141563-b2a0d9f9-8773-4eb8-9409-79c943b9248f.png)

Sometimes you want your current code to be *runnable* in a particular location -- for example, if you want to bring up a shell and run the same file as the changes are demonstrated. In this case you can use *Select output file...* to select the file to write the latest version to. Only the final working files are written (the state *after* the diff) so it will always work.

![diffcast-demo-output](https://user-images.githubusercontent.com/126239/151141588-b2f84633-6239-4c50-a929-afde83b55ca6.png)

You can optionally show a file listing next to the code viewer, which will default to showing the selected output file in it's folder.

![diffcast-demo-editor-filelist](https://user-images.githubusercontent.com/126239/151141686-41bab266-7c15-464c-b73e-2bfce1a48e61.png)

## FAQ

Some questions you'll probably ask.

### What do you mean by human-like edits?

When you edit a file you *generally* go from top to bottom, but you don't enter lines perfectly in order or delete lines before retyping them. To make the edits appear natural DiffCast tries to replicate some of these behaviors. Some examples --

* If you're adding a block of code which is followed by a blank line, a trailing blank line will be added first (adding space around the new code).
* Changes to the middle of lines will be edited in the middle of the line, leaving leading and trailing parts intact during editing.
* Whitespace is added in blocks of 4 (emulating tab indent) where possible.
* Blocks are indented as a whole, where possible.

This is a work in progress and new edits may be added.

### Does DiffCast create videos?

Not yet. But you can record the window using any normal screen recording software. It includes a few preset window sizes ideal for generating videos.

### Can I change the order edits are made?

Sure. Just add more intermediate files. For example, if you want to make edits to the bottom of a method before the top, you can create an intermediate file with the later edits and they will be applied first.

### Is this Python only?

Yes, right now. But the viewer component uses QScintilla as the editing component which includes lexers for many other languages (including AVS, Bash, Batch, CMake, CoffeeScript, CPP, D, Diff, Fortran77, HTML, JSON, Lua, Makefile, Markdown, Matlab, Pascal, Perl, PostScript, Python, Ruby, Spice, SQL, TCL, TeX, Verilog, VHDL and YAML). Other language support and syntax highlighting configuration will be added in a later version, if there is interest.


### Can you DiffCast through git commits?

Not yet, but it's a nice idea.
