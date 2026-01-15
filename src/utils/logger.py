import sys
from io import StringIO
from pathlib import Path
from datetime import datetime

class LogCapture:
    def __init__(self):
        log_dir = Path(__file__).parent.parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        
        self.log_file = log_dir / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.buffer = StringIO()
        self.original_stdout = sys.stdout
        
    def start(self):
        sys.stdout = self
        
    def stop(self):
        sys.stdout = self.original_stdout
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(self.buffer.getvalue())
        print(f"\nLog sauvegardé : {self.log_file}")
    
    def write(self, text):
        self.original_stdout.write(text)
        self.buffer.write(text)
    
    def flush(self):
        self.original_stdout.flush()