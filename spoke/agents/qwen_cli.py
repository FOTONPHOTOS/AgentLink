import os
import pty
import subprocess
import select
import threading
import logging
from .base import BaseAgent

logger = logging.getLogger('QwenPlugin')

class QwenAgent(BaseAgent):
    def start(self):
        env = os.environ.copy()
        env['HOME'] = '/root'
        cmd = ['/usr/bin/node', '/usr/bin/qwen', 'chat']
        
        self.master_fd, slave_fd = pty.openpty()
        self.process = subprocess.Popen(
            cmd, stdin=slave_fd, stdout=slave_fd, stderr=slave_fd, env=env, start_new_session=True
        )
        os.close(slave_fd)
        self.started = True
        threading.Thread(target=self._read_loop, daemon=True).start()

    def _read_loop(self):
        while self.process.poll() is None:
            try:
                r, _, _ = select.select([self.master_fd], [], [], 0.1)
                if self.master_fd in r:
                    data = os.read(self.master_fd, 4096)
                    if data:
                        self._add_to_buffer(data.decode('utf-8', errors='ignore'))
            except: break

    def send_text(self, text: str):
        if hasattr(self, 'master_fd'):
            os.write(self.master_fd, (text + '\n').encode('utf-8'))

    def send_key(self, key_name: str):
        key_map = {'UP': b'\x1b[A', 'DOWN': b'\x1b[B', 'ENTER': b'\n', 'ESC': b'\x1b', 'CTRL_C': b'\x03'}
        if key_name.upper() in key_map and hasattr(self, 'master_fd'):
            os.write(self.master_fd, key_map[key_name.upper()])
