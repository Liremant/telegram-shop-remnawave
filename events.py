from typing import Dict, List, Callable
import logging
logger = logging.getLogger('__name__')

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event: str):
        def decorator(callback: Callable):
            if event not in self._subscribers:
                self._subscribers[event] = []
            self._subscribers[event].append(callback)
            return callback
        return decorator
    
    async def emit(self, event: str, **data):
        if event in self._subscribers:
            for callback in self._subscribers[event]:
                try:
                    await callback(**data)
                except Exception as e:
                    logger.exception(f'error while emiting event:{e}')

event_bus = EventBus()