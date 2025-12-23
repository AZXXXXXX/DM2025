

from typing import Callable, Any, Optional
from PyQt6.QtCore import QObject, QThread, QRunnable, QThreadPool, pyqtSignal, pyqtSlot


class WorkerSignals(QObject):
    
    
    finished = pyqtSignal()                               
    error = pyqtSignal(Exception)                                   
    result = pyqtSignal(object)                                  
    progress = pyqtSignal(int)                                    


class Worker(QRunnable):
    
    
    def __init__(self, fn: Callable, *args, **kwargs):
        
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
    
    @pyqtSlot()
    def run(self):
        
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception as e:
            self.signals.error.emit(e)
        finally:
            self.signals.finished.emit()


class ServiceRunner:
    
    
    def __init__(self):
        
        self._thread_pool = QThreadPool.globalInstance()
    
    def run(
        self,
        fn: Callable,
        args: tuple = (),
        kwargs: Optional[dict] = None,
        on_success: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        on_finished: Optional[Callable[[], None]] = None,
        on_progress: Optional[Callable[[int], None]] = None
    ):
        
        if kwargs is None:
            kwargs = {}
        
        worker = Worker(fn, *args, **kwargs)
        
        if on_success:
            worker.signals.result.connect(on_success)
        if on_error:
            worker.signals.error.connect(on_error)
        if on_finished:
            worker.signals.finished.connect(on_finished)
        if on_progress:
            worker.signals.progress.connect(on_progress)
        
        self._thread_pool.start(worker)
    
    def wait_for_done(self):
        
        self._thread_pool.waitForDone()


                                
_service_runner: Optional[ServiceRunner] = None


def get_service_runner() -> ServiceRunner:
    
    global _service_runner
    if _service_runner is None:
        _service_runner = ServiceRunner()
    return _service_runner
