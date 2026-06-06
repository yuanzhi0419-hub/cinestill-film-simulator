import atexit

from flask import Flask

from .config import DefaultConfig
from .jobs import JobQueue
from .storage import SessionStorage


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.from_object(DefaultConfig)
    if overrides:
        app.config.update(overrides)

    storage = SessionStorage(app.config["SESSION_ROOT"])
    job_queue = JobQueue(worker_count=app.config["JOB_WORKERS"])
    app.extensions["session_storage"] = storage
    app.extensions["job_queue"] = job_queue
    app.extensions["luts"] = {}

    from .routes import api

    app.register_blueprint(api)
    _register_error_handlers(app)

    def cleanup():
        job_queue.shutdown()
        storage.cleanup()

    atexit.register(cleanup)
    return app


def _register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(error):
        return {"error": getattr(error, "description", "请求无效")}, 400

    @app.errorhandler(404)
    def not_found(error):
        return {"error": getattr(error, "description", "资源不存在")}, 404

    @app.errorhandler(413)
    def too_large(error):
        return {"error": "上传内容超过大小限制"}, 413

    @app.errorhandler(409)
    def conflict(error):
        return {"error": getattr(error, "description", "操作冲突")}, 409

    @app.errorhandler(500)
    def internal_error(error):
        return {"error": "本地处理发生错误"}, 500
