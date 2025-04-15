import fcntl
import warnings
import re
import datetime

import requests
from flask import Blueprint, render_template, session, current_app, request
from flask_apscheduler import APScheduler

from CTFd.api import CTFd_API_v1
from CTFd.plugins import (
    register_plugin_assets_directory,
    register_admin_plugin_menu_bar,
)
from CTFd.plugins.challenges import CHALLENGE_CLASSES
from CTFd.utils import get_config, set_config
from CTFd.utils.decorators import admins_only

from .api import user_namespace, admin_namespace, AdminContainers
from .challenge_type import DynamicValueDockerChallenge
from .utils.checks import WhaleChecks
from .utils.control import ControlUtil
from .utils.db import DBContainer
from .utils.docker import DockerUtils
from .utils.exceptions import WhaleWarning
from .utils.setup import setup_default_configs
from .utils.routers import Router


def load(app):
    app.config['RESTX_ERROR_404_HELP'] = False
    # upgrade()
    plugin_name = __name__.split('.')[-1]
    set_config('whale:plugin_name', plugin_name)
    app.db.create_all()
    if not get_config("whale:setup"):
        setup_default_configs()

    register_plugin_assets_directory(
        app, base_path=f"/plugins/{plugin_name}/assets",
        endpoint='plugins.ctfd-whale.assets'
    )
    register_admin_plugin_menu_bar(
        title='Whale',
        route='/plugins/ctfd-whale/admin/settings'
    )

    DynamicValueDockerChallenge.templates = {
        "create": f"/plugins/{plugin_name}/assets/create.html",
        "update": f"/plugins/{plugin_name}/assets/update.html",
        "view": f"/plugins/{plugin_name}/assets/view.html",
    }
    DynamicValueDockerChallenge.scripts = {
        "create": "/plugins/ctfd-whale/assets/create.js",
        "update": "/plugins/ctfd-whale/assets/update.js",
        "view": "/plugins/ctfd-whale/assets/view.js",
    }
    CHALLENGE_CLASSES["dynamic_docker"] = DynamicValueDockerChallenge

    page_blueprint = Blueprint(
        "ctfd-whale",
        __name__,
        template_folder="templates",
        static_folder="assets",
        url_prefix="/plugins/ctfd-whale"
    )
    CTFd_API_v1.add_namespace(admin_namespace, path="/plugins/ctfd-whale/admin")
    CTFd_API_v1.add_namespace(user_namespace, path="/plugins/ctfd-whale")

    worker_config_commit = None

    @page_blueprint.route('/admin/settings')
    @admins_only
    def admin_list_configs():
        nonlocal worker_config_commit
        errors = WhaleChecks.perform()
        if not errors and get_config("whale:refresh") != worker_config_commit:
            worker_config_commit = get_config("whale:refresh")
            DockerUtils.init()
            Router.reset()
            set_config("whale:refresh", "false")
        return render_template('whale_config.html', errors=errors)

    @page_blueprint.route("/admin/containers")
    @admins_only
    def admin_list_containers():
        result = AdminContainers.get()
        view_mode = request.args.get('mode', session.get('view_mode', 'list'))
        session['view_mode'] = view_mode
        return render_template("whale_containers.html",
                               plugin_name=plugin_name,
                               containers=result['data']['containers'],
                               pages=result['data']['pages'],
                               curr_page=abs(request.args.get("page", 1, type=int)),
                               curr_page_start=result['data']['page_start'])

    def auto_clean_container():
        with app.app_context():
            try:
                # Get current time
                current_time = datetime.datetime.now()

                # Clean up expired containers from database
                results = DBContainer.get_all_expired_container()
                for r in results:
                    try:
                        # Calculate time elapsed since container start
                        time_elapsed = (current_time - r.start_time).total_seconds()
                        timeout = int(get_config("whale:docker_timeout", "3600"))

                        # Only remove if container has actually expired
                        if time_elapsed >= timeout:
                            # First remove the Docker service
                            whale_id = f'{r.user_id}-{r.uuid}'
                            client = DockerUtils.get_docker_client()
                            services = client.services.list(filters={'label': f'whale_id={whale_id}'})
                            for service in services:
                                try:
                                    service.remove(force=True)
                                except Exception as e:
                                    print(f"Error removing service {service.name}: {str(e)}")
                                    # Try direct API call as fallback
                                    try:
                                        client.api.remove_service(service.id)
                                    except Exception as e2:
                                        print(f"Failed to remove service {service.name} after retry: {str(e2)}")

                            # Then remove from database
                            DBContainer.remove_container_record(r.user_id, r.challenge_id)
                            print(f"Removed expired container: {whale_id} (elapsed: {time_elapsed}s, timeout: {timeout}s)")
                    except Exception as e:
                        print(f"Error cleaning up container {r.id}: {str(e)}")

                # Clean up orphaned Docker Swarm services
                client = DockerUtils.get_docker_client()
                services = client.services.list()

                for service in services:
                    # Check if service name matches CTFd-Whale pattern
                    if re.match(r'^\d+-[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', service.name):
                        try:
                            # Check if service has any running tasks
                            tasks = service.tasks()
                            running_tasks = [t for t in tasks if t['Status']['State'] == 'running']

                            if not running_tasks:
                                # Check if this service exists in our database
                                service_uuid = service.name.split('.')[0].split('-', 1)[1]
                                container = DBContainer.query.filter_by(uuid=service_uuid).first()
                                if not container:
                                    # Service exists in Docker but not in our database - remove it
                                    service.remove(force=True)
                                    print(f"Removed orphaned service: {service.name}")
                        except Exception as e:
                            print(f"Error processing service {service.name}: {str(e)}")
            except Exception as e:
                print(f"Error in auto_clean_container: {str(e)}")

    app.register_blueprint(page_blueprint)

    try:
        Router.check_availability()
        DockerUtils.init()
    except Exception:
        warnings.warn("Initialization Failed. Please check your configs.", WhaleWarning)

    try:
        lock_file = open("/tmp/ctfd_whale.lock", "w")
        lock_fd = lock_file.fileno()
        fcntl.lockf(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

        scheduler = APScheduler()
        scheduler.init_app(app)
        scheduler.start()
        scheduler.add_job(
            id='whale-auto-clean', func=auto_clean_container,
            trigger="interval", seconds=10
        )

        print("[CTFd Whale] Started successfully")
    except IOError:
        pass
