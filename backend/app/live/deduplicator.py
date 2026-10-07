import datetime
from typing import Dict, Any, Optional

class DuplicateSignalDeduplicator:
    """
    Prevents repeated or duplicate signals for the same symbol.
    Maintains a cooldown window and checks active position/signal state.
    """

    def __init__(self, cooldown_minutes: int = 15):
        self.cooldown_minutes = cooldown_minutes
        self._last_signal_times: Dict[str, datetime.datetime] = {}
        self._active_symbols: set = set()

    def can_generate_signal(self, symbol: str) -> bool:
        now = datetime.datetime.now()
        if symbol in self._active_symbols:
            return False

        last_time = self._last_signal_times.get(symbol)
        if last_time:
            elapsed = (now - last_time).total_seconds() / 60.0
            if elapsed < self.cooldown_minutes:
                return False

        return True

    def register_signal(self, symbol: str):
        self._last_signal_times[symbol] = datetime.datetime.now()

    def set_symbol_active(self, symbol: str, active: bool = True):
        if active:
            self._active_symbols.add(symbol)
        else:
            self._active_symbols.discard(symbol)
