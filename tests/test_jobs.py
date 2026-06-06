from threading import Event

import pytest

from pineapple_film_lab.domain import JobStatus
from pineapple_film_lab.jobs.queue import JobQueue


def test_queue_completes_job():
    queue = JobQueue(worker_count=1)
    job = queue.submit(lambda context: "done")

    finished = queue.wait(job.id, timeout=2)

    assert finished.status == JobStatus.COMPLETED
    assert finished.result == "done"
    queue.shutdown()


def test_job_failure_does_not_stop_next_job():
    queue = JobQueue(worker_count=1)
    failed = queue.submit(lambda context: 1 / 0)
    passed = queue.submit(lambda context: "ok")

    assert queue.wait(failed.id, 2).status == JobStatus.FAILED
    assert queue.wait(passed.id, 2).status == JobStatus.COMPLETED
    queue.shutdown()


def test_context_updates_progress():
    queue = JobQueue(worker_count=1)

    def work(context):
        context.set_progress(0.4)
        return "ok"

    finished = queue.wait(queue.submit(work).id, 2)

    assert finished.progress == 1.0
    queue.shutdown()


def test_running_job_can_be_cancelled_cooperatively():
    queue = JobQueue(worker_count=1)
    started = Event()
    release = Event()

    def work(context):
        started.set()
        release.wait(2)
        return "cancelled" if context.cancelled else "missed"

    job = queue.submit(work)
    assert started.wait(1)
    assert queue.cancel(job.id)
    release.set()
    finished = queue.wait(job.id, 2)

    assert finished.status == JobStatus.CANCELLED
    queue.shutdown()


def test_failed_job_can_be_retried():
    queue = JobQueue(worker_count=1)
    attempts = {"count": 0}

    def work(context):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("first failure")
        return "recovered"

    failed = queue.wait(queue.submit(work).id, 2)
    retried = queue.retry(failed.id)
    finished = queue.wait(retried.id, 2)

    assert failed.status == JobStatus.FAILED
    assert finished.status == JobStatus.COMPLETED
    assert finished.result == "recovered"
    queue.shutdown()


def test_shutdown_rejects_new_jobs_and_joins_workers():
    queue = JobQueue(worker_count=2)

    queue.shutdown()

    assert all(not worker.is_alive() for worker in queue.workers)
    with pytest.raises(RuntimeError, match="shut down"):
        queue.submit(lambda context: None)
