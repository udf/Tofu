#!/usr/bin/python3

import fontforge
import progressbar
import argparse
import os

TEMP_FILE = 'temp.sfd'

def irange(start, end=None):
    if end is None:
        return range(start+1)
    else:
        return range(start, end+1)

def align_point(i, count, item_size, spacing, total_size, reverse=False):
    if reverse:
        i = count - i - 1
    # remaining_space / 2 + current_item * size_of_one_item
    # remaining_space = total_size - space_taken_by_all_items
    return (total_size - (count * (item_size + spacing) - spacing)) / 2 + i * (item_size + spacing)

def main():
    parser = argparse.ArgumentParser(description='Generate Tofu font.')

    parser.add_argument('start', metavar='Start', type=str, nargs=1,
                    help='hex code for beginning char. Ex. 0000 or 1000')

    parser.add_argument('end', metavar='End', type=str, nargs=1,
                    help='hex code for ending char. Ex. 0FFF or FFFF')

    parser.add_argument('-t', '--ttf', action='store_true',
                    help='output to an ttf file rather than otf')

    args = parser.parse_args()

    start_str = args.start[0].upper()
    end_str = args.end[0].upper()

    if len(start_str) > 5 or len(start_str) < 4:
        print('Start argument must be 4 or 5 characters long. Ex. 0000 or 10000.')
        exit(2)

    if len(end_str) > 5 or len(end_str) < 4:
        print('End argument must be 4 or 5 characters long. Ex. 0000 or 10000.')
        exit(2)

    try:
        start = int(start_str, 16)
    except ValueError:
        print('Start argument must only contain hexadecimal characters.')
        exit(2)

    try:
        end = int(end_str, 16)
    except ValueError:
        print('End argument must only contain hexadecimal characters.')
        exit(2)

    if start >= end:
        print('Start must be less than end')
        exit(2)

    if (end - start + (1 if args.ttf else 2) + 17) > 65535:
        print('Range is (note: 17 spaces are reserved for template glyphs)', end - start + 1 + 17)

        if args.otf:
            print('Range max is 65534 characters long. Otf includes one by default?')
        else:
            print('Range max is 65535 characters long.')
        exit(2)


    print('Generating Tofu for unicode characters between U+{} and U+{}'.format(start_str, end_str))

    # return
    progressbar.streams.wrap_stderr()
    bar = progressbar.ProgressBar()

    # load template as string
    font_template = None
    with open('template.sfd') as file:
        font_template = file.read()

    # build sfd by adding each character
    font_data = [font_template]
    for i in bar(irange(start, end)):
        font_data.append(gen_char(i))

    # save sfd to disk (todo: figure out how to avoid saving)
    with open(TEMP_FILE, 'w') as file:
        file.write('\n'.join(font_data))

    print('Loading spline database')
    # load our sfd and generate a usable font from it
    font = fontforge.open(TEMP_FILE)
    os.remove(TEMP_FILE)
    font.familyname = 'Tofu'
    font.fontname = 'Tofu'
    font.fullname = 'Tofu {} - {}'.format(start_str, end_str)
    font.comment = 'The complete opposite of a font'
    font.version = '0.1'
    font.copyright = open('FONT_LICENSE', 'r').read()

    save_name = 'tofu_{}_{}.{}'.format(start_str, end_str, 'ttf' if args.ttf else 'otf')
    print('Saving as {}'.format(save_name))
    font.generate(save_name, flags=('short-post',))


def gen_char(codepoint):
    hex_str = '{:X}'.format(codepoint)
    hex_str = hex_str.zfill(6 if len(hex_str) > 4 else 4)

    # todo: make this better
    x_count = len(hex_str) // 2
    y_count = len(hex_str) // x_count

    references = ['Refer: 0 -1 N 1 0 0 1 0 0 2']
    for i,c in enumerate(hex_str):
        references.append(
            'Refer: {id_glyph} -1 N 1 0 0 1 {x} {y} 2'.format(
                id_glyph=int(c, 16) + 1,
                x=align_point(i % 2, x_count, 255, 90, 1000),
                y=align_point(i // 2, y_count, 425, 90, 1000, True) - 200
            )
        )

    return (
        'StartChar: uni{codepoint}\n'
        'Encoding: {id_font} {id_uni} {id_glyph}\n'
        'Width: 1000\n'
        'Flags: HW\n'
        'LayerCount: 2\n'
        'Fore\n'
        '{references}\n'
        'EndChar\n'
    ).format(
        codepoint=hex_str,
        id_font=codepoint,
        id_uni=codepoint,
        id_glyph=codepoint+17,
        references='\n'.join(references),
    )

if __name__ == '__main__':
    main()