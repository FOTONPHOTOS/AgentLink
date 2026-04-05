import re
import threading

class BaseAgent:
    def __init__(self):
        self.buffer = []
        self.line_buffer = ""
        self.started = False
        self.lock = threading.Lock()
        self.ansi_escape = re.compile(r'\x1B(?:[@-Z\-_]|\[[0-?]*[ -/]*[@-~])')
        
        # Comprehensive noise patterns
        self.noise_patterns = [
            re.compile(r'^\s*at\s+.*\(file:.*\)'), 
            re.compile(r'^\s*at\s+.*\(node:internal.*\)'),
            re.compile(r'^\s*at\s+async\s+.*'),
            re.compile(r'\{\s*$'), 
            re.compile(r'^\s*cause: \{'),
            re.compile(r'^\s*code: \d+,'),
            re.compile(r'^\s*message: .*'),
            re.compile(r'^\s*details: \[.*\]'),
            re.compile(r'^\s*retryDelayMs: .*'),
            re.compile(r'^\s*\}\,?\s*$'), 
            re.compile(r'^\s*\]\,?\s*$'),
            re.compile(r'^\s*\d+,\s*$'),
            re.compile(r'An unexpected critical error occurred'),
            re.compile(r'\[object Object\]'),
            re.compile(r'TerminalQuotaError'),
            re.compile(r'Loaded cached credentials'),
            re.compile(r'IMPORTANT: Speak English ONLY'),
            re.compile(r'^\s*\}\,?\s*$')
        ]

    def start(self): raise NotImplementedError
    def send_text(self, text: str): raise NotImplementedError
    def send_key(self, key_name: str): raise NotImplementedError
    
    def get_logs(self, lines=100):
        with self.lock:
            return ''.join(self.buffer[-lines:])
    
    def _add_to_buffer(self, text: str):
        chunk = self.ansi_escape.sub('', text)
        self.line_buffer += chunk
        
        if "\n" in self.line_buffer:
            lines = self.line_buffer.splitlines(keepends=True)
            if not self.line_buffer.endswith("\n"):
                self.line_buffer = lines.pop()
            else:
                self.line_buffer = ""

            filtered = []
            for line in lines:
                if any(p.search(line) for p in self.noise_patterns):
                    continue
                filtered.append(line)

            with self.lock:
                self.buffer.extend(filtered)
                if len(self.buffer) > 5000:
                    self.buffer = self.buffer[-5000:]
