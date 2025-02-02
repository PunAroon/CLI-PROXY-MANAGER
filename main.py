import curses
from curses import textpad
import json
import os
import re
import requests  # For proxy testing

PROXY_FILE = "proxies.json"
PROXY_ASCII = r"""
⠀⠀⠀▄███████▄    ▄████████  ▄██████▄  ▀████    ▐████▀ ▄██   ▄          ▄▄▄▄███▄▄▄▄      ▄████████ ███▄▄▄▄      ▄████████    ▄██████▄     ▄████████    ▄████████ 
  ███    ███   ███    ███ ███    ███   ███▌   ████▀  ███   ██▄      ▄██▀▀▀███▀▀▀██▄   ███    ███ ███▀▀▀██▄   ███    ███   ███    ███   ███    ███   ███    ███ 
  ███    ███   ███    ███ ███    ███    ███  ▐███    ███▄▄▄███      ███   ███   ███   ███    ███ ███   ███   ███    ███   ███    █▀    ███    █▀    ███    ███ 
  ███    ███  ▄███▄▄▄▄██▀ ███    ███    ▀███▄███▀    ▀▀▀▀▀▀███      ███   ███   ███   ███    ███ ███   ███   ███    ███  ▄███         ▄███▄▄▄      ▄███▄▄▄▄██▀ 
▀█████████▀  ▀▀███▀▀▀▀▀   ███    ███    ████▀██▄     ▄██   ███      ███   ███   ███ ▀███████████ ███   ███ ▀███████████ ▀▀███ ████▄  ▀▀███▀▀▀     ▀▀███▀▀▀▀▀   
  ███        ▀███████████ ███    ███   ▐███  ▀███    ███   ███      ███   ███   ███   ███    ███ ███   ███   ███    ███   ███    ███   ███    █▄  ▀███████████ 
  ███          ███    ███ ███    ███  ▄███     ███▄  ███   ███      ███   ███   ███   ███    ███ ███   ███   ███    ███   ███    ███   ███    ███   ███    ███ 
 ▄████▀        ███    ███  ▀██████▀  ████       ███▄  ▀█████▀        ▀█   ███   █▀    ███    █▀   ▀█   █▀    ███    █▀    ████████▀    ██████████   ███    ███ 
               ███    ███                                                                                                                           ███    ███ 
                                                                                                                                               © 2025 PUNAROON
"""

def check_terminal_size(stdscr):
    """Check if terminal is large enough to display content"""
    min_y, min_x = 30, 80  # Minimum terminal size
    max_y, max_x = stdscr.getmaxyx()
    if max_y < min_y or max_x < min_x:
        return False
    return True

def validate_proxy(proxy):
    """Validate proxy structure with new fields"""
    required = {'id', 'name', 'server', 'port', 'type', 'active', 'user', 'password'}
    if not all(key in proxy for key in required):
        return False
    
    try:
        if not isinstance(proxy['id'], int) or \
           not isinstance(proxy['name'], str) or \
           not isinstance(proxy['server'], str) or \
           not isinstance(proxy['port'], int) or \
           not isinstance(proxy['type'], str) or \
           not isinstance(proxy['active'], bool) or \
           not isinstance(proxy['user'], str) or \
           not isinstance(proxy['password'], str):
            return False
        
        valid_types = {"HTTP", "HTTPS", "SOCKS4", "SOCKS5"}
        if proxy['type'] not in valid_types:
            return False
        
        return True
    except (TypeError, ValueError):
        return False

def load_proxies():
    """Load and validate proxies, handling legacy format"""
    if not os.path.exists(PROXY_FILE):
        with open(PROXY_FILE, 'w') as f:
            json.dump([], f)
        return []

    try:
        with open(PROXY_FILE, 'r') as f:
            proxies = json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

    validated = []
    existing_ids = set()
    
    for proxy in proxies:
        # Handle legacy fields
        proxy.setdefault('user', '')
        proxy.setdefault('password', '')
        proxy.setdefault('id', 0)
        
        # Convert port if stored as string
        if isinstance(proxy['port'], str) and proxy['port'].isdigit():
            proxy['port'] = int(proxy['port'])
            
        if validate_proxy(proxy):
            # Ensure unique ID
            while proxy['id'] in existing_ids or proxy['id'] == 0:
                proxy['id'] = max(existing_ids, default=0) + 1
            existing_ids.add(proxy['id'])
            validated.append(proxy)

    return validated

def save_proxies(proxies):
    """Save validated proxies to JSON file"""
    with open(PROXY_FILE, 'w') as f:
        json.dump([p for p in proxies if validate_proxy(p)], f, indent=2)

def parse_proxy_string(proxy_str):
    """Parse proxy string in format hostname:port@username:password"""
    pattern = r'^(.*?):(\d+)@(.*?):(.*)$'
    match = re.match(pattern, proxy_str)
    if match:
        return {
            'server': match.group(1),
            'port': int(match.group(2)),
            'user': match.group(3),
            'password': match.group(4)
        }
    return None

def add_proxy_from_string(stdscr, proxies, proxy_str):
    """Add proxy from formatted string"""
    parsed = parse_proxy_string(proxy_str)
    if not parsed:
        stdscr.addstr(0, 0, "Invalid proxy format! Use hostname:port@username:password", curses.color_pair(4))
        stdscr.refresh()
        stdscr.getch()
        return False

    # Generate unique ID
    existing_ids = {p['id'] for p in proxies}
    new_id = max(existing_ids, default=0) + 1
    
    new_proxy = {
        'id': new_id,
        'name': f"Proxy {new_id}",
        'server': parsed['server'],
        'port': parsed['port'],
        'type': "HTTP",  # Default type
        'active': False,
        'user': parsed['user'],
        'password': parsed['password']
    }
    
    if validate_proxy(new_proxy):
        proxies.append(new_proxy)
        save_proxies(proxies)
        return True
    return False

def add_bulk_proxies(stdscr, proxies, proxy_str):
    """Add multiple proxies from a formatted string"""
    lines = proxy_str.strip().split('\n')
    success_count = 0
    for line in lines:
        if add_proxy_from_string(stdscr, proxies, line):
            success_count += 1
    return success_count

def export_proxies(proxies, filename="proxies_export.json"):
    """Export proxies to a file"""
    try:
        with open(filename, 'w') as f:
            json.dump(proxies, f, indent=2)
        return True
    except IOError:
        return False

def import_proxies(filename="proxies_export.json"):
    """Import proxies from a file"""
    try:
        with open(filename, 'r') as f:
            new_proxies = json.load(f)
        return new_proxies
    except (IOError, json.JSONDecodeError):
        return None

def test_proxy(proxy):
    """Test if a proxy is active and reachable"""
    try:
        proxies = {
            "http": f"{proxy['type'].lower()}://{proxy['user']}:{proxy['password']}@{proxy['server']}:{proxy['port']}",
            "https": f"{proxy['type'].lower()}://{proxy['user']}:{proxy['password']}@{proxy['server']}:{proxy['port']}"
        }
        response = requests.get("http://example.com", proxies=proxies, timeout=5)
        return response.status_code == 200
    except:
        return False

def sort_proxies(proxies, key='id'):
    """Sort proxies by a given key"""
    return sorted(proxies, key=lambda x: x[key])

def draw_ascii_art(stdscr):
    max_y, max_x = stdscr.getmaxyx()
    ascii_lines = PROXY_ASCII.strip().split('\n')
    start_y = 3
    
    for i, line in enumerate(ascii_lines):
        x = max_x//2 - len(line)//2
        try:
            stdscr.addstr(start_y + i, x, line, curses.color_pair(3))
        except curses.error:
            pass

def draw_status(stdscr, active_proxies, total_proxies):
    max_y, max_x = stdscr.getmaxyx()
    status_str = f" Active Proxies: {active_proxies} | Total Proxies: {total_proxies} "
    stdscr.addstr(max_y//4 + 1, max_x//2 - len(status_str)//2, status_str, curses.color_pair(2))

def draw_proxies(stdscr, selected_idx, proxies):
    max_y, max_x = stdscr.getmaxyx()
    start_y = max_y//3 + 2
    width = min(max_x - 4, 80)
    start_x = max_x//2 - width//2

    for idx, proxy in enumerate(proxies):
        y = start_y + idx
        color = curses.color_pair(1) if proxy['active'] else curses.color_pair(4)
        status = "✓" if proxy['active'] else "✗"
        
        if idx == selected_idx:
            stdscr.attron(curses.color_pair(5))
            stdscr.addstr(y, start_x, " " * width)
            stdscr.attroff(curses.color_pair(5))
        
        auth = ""
        if proxy['user']:
            auth = f" ({proxy['user']}:{'*'*len(proxy['password'])})"
        proxy_str = f" {status} [{proxy['id']}] {proxy['name']} ({proxy['type']}) - {proxy['server']}:{proxy['port']}{auth} "
        try:
            stdscr.addstr(y, start_x, proxy_str[:width-2], curses.color_pair(5) if idx == selected_idx else color)
        except curses.error:
            pass

def edit_proxy(stdscr, proxy):
    max_y, max_x = stdscr.getmaxyx()
    fields = [
        ("Name", proxy['name']),
        ("Server", proxy['server']),
        ("Port", str(proxy['port'])),
        ("Type", proxy['type']),
        ("Username", proxy['user']),
        ("Password", proxy['password']),
    ]
    current_field = 0
    types = ["HTTP", "HTTPS", "SOCKS4", "SOCKS5"]

    while True:
        stdscr.clear()
        draw_ascii_art(stdscr)
        stdscr.addstr(max_y//4 + 3, max_x//2 - 10, "Edit Proxy Settings", curses.color_pair(2))
        
        for i, (label, value) in enumerate(fields):
            y = max_y//3 + 2 + i*2
            stdscr.addstr(y, max_x//2 - 15, f"{label}:", curses.color_pair(2))
            if i == current_field:
                stdscr.attron(curses.color_pair(5))
                stdscr.addstr(y, max_x//2 - 10, " " * 30)
                stdscr.addstr(y, max_x//2 - 10, value, curses.color_pair(5))
                stdscr.attroff(curses.color_pair(5))
            else:
                stdscr.addstr(y, max_x//2 - 10, value)
        
        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and current_field > 0:
            current_field -= 1
        elif key == curses.KEY_DOWN and current_field < len(fields)-1:
            current_field += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            if current_field == len(fields)-1:
                break
        elif key == 27:  # ESC
            return None
        elif current_field == 3:  # Type selection
            if key == curses.KEY_LEFT:
                idx = (types.index(fields[3][1]) - 1) % len(types)
                fields[3] = ("Type", types[idx])
            elif key == curses.KEY_RIGHT:
                idx = (types.index(fields[3][1]) + 1) % len(types)
                fields[3] = ("Type", types[idx])
        else:
            if current_field == 2:  # Port number
                if key == curses.KEY_BACKSPACE or key == 127:
                    fields[2] = ("Port", fields[2][1][:-1])
                elif 48 <= key <= 57:  # Numeric input
                    fields[2] = ("Port", fields[2][1] + chr(key))
            else:
                if key == curses.KEY_BACKSPACE or key == 127:
                    fields[current_field] = (fields[current_field][0], fields[current_field][1][:-1])
                elif 32 <= key <= 126:
                    fields[current_field] = (fields[current_field][0], fields[current_field][1] + chr(key))

    return {
        "id": proxy.get('id', 0),
        "name": fields[0][1],
        "server": fields[1][1],
        "port": int(fields[2][1]),
        "type": fields[3][1],
        "active": proxy['active'],
        "user": fields[4][1],
        "password": fields[5][1]
    }

def main(stdscr):
    if not check_terminal_size(stdscr):
        stdscr.addstr(0, 0, "Terminal too small! Resize to at least 80x30.", curses.color_pair(4))
        stdscr.refresh()
        stdscr.getch()
        return

    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_WHITE)
    
    proxies = load_proxies()
    current_selection = 0 if proxies else -1
    
    while True:
        stdscr.clear()
        max_y, max_x = stdscr.getmaxyx()
        
        draw_ascii_art(stdscr)
        
        active_proxies = sum(1 for p in proxies if p['active'])
        draw_status(stdscr, active_proxies, len(proxies))
        
        if proxies:
            draw_proxies(stdscr, current_selection, proxies)
        else:
            stdscr.addstr(max_y//2, max_x//2 - 10, "No proxies found. Press 'a' to add.", curses.color_pair(4))
        
        help_text = " ↑/↓: Navigate | Enter: Toggle | A: Add | E: Edit | D: Delete | P: Paste Proxy | S: Sort | T: Test | X: Export | I: Import | Q: Quit "
        stdscr.addstr(max_y-2, max_x//2 - len(help_text)//2, help_text, curses.color_pair(2))
        
        stdscr.refresh()
        key = stdscr.getch()
        
        if key == curses.KEY_UP and current_selection > 0:
            current_selection -= 1
        elif key == curses.KEY_DOWN and current_selection < len(proxies) - 1:
            current_selection += 1
        elif key == curses.KEY_ENTER or key in [10, 13] and proxies:
            proxies[current_selection]['active'] = not proxies[current_selection]['active']
            save_proxies(proxies)
        elif key == ord('a'):
            new_proxy = {
                "id": max((p['id'] for p in proxies), default=0) + 1,
                "name": "New Proxy",
                "server": "server.com",
                "port": 8080,
                "type": "HTTP",
                "active": False,
                "user": "",
                "password": ""
            }
            edited = edit_proxy(stdscr, new_proxy)
            if edited:
                proxies.append(edited)
                save_proxies(proxies)
                current_selection = len(proxies)-1
        elif key == ord('e') and proxies:
            edited = edit_proxy(stdscr, proxies[current_selection])
            if edited:
                proxies[current_selection] = edited
                save_proxies(proxies)
        elif key == ord('d') and proxies:
            if len(proxies) > 1:  # Ensure there's more than one proxy before allowing deletion
                stdscr.clear()
                draw_ascii_art(stdscr)
                stdscr.addstr(max_y//2 - 2, max_x//2 - 20, "Are you sure you want to delete this proxy? (y/n)", curses.color_pair(4))
                stdscr.refresh()
                confirm = stdscr.getch()
                if confirm == ord('y'):
                    del proxies[current_selection]
                    save_proxies(proxies)
                    current_selection = max(0, current_selection-1) if proxies else -1
                else:
                    stdscr.clear()
                    draw_ascii_art(stdscr)
                    stdscr.addstr(max_y//2, max_x//2 - 20, "Deletion canceled.", curses.color_pair(2))
                    stdscr.refresh()
                    stdscr.getch()
            else:
                stdscr.addstr(max_y//2, max_x//2 - 20, "Cannot delete the last proxy.", curses.color_pair(4))
                stdscr.refresh()
                stdscr.getch()
        elif key == ord('p'):
            stdscr.clear()
            draw_ascii_art(stdscr)
            stdscr.addstr(max_y//2 - 2, max_x//2 - 20, "Paste proxies (one per line, host:port@user:pass):", curses.color_pair(2))
            curses.echo()

            # Increase the buffer size (allow longer input)
            proxy_str = stdscr.getstr(max_y//2, max_x//2 - 20, 160).decode('utf-8')  # 160 characters buffer size
            curses.noecho()

            success_count = add_bulk_proxies(stdscr, proxies, proxy_str)
            stdscr.clear()
            draw_ascii_art(stdscr)
            stdscr.addstr(max_y//2, max_x//2 - 20, f"Added {success_count} proxies successfully!", curses.color_pair(2))
            stdscr.refresh()
            stdscr.getch()
        elif key == ord('s'):  # Simplify sorting
            stdscr.clear()
            draw_ascii_art(stdscr)
            stdscr.addstr(max_y//2 - 2, max_x//2 - 20, "Sort by: (i) ID, (n) Name, (t) Type", curses.color_pair(2))
            stdscr.refresh()
            sort_key = stdscr.getch()
            if sort_key == ord('i'):
                proxies = sort_proxies(proxies, 'id')
            elif sort_key == ord('n'):
                proxies = sort_proxies(proxies, 'name')
            elif sort_key == ord('t'):
                proxies = sort_proxies(proxies, 'type')
            save_proxies(proxies)
        elif key == ord('t') and proxies:  # Test selected proxy
            if test_proxy(proxies[current_selection]):
                stdscr.addstr(0, 0, "Proxy is active and reachable!", curses.color_pair(2))
            else:
                stdscr.addstr(0, 0, "Proxy is unreachable!", curses.color_pair(4))
            stdscr.refresh()
            stdscr.getch()
        elif key == ord('x'):  # Export proxies
            if export_proxies(proxies):
                stdscr.addstr(0, 0, "Proxies exported successfully!", curses.color_pair(2))
            else:
                stdscr.addstr(0, 0, "Failed to export proxies!", curses.color_pair(4))
            stdscr.refresh()
            stdscr.getch()
        elif key == ord('i'):  # Import proxies
            imported = import_proxies()
            if imported:
                proxies.extend(imported)
                save_proxies(proxies)
                stdscr.addstr(0, 0, "Proxies imported successfully!", curses.color_pair(2))
            else:
                stdscr.addstr(0, 0, "Failed to import proxies!", curses.color_pair(4))
            stdscr.refresh()
            stdscr.getch()
        elif key == ord('q') or key == ord('Q'):
            break

if __name__ == "__main__":
    curses.wrapper(main)
