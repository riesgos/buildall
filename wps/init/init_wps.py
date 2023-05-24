#!/usr/bin/env python3

import re
import os
import time
import pathlib
from xml.etree import ElementTree
import requests

# Helper classes and functions
class Env:
    def str(self, key, default=None):
        return os.environ.get(key, default)


class Tasks:
    def __init__(self):
        self.tasks = []

    def register(self, f):
        self.tasks.append(f)
        return f

    def run(self):
        for f in self.tasks:
            f()


class Tomcat:
    def __init__(self, base_path):
        self.base_path = base_path

    def set_connection_timeout(self, connectionTimeout):
        filepath = self.base_path / "conf" / "server.xml"

        et = ElementTree.parse(filepath)
        server = et.getroot()
        service = server.find("Service")
        connector = service.find("Connector")
        connector.attrib["connectionTimeout"] = "180000"
        et.write(filepath)

    def set_username_and_password(self, username, password):
        filepath = self.base_path / "conf" / "tomcat-users.xml"

        et = ElementTree.parse(filepath)
        tomcat_users = et.getroot()

        for existing_user in list(
            tomcat_users.findall("{http://tomcat.apache.org/xml}user")
        ):
            tomcat_users.remove(existing_user)

        new_user = ElementTree.Element("{http://tomcat.apache.org/xml}user")
        new_user.attrib["username"] = username
        new_user.attrib["password"] = password
        new_user.attrib["roles"] = "manager-gui"
        tomcat_users.append(new_user)

        et.write(filepath)

    def reload_settings(self, app):
        # According to https://stackoverflow.com/a/32367339
        # It is enought to touch the web.xml to trigger a
        # restart of the webapp.
        filepath = self.base_path / "webapps" / app / "WEB-INF" / "web.xml"
        os.system(f"touch {filepath}")


class WaitMixin:
    def wait_until_ready(self):
        ready = False
        while not ready:
            try:
                resp = requests.get(self.base_url)
                resp.raise_for_status()
                ready = True
            except Exception:
                time.sleep(2)


class Wps(WaitMixin):
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()

    def _get_csrf(self, resp):
        resp_elements = resp.text.split()
        csrf_idx = [i for i, x in enumerate(resp_elements) if x == 'name="_csrf"'][0]
        crsf_value_str = resp_elements[csrf_idx + 1]
        csrf_token = re.search('"(.*?)"', crsf_value_str).groups()[0]
        return csrf_token

    def login(self, username, password):
        resp_login_page = self.session.get(f"{self.base_url}/login")
        resp_login_page.raise_for_status()
        csrf_token = self._get_csrf(resp_login_page)

        resp_login = self.session.post(
            f"{self.base_url}/j_spring_security_check",
            {
                "username": username,
                "password": password,
                "_csrf": csrf_token,
            },
        )
        resp_login.raise_for_status()

    def change_password(self, old_password, new_password):
        resp_change_page = self.session.get(f"{self.base_url}/change_password")
        resp_change_page.raise_for_status()
        csrf_token = self._get_csrf(resp_change_page)

        resp_change = self.session.post(
            f"{self.base_url}/change_password",
            {
                "currentPassword": old_password,
                "newPassword": new_password,
                "_csrf": csrf_token,
            },
        )
        resp_change.raise_for_status()

    def post_server(self, protocol, hostname, hostport):
        resp_server_page = self.session.get(f"{self.base_url}/server")
        resp_server_page.raise_for_status()
        csrf_token = self._get_csrf(resp_server_page)

        data = {
            "protocol": protocol,
            "hostname": hostname,
            "hostport": hostport,
            "computation_timeout": "5",
            "weppapp_path": "wps",
            "repo_reload_interval": "0.0",
            "data_inputs_in_response": "false",
            "cache_capabilites": "false",
            "response_url_filter_enabled": "false",
            "min_pool_size": "10",
            "max_pool_size": "20",
            "keep_alive_seconds": "1000",
            "max_queued_tasks": "100",
            "max_request_size": "128",
            "add_process_description_Link_to_process_summary": "true",
        }

        payload = []
        for key, value in data.items():
            payload.append(f"value={value}")
            payload.append(f"key={key}")
            payload.append("module=org.n52.wps.webapp.entities.Server")
        payload = "&".join(payload)

        resp_post = self.session.post(
            f"{self.base_url}/server",
            payload,
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "X-CSRF-TOKEN": csrf_token,
            },
        )
        resp_post.raise_for_status()


class Geoserver(WaitMixin):
    def __init__(self, base_path, base_url):
        self.base_path = base_path
        self.base_url = base_url

    def set_username_and_password(self, username, password):
        filepath = (
            self.base_path / "data" / "security" / "usergroup" / "default" / "users.xml"
        )

        et = ElementTree.parse(filepath)
        user_registry = et.getroot()
        users = user_registry.find("{http://www.geoserver.org/security/users}users")

        for existing_user in list(
            users.findall("{http://www.geoserver.org/security/users}user")
        ):
            users.remove(existing_user)

        new_user = ElementTree.Element("{http://www.geoserver.org/security/users}user")
        new_user.attrib["enabled"] = "true"
        new_user.attrib["name"] = username
        new_user.attrib["password"] = f"plain:{password}"
        users.append(new_user)

        et.write(filepath)

    def set_role(self, username, role):
        filepath = (
            self.base_path / "data" / "security" / "role" / "default" / "roles.xml"
        )

        et = ElementTree.parse(filepath)
        role_registry = et.getroot()
        user_list = role_registry.find(
            "{http://www.geoserver.org/security/roles}userList"
        )

        for existing_user_roles in list(
            user_list.findall("{http://www.geoserver.org/security/roles}userRoles")
        ):
            user_list.remove(existing_user_roles)

        new_user_roles = ElementTree.Element(
            "{http://www.geoserver.org/security/roles}userRoles"
        )
        new_user_roles.attrib["username"] = username
        new_role_ref = ElementTree.Element("{http://www.geoserver.org/security/roles}roleRef")
        new_role_ref.attrib["roleID"] = role
        new_user_roles.append(new_role_ref)
        user_list.append(new_user_roles)

        et.write(filepath)


# Some instances of the classes.
env = Env()
tomcat = Tomcat(base_path=pathlib.Path("/tomcat"))
wps = Wps("http://riesgos-wps:8080/wps")
geoserver = Geoserver(
    base_path=pathlib.Path("/tomcat/webapps/geoserver"),
    base_url=env.str("RIESGOS_WPS_SEND_BASE_URL", default="http://riesgos-wps:8080/geoserver"),
)
tasks = Tasks()


# And our tasks.
# The tasks run in the order in which we register them here.
@tasks.register
def step_tomcat_username_and_password():
    """Set the username & password for the tomcat admin interface."""
    username = env.str("RIESGOS_WPS_TOMCAT_USERNAME")
    password = env.str("RIESGOS_WPS_TOMCAT_PASSWORD")
    tomcat.set_username_and_password(username=username, password=password)


@tasks.register
def step_tomcat_connection_timeout():
    """Set the connection timeout for tomcats server.xml file."""
    tomcat.set_connection_timeout("180000")


@tasks.register
def step_wps_password():
    initial_username = "wps"
    initial_password = "wps"
    wps.wait_until_ready()
    try:
        wps.login(username=initial_username, password=initial_password)
        new_password = env.str("RIESGOS_WPS_PASSWORD", default="wps")
        wps.change_password(old_password=initial_password, new_password=new_password)
    except:
        print("Problem on setting the wps password - skipping")


@tasks.register
def step_wps_server_settings():
    initial_username = "wps"
    password = env.str("RIESGOS_WPS_PASSWORD", default="wps")

    protocol = env.str("RIESGOS_WPS_ACCESS_SERVER_PROTOCOL", default="http")
    hostname = env.str("RIESGOS_WPS_ACCESS_SERVER_HOST", default="localhost")
    hostport = env.str("RIESGOS_WPS_ACCESS_SERVER_PORT", default="8082")

    wps.wait_until_ready()

    wps.login(username=initial_username, password=password)

    wps.post_server(protocol=protocol, hostname=hostname, hostport=hostport)


@tasks.register
def step_geoserver_password():
    username = env.str("RIESGOS_GEOSERVER_USERNAME", default="admin")
    password = env.str("RIESGOS_GEOSERVER_PASSWORD", default="geoserver")
    geoserver.set_username_and_password(username=username, password=password)
    geoserver.set_role(username, role="ADMIN")


@tasks.register
def step_geoserver_upload_styles():
    username = env.str("RIESGOS_GEOSERVER_USERNAME", default="admin")
    password = env.str("RIESGOS_GEOSERVER_PASSWORD", default="geoserver")

    scriptname = "/styles/add-style-to-geoserver.sh"
    content = open(scriptname).read()
    content_updated = (
        content.replace("__GEOSERVER_URL__", geoserver.base_url)
        .replace("__GEOSERVER_PASSWORD__", password)
        .replace("admin", username)
    )

    updated_scriptname = "/styles/add-style-to-geoserver-updated.sh"
    with open(updated_scriptname, "w") as outfile:
        outfile.write(content_updated)

    os.system(f"chmod +x {updated_scriptname}")
    geoserver.wait_until_ready()

    os.system(updated_scriptname)
    os.unlink(updated_scriptname)


@tasks.register
def step_tomcat_reload_settings():
    apps = ["geoserver", "wps"]

    for app in apps:
        tomcat.reload_settings(app)


if __name__ == "__main__":
    tasks.run()
