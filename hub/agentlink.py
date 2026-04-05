import os
import json
import sys
import requests
import threading
import time
import subprocess
import argparse
import textwrap
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.table import Table
from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style as PromptStyle

console = Console()
REGISTRY_PATH = "/root/AgentLink/hub/registry.json"
API_TOKEN = "agentlink_secret_123"

# Institutional Palette
C_PRIMARY = "#5f87af" # Steel Blue
C_SECONDARY = "#ffaf00" # Industrial Amber
C_ACCENT = "#87af87" # Sage Green
C_DIM = "#444444"
C_WHITE = "#eeeeee"

def get_headers():
    return {"Authorization": f"Bearer {API_TOKEN}"}

def load_registry():
    if not os.path.exists(REGISTRY_PATH): return []
    with open(REGISTRY_PATH, 'r') as f:
        try: return json.load(f)
        except: return []

def get_ascii_header():
    width = console.width
    
    # Static Pixel-Perfect Components
    # Bot: 19 chars
    b_lines = [
        r"     .───────.     ",
        r"    o| o   o |o    ",
        r"     |  ───  |     ",
        r"     '───────'     ",
        r"      /─────\      "
    ]
    
    # Agent: 44 chars
    a_lines = [
        " █████   ██████  ███████ ███    ██ ████████ ",
        "██   ██ ██       ██      ████   ██    ██    ",
        "███████ ██   ███ █████   ██ ██  ██    ██    ",
        "██   ██ ██    ██ ██      ██  ██ ██    ██    ",
        "██   ██  ██████  ███████ ██   ████    ██    "
    ]
    
    # Link: 33 chars
    l_lines = [
        "██      ██ ███    ██ ██   ██     ",
        "██      ██ ████   ██ ██  ██      ",
        "██      ██ ██ ██  ██ █████       ",
        "██      ██ ██  ██ ██ ██  ██      ",
        "███████ ██ ██   ████ ██   ██     "
    ]

    # Tier 1: Ultra-Compact (< 80 chars)
    if width < 80:
        header_text = Text.from_markup(f"[bold {C_SECONDARY}]〈[ o ─-─ o ]〉[/] [bold {C_PRIMARY}]AGENT[/][bold {C_ACCENT}]LINK[/]")
        return Align.center(Panel(header_text, border_style=C_PRIMARY, padding=(0, 2)))

    # Tier 2: Mid-Size (Logo Only, 80-120 chars)
    if width < 125:
        mid_content = []
        for i in range(5):
            line = Text()
            line.append(a_lines[i], style=f"bold {C_PRIMARY}")
            line.append(l_lines[i], style=f"bold {C_ACCENT}")
            mid_content.append(line)
        return Align.center(Text.assemble(*[ln + "\n" for ln in mid_content]))

    # Tier 3: Full Industrial (Bots + Logo, > 125 chars)
    # Using a Table Grid to lock alignment and prevent slanting
    grid = Table.grid(expand=False)
    grid.add_column(width=21, justify="right") # Left Bot
    grid.add_column(width=79, justify="center") # Logo
    grid.add_column(width=21, justify="left") # Right Bot

    for i in range(5):
        bot_l = Text(b_lines[i], style=f"bold {C_SECONDARY}")
        
        logo = Text()
        logo.append(a_lines[i], style=f"bold {C_PRIMARY}")
        logo.append(l_lines[i], style=f"bold {C_ACCENT}")
        
        bot_r = Text(b_lines[i], style=f"bold {C_SECONDARY}")
        
        grid.add_row(bot_l, logo, bot_r)

    return Align.center(grid)

def list_servers():
    registry = load_registry()
    table = Table(box=None, header_style=f"bold {C_SECONDARY}")
    table.add_column("NODE IDENTITY", style=C_PRIMARY, width=22)
    table.add_column("IPV4 ADDRESS", style="white", width=15)
    table.add_column("LINK STATUS", width=15)
    for node in registry:
        try:
            r = requests.get(f"http://{node['ip']}:8092/status", headers=get_headers(), timeout=1)
            status = f"[bold {C_ACCENT}]● OPERATIONAL[/bold {C_ACCENT}]" if r.status_code == 200 else "[bold red]○ DISCONNECTED[/bold red]"
        except: status = "[bold red]○ DISCONNECTED[/bold red]"
        table.add_row(node['name'].upper(), node['ip'], status)
    return Panel(table, title=f"[bold {C_WHITE}]Managed Fleet Core[/bold {C_WHITE}]", border_style=C_PRIMARY, expand=False)

def posses_server(name):
    registry = load_registry()
    node = next((n for n in registry if n['name'] == name), None)
    if not node: return
    ip = node['ip']
    console.clear()
    console.print(get_ascii_header())
    
    box_width = min(console.width - 2, 124)
    inner_w = box_width - 6
    
    # Session Header
    console.print(Align.center(Panel(
        Align.center(f"[bold {C_WHITE}]SECURE UPLINK:[/bold {C_WHITE}] [bold {C_PRIMARY}]{name.upper()}[/bold {C_PRIMARY}] @ {ip}\n[dim]Protocol: Neural-PTY | Encryption: Industrial Strength[/dim]"),
        border_style=C_ACCENT,
        title=f"[bold {C_ACCENT}]SESSION INITIALIZED[/bold {C_ACCENT}]",
        width=box_width
    )))

    stop_event = threading.Event()
    state = {"active_model": "gemini", "is_started": False}

    def boxed_print(text, color=C_WHITE):
        for line in text.splitlines():
            segments = textwrap.wrap(line, width=inner_w) if line.strip() else [""]
            for segment in segments:
                padding = " " * (inner_w - len(segment))
                print_formatted_text(HTML(f'<style fg="{C_ACCENT}"> │ </style> <style fg="{color}">{segment}</style>{padding} <style fg="{C_ACCENT}">│</style>'))

    def log_tailer():
        last_logs = ""
        while not stop_event.is_set():
            try:
                status_r = requests.get(f"http://{ip}:8092/status", headers=get_headers(), timeout=1)
                if status_r.status_code == 200:
                    data = status_r.json()
                    state["active_model"] = data.get("active_model", "gemini")
                    state["is_started"] = data.get("started", False)
                if state["is_started"]:
                    r = requests.get(f"http://{ip}:8092/logs", headers=get_headers(), timeout=2)
                    if r.status_code == 200:
                        new_logs = r.text
                        if new_logs != last_logs:
                            diff = new_logs[len(last_logs):]
                            if diff: boxed_print(diff.strip("\n"))
                            last_logs = new_logs
            except: pass
            time.sleep(0.5)

    threading.Thread(target=log_tailer, daemon=True).start()

    kb = KeyBindings()
    @kb.add('escape')
    def _(event):
        boxed_print("CMDS: /start, /switch <model>, /clear, /exit", C_SECONDARY)

    history_file = f"/root/.agentlink_history_{name}"
    custom_style = PromptStyle.from_dict({
        'prompt': f'{C_PRIMARY} bold',
        'toolbar': f'bg:{C_DIM} {C_WHITE} bold',
        'status-on': f'{C_ACCENT} bold',
        'status-off': 'red bold',
    })

    session = PromptSession(key_bindings=kb, history=FileHistory(history_file), style=custom_style)

    def bottom_toolbar():
        status_tag = "status-on" if state["is_started"] else "status-off"
        status_text = "ACTIVE" if state["is_started"] else "STANDBY"
        return HTML(f' <b>NODE:</b> {name.upper()} | <b>CORE:</b> {state["active_model"].upper()} | <b>LINK:</b> <{status_tag}>{status_text}</{status_tag}> | [Esc] Help')

    try:
        with patch_stdout():
            while True:
                # Continuous Box
                h_line = "─" * (box_width - 2)
                print_formatted_text(HTML(f'<style fg="{C_ACCENT}">╭{h_line}╮</style>'))
                
                ui_input = session.prompt(
                    HTML(f'<style fg="{C_ACCENT}"> │ </style><style fg="{C_PRIMARY}"><b> > </b></style>'), 
                    bottom_toolbar=bottom_toolbar
                )
                
                print_formatted_text(HTML(f'<style fg="{C_ACCENT}">╰{h_line}╯</style>'))
                
                if not ui_input: continue
                if ui_input == "/exit": break
                elif ui_input == "/start":
                    r = requests.post(f"http://{ip}:8092/start", headers=get_headers())
                    boxed_print("SYSTEM: Neural uplink operational.", C_ACCENT)
                elif ui_input == "/clear":
                    console.clear()
                    console.print(get_ascii_header())
                elif ui_input == "/help":
                    boxed_print("CMDS: /start, /switch <model>, /clear, /exit", C_SECONDARY)
                elif ui_input.startswith("/switch "):
                    m = ui_input.split(" ")[1]
                    requests.post(f"http://{ip}:8092/switch", json={"model": m}, headers=get_headers())
                    boxed_print(f"SYSTEM: Routing to {m.upper()}...", C_SECONDARY)
                else:
                    if state["is_started"]:
                        requests.post(f"http://{ip}:8092/prompt", json={"text": ui_input}, headers=get_headers())
                    else:
                        boxed_print("ERROR: Link standby. Execute /start.", "red")
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        stop_event.set()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("target", nargs="?")
    args = parser.parse_args()
    registry = load_registry()
    node_names = [n['name'] for n in registry]

    if not args.target:
        console.clear()
        console.print(get_ascii_header())
        console.print("")
        tips = f"[bold {C_PRIMARY}]1.[/] Access Node: agentlink <name>\n[bold {C_PRIMARY}]2.[/] Wake Logic: /start\n[bold {C_PRIMARY}]3.[/] Route Core: /switch qwen"
        console.print(Align.center(Panel(tips, title=f"[bold {C_SECONDARY}]Quick Procedures[/]", border_style=C_SECONDARY, expand=False)))
        console.print(Align.center(list_servers()))
    elif args.target == "list":
        console.print(get_ascii_header())
        console.print(Align.center(list_servers()))
    elif args.target in node_names:
        posses_server(args.target)
    else:
        console.print(f"[bold red]FATAL:[/bold red] Identity '{args.target}' not recognized.")
        console.print(Align.center(list_servers()))
