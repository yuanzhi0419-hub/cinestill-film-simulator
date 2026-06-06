from dataclasses import dataclass, field
from queue import Empty, Queue
from threading import Condition, Event, RLock, Thread
from uuid import uuid4

from pineapple_film_lab.domain import JobStatus


@dataclass
class Job:
    id: str
    callable: object = field(repr=False)
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    result: object = None
    error: str | None = None
    cancel_event: Event = field(default_factory=Event, repr=False)


class JobContext:
    def __init__(self, queue, job_id):
        self._queue = queue
        self._job_id = job_id

    @property
    def cancelled(self):
        return self._queue.get(self._job_id).cancel_event.is_set()

    def set_progress(self, value):
        self._queue._set_progress(self._job_id, value)


class JobQueue:
    def __init__(self, worker_count=1):
        if worker_count < 1:
            raise ValueError("worker_count must be at least 1")

        self._pending = Queue()
        self._jobs = {}
        self._lock = RLock()
        self._condition = Condition(self._lock)
        self._shutdown = Event()
        self.workers = [
            Thread(
                target=self._worker,
                name=f"pineapple-film-job-{index + 1}",
                daemon=False,
            )
            for index in range(worker_count)
        ]
        for worker in self.workers:
            worker.start()

    def submit(self, callable_):
        with self._condition:
            if self._shutdown.is_set():
                raise RuntimeError("job queue has been shut down")
            job = Job(id=uuid4().hex, callable=callable_)
            self._jobs[job.id] = job
            self._pending.put(job.id)
            self._condition.notify_all()
            return job

    def get(self, job_id):
        with self._lock:
            try:
                return self._jobs[job_id]
            except KeyError as error:
                raise KeyError(f"unknown job: {job_id}") from error

    def wait(self, job_id, timeout=None):
        with self._condition:
            completed = self._condition.wait_for(
                lambda: self.get(job_id).status.is_terminal,
                timeout=timeout,
            )
            if not completed:
                raise TimeoutError(f"job did not finish: {job_id}")
            return self.get(job_id)

    def cancel(self, job_id):
        with self._condition:
            job = self.get(job_id)
            if job.status.is_terminal:
                return False
            job.cancel_event.set()
            if job.status == JobStatus.PENDING:
                job.status = JobStatus.CANCELLED
            self._condition.notify_all()
            return True

    def retry(self, job_id):
        original = self.get(job_id)
        if original.status not in {JobStatus.FAILED, JobStatus.CANCELLED}:
            raise ValueError("only failed or cancelled jobs can be retried")
        return self.submit(original.callable)

    def shutdown(self, timeout=5):
        with self._condition:
            if self._shutdown.is_set():
                return
            self._shutdown.set()
            for _ in self.workers:
                self._pending.put(None)
            self._condition.notify_all()
        for worker in self.workers:
            worker.join(timeout)

    def _worker(self):
        while True:
            try:
                job_id = self._pending.get(timeout=0.2)
            except Empty:
                if self._shutdown.is_set():
                    return
                continue

            if job_id is None:
                return

            with self._condition:
                job = self.get(job_id)
                if job.cancel_event.is_set():
                    job.status = JobStatus.CANCELLED
                    self._condition.notify_all()
                    continue
                job.status = JobStatus.RUNNING
                self._condition.notify_all()

            context = JobContext(self, job_id)
            try:
                result = job.callable(context)
            except Exception as error:
                with self._condition:
                    job.status = (
                        JobStatus.CANCELLED
                        if job.cancel_event.is_set()
                        else JobStatus.FAILED
                    )
                    job.error = str(error) or error.__class__.__name__
                    self._condition.notify_all()
            else:
                with self._condition:
                    job.result = result
                    if job.cancel_event.is_set():
                        job.status = JobStatus.CANCELLED
                    else:
                        job.progress = 1.0
                        job.status = JobStatus.COMPLETED
                    self._condition.notify_all()

    def _set_progress(self, job_id, value):
        progress = float(value)
        if not 0.0 <= progress <= 1.0:
            raise ValueError("progress must be between 0 and 1")
        with self._condition:
            job = self.get(job_id)
            if not job.status.is_terminal:
                job.progress = progress
                self._condition.notify_all()
