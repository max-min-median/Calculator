import curses

def get_key(window):
    key = window.getch()
    if key == 27: # CTRL+c
        raise KeyboardInterrupt
    return key

def main():
    # Initialize curses
    stdscr = curses.initscr()

    # Turn off echoing of keys, and enter cbreak mode,
    # where no buffering is performed on keyboard input
    curses.noecho()
    curses.raw()

    # In keypad mode, escape sequences for special keys
    # (like the cursor keys) will be interpreted and
    # a special value like curses.KEY_LEFT will be returned
    stdscr.keypad(1)

    # Start color, too.  Harmless if the terminal doesn't have
    # color; user can test with has_color() later on.  The try/catch
    # works around a minor bit of over-conscientiousness in the curses
    # module -- the error return from C start_color() is ignorable.
    try:
        curses.start_color()
    except:
        pass

    # win = curses.newwin(height, width, begin_y, begin_x)
    stdscr.scrollok(1)
    k = None
    while k != 27:
        k = get_key(stdscr)
        stdscr.addstr(f'key {str(k)} typed.\n')
        stdscr.refresh()

if __name__ == "__main__":
    main()