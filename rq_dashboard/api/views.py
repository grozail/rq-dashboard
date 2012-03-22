import times
from flask import Blueprint
from . import jsonify
from rq import Queue, Worker
from rq import cancel_job, requeue_job
from rq import get_failed_queue


app = Blueprint('api', __name__)


def serialize_queues(queues):
    return [dict(name=q.name, count=q.count) for q in queues]


def serialize_date(dt):
    if dt is None:
        return None
    return times.format(dt, 'UTC')


def serialize_job(job):
    return dict(
        id=job.id,
        created_at=serialize_date(job.created_at),
        enqueued_at=serialize_date(job.enqueued_at),
        ended_at=serialize_date(job.ended_at),
        origin=job.origin,
        result=job._result,
        exc_info=job.exc_info,
        description=job.description)


@app.route('/job/<job_id>/cancel', methods=['POST'])
@jsonify
def cancel_job_view(job_id):
    cancel_job(job_id)
    return dict(status='OK')


@app.route('/job/<job_id>/requeue', methods=['POST'])
@jsonify
def requeue_job_view(job_id):
    requeue_job(job_id)
    return dict(status='OK')


@app.route('/requeue-all', methods=['GET', 'POST'])
@jsonify
def requeue_all():
    fq = get_failed_queue()
    job_ids = fq.job_ids
    count = len(job_ids)
    for job_id in job_ids:
        requeue_job(job_id)
    return dict(status='OK', count=count)


@app.route('/queue/<queue_name>/empty', methods=['POST'])
@jsonify
def empty_queue(queue_name):
    q = Queue(queue_name)
    q.empty()
    return dict(status='OK')


@app.route('/queue/<queue_name>/compact', methods=['POST'])
@jsonify
def compact_queue(queue_name):
    q = Queue(queue_name)
    q.compact()
    return dict(status='OK')


@app.route('/queues')
@jsonify
def list_queues():
    queues = serialize_queues(sorted(Queue.all()))
    return dict(queues=queues)


@app.route('/jobs/<queue_name>')
@jsonify
def list_jobs(queue_name):
    queue = Queue(queue_name)
    jobs = [serialize_job(job) for job in queue.jobs]
    return dict(name=queue.name, jobs=jobs)


@app.route('/workers')
@jsonify
def list_workers():
    def serialize_queue_names(worker):
        return [q.name for q in worker.queues]

    workers = [dict(name=worker.name, queues=serialize_queue_names(worker),
        state=worker.state) for worker in Worker.all()]
    return dict(workers=workers)