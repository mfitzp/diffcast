import sys
import difflib
import time
import argparse

INITIAL_SPEED = 3
TYPING_SPEED = 0.1
INSERT_SPEED = 1.5
DELETE_SPEED = 0.5

DIFF_NO_CHANGE = ' '
DIFF_INSERTION = '+'
DIFF_DELETION = '-'
DIFF_COMMENT = '?'



def rewrite_output_file(output_file, lines):
    with open(output_file, 'w') as fo:
        fo.writelines(lines)


def insert_line(output_file, current, line, diffline):
    current.insert(line, '\n')
    for n in range(len(diffline)):
        current[line] = diffline[:n] + '\n'
        time.sleep(TYPING_SPEED)
        rewrite_output_file(output_file, current)


def first_whitespace(s):
    return len(s) - len(s.lstrip())


def _indent_line(output_file, current, line, nindents):
    for n in range(nindents):
        current[line] = ' ' + current[line]
        time.sleep(TYPING_SPEED)
        rewrite_output_file(output_file, current)


def _dedent_line(output_file, current, line, ndedents):
    for n in range(ndedents):
        current[line] = current[line][1:]
        time.sleep(TYPING_SPEED)
        rewrite_output_file(output_file, current)


def indent_line(output_file, current, line, diffline):
    # diffline has our goal
    current_line = current[line]

    # check for indent difference, bring indent up to level first.
    cstart = first_whitespace(current_line)
    dstart = first_whitespace(diffline)
    
    # Fix indent differences if there are any.
    _indent_line(output_file, current, line, dstart-cstart)
    _dedent_line(output_file, current, line, cstart-dstart)


def edit_line(output_file, current, line, diffline):
    
    # diffline has our goal
    current_line = current[line]

    # find common start, common end, rewrite the middle.
    for n, (a, b) in enumerate(zip(current_line, diffline)):
        starti = n
        if a != b:
            break

    for n, (a, b) in enumerate(zip(current_line[::-1], diffline[::-1])):
        endi = n
        if a != b:
            break
    
    to_type_len = len(diffline) - (starti + endi)

    for n in range(to_type_len + 1):
        current[line] = current_line[:starti] + diffline[starti:starti+n] + current_line[-endi:]
        time.sleep(TYPING_SPEED)
        rewrite_output_file(output_file, current)

def play(output_file, files):
    print("Writing ", ' '.join(files), " to ", output_file)

    with open(files[0], 'r') as f1:
        current = f1.readlines()

    rewrite_output_file(output_file, current)    
    time.sleep(INITIAL_SPEED)

    for file in files[1:]:
        
        with open(file, 'r') as f2:
            target = f2.readlines()

        diff = difflib.Differ()
        delta = list(diff.compare(current, target))

        # Strip comments.
        delta = [d for d in delta if d[0] != DIFF_COMMENT]
        
        cl, dl = 0, 0  # current line, diff line
        while cl < len(current) -1:

            currline = current[cl]
            dc = delta[dl]
            
            first_char, diffline = dc[0], dc[2:]

            if first_char == DIFF_NO_CHANGE:
                # continue
                cl += 1
                dl += 1
                continue
            
            if dl < len(delta) -1:
                # Handle subsequent edit lines, delete>insert = modify
                dn = delta[dl+1]
                next_char, nextdiffline = dn[0], dn[2:]
            else:
                next_char = None

            if (first_char, next_char) == (DIFF_DELETION, DIFF_INSERTION):
                # Correct the indentation of the line.
                indent_line(output_file, current, cl, nextdiffline)
                # Modify diffline to nextdiffline.
                edit_line(output_file, current, cl, nextdiffline)
                dl += 2  # Advance diff 2, deletion & insertion.
                cl += 1
                time.sleep(INSERT_SPEED)
                continue
            
            if first_char == DIFF_DELETION:
                del current[cl]  # don't increment cl.
                rewrite_output_file(output_file, current)
                dl += 1
                time.sleep(DELETE_SPEED)
                continue

            if first_char == DIFF_INSERTION:
                # add a line at cl in current
                insert_line(output_file, current, cl, diffline)
                cl += 1
                dl += 1
                time.sleep(INSERT_SPEED)
                continue
            

parser = argparse.ArgumentParser(prog="diffplay", description='Replay a series of edits to files.')
parser.add_argument('output_file', help='Output file where playback will be written to.')
parser.add_argument('files', metavar='N', nargs='+',
                    help='The series of files to apply. The first file is the starting point.')

args = parser.parse_args()

play(args.output_file, args.files)