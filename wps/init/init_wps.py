#!/usr/bin/env python3

"""Update passwords, set server settings & upload styles."""

import json
import logging
import os
import pathlib
import re
import shutil
import time
from xml.etree import ElementTree

import requests


# Helper classes and functions
class Env:
    """A helper class for easier access of env variables with conversion."""

    def str(self, key, default=None):
        """Return the value for the key as a string."""
        return os.environ.get(key, default)


class JsonFile:
    """
    Helper to allow access for variables that we want to store.

    Allows reuse in later runs of this script.
    """

    def __init__(self, filename):
        """Load the data from a file."""
        data = {}
        self.filename = filename
        if self.filename.exists():
            with self.filename.open() as infile:
                data = json.load(infile)
        self.data = data

    def get(self, key, default=None):
        """Return the value for the key or use the default value."""
        return self.data.get(key, default)

    def put(self, key, value):
        """Store the value for the key."""
        self.data[key] = value

    def save(self):
        """Store the data in a file so that it can be reused."""
        with self.filename.open("w") as outfile:
            json.dump(self.data, outfile)


class Tasks:
    """
    Helper class to collect various tasks & run them later.

    This one here is just linear, so without further dependency
    management (as Makefiles have it).
    """

    def __init__(self):
        """Init with empty task list."""
        self.tasks = []

    def register(self, f):
        """Register a task to be done."""
        self.tasks.append(f)
        return f

    def run(self):
        """Run all the tasks."""
        for f in self.tasks:
            f()


class Tomcat:
    """Helper class to make changes on the tomcat configuration."""

    def __init__(self, base_path):
        """Init the object with the file path of the base directory."""
        self.base_path = base_path

    def set_connection_timeout(self, connectionTimeout):
        """Update the connection timeout."""
        filepath = self.base_path / "conf" / "server.xml"

        et = ElementTree.parse(filepath)
        server = et.getroot()
        service = server.find("Service")
        connector = service.find("Connector")
        connector.attrib["connectionTimeout"] = "180000"
        et.write(filepath)

    def set_username_and_password(self, username, password):
        """Update the user for the management ui."""
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
        """Reload settings for an app."""
        # According to https://stackoverflow.com/a/32367339
        # It is enought to touch the web.xml to trigger a
        # restart of the webapp.
        filepath = self.base_path / "webapps" / app / "WEB-INF" / "web.xml"
        os.system(f"touch {filepath}")


class Wps:
    """Helper class to interact with the WPS server."""

    def __init__(self, base_url):
        """Init the object with the base url."""
        self.base_url = base_url
        self.session = requests.Session()

    def wait_until_ready(self):
        """Wait until we get success response codes from the servers base url."""
        ready = False
        while not ready:
            try:
                resp = requests.get(self.base_url)
                resp.raise_for_status()
                ready = True
            except Exception:
                time.sleep(2)

    def _get_csrf(self, resp):
        """Extract the csrf token from the response."""
        resp_elements = resp.text.split()
        csrf_idx = [i for i, x in enumerate(resp_elements) if x == 'name="_csrf"'][0]
        crsf_value_str = resp_elements[csrf_idx + 1]
        csrf_token = re.search('"(.*?)"', crsf_value_str).groups()[0]
        return csrf_token

    def login(self, username, password):
        """Login into the wps server in the session."""
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
        """
        Change the password.

        It is required to be logged in to use this method.
        """
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
        """
        Update the server data of the wps (host, port, etc).

        Required to be logged in.
        """
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


class Geoserver:
    """Helper class to interact with the geoserver."""

    def __init__(self, base_path):
        """Init the object with the base_path on the filesystem."""
        self.base_path = base_path

    def set_username_and_password(self, username, password):
        """Update the username & password."""
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
        """Set a role for a user."""
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
        new_role_ref = ElementTree.Element(
            "{http://www.geoserver.org/security/roles}roleRef"
        )
        new_role_ref.attrib["roleID"] = role
        new_user_roles.append(new_role_ref)
        user_list.append(new_user_roles)

        et.write(filepath)


class GeoserverStyle:
    """Helper class to write geoserver styles to filesystem."""

    def __init__(self, id_, name, format_, version, filename):
        """Init the object."""
        self.id_ = id_
        self.name = name
        self.format_ = format_
        self.version = version
        self.filename = filename

    def write(self, xml_target):
        """Write the style to a file as xml."""
        xml_style = ElementTree.Element("style")

        xml_id = ElementTree.Element("id")
        xml_id.text = self.id_
        xml_style.append(xml_id)

        xml_name = ElementTree.Element("name")
        xml_name.text = self.name
        xml_style.append(xml_name)

        xml_format = ElementTree.Element("format")
        xml_format.text = self.format_
        xml_style.append(xml_format)

        xml_language_version = ElementTree.Element("languageVersion")
        xml_version = ElementTree.Element("version")
        xml_version.text = self.version
        xml_language_version.append(xml_version)
        xml_style.append(xml_language_version)

        xml_filename = ElementTree.Element("filename")
        xml_filename.text = self.filename
        xml_style.append(xml_filename)

        et = ElementTree.ElementTree(xml_style)
        et.write(xml_target, xml_declaration=True)


# Some instances of the classes.
env = Env()
# We store it inside of tomcat volume. So those data are as persistent
# as the volume.
# If we lose the volume we can use just some default initial values.
init_wps_data = JsonFile(
    pathlib.Path("/tomcat/webapps/wps/WEB-INF/classes/init_wps.json")
)
tomcat = Tomcat(base_path=pathlib.Path("/tomcat"))
wps = Wps("http://riesgos-wps:8080/wps")
geoserver = Geoserver(
    base_path=pathlib.Path("/tomcat/webapps/geoserver"),
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
    """Update the wps password."""
    initial_username = "wps"
    # We store the last password in a file, so that we can read it from
    # there in case we run multiple docker-compose up calls.
    # This way we can get the latest password that was used.
    initial_password = init_wps_data.get("RIESGOS_WPS_PASSWORD", default="wps")

    wps.wait_until_ready()
    try:
        wps.login(username=initial_username, password=initial_password)
        new_password = env.str("RIESGOS_WPS_PASSWORD", default="wps")
        wps.change_password(old_password=initial_password, new_password=new_password)
        init_wps_data.put("RIESGOS_WPS_PASSWORD", new_password)
    except Exception:
        logging.error("Problem on setting the wps password - skipping")


@tasks.register
def step_wps_server_settings():
    """Update the wps server settings."""
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
    """Update the geoserver password."""
    username = env.str("RIESGOS_GEOSERVER_USERNAME", default="admin")
    password = env.str("RIESGOS_GEOSERVER_PASSWORD", default="geoserver")
    geoserver.set_username_and_password(username=username, password=password)
    geoserver.set_role(username, role="ADMIN")


@tasks.register
def step_geoserver_upload_styles():
    """Upload the styles to the geoserver."""

    def to_style_name(base_name):
        """Return a stylename with common naming conventions."""
        without_file_extension = base_name.replace(".sld", "")
        without_underscores = without_file_extension.replace("_", "-")
        return without_underscores

    styles = pathlib.Path("/styles").glob("*.sld")
    for sld_file in styles:
        style_name = to_style_name(sld_file.name)
        # Copy the sld file to the geoserver folder
        sld_target = geoserver.base_path / "data" / "styles" / f"{style_name}.sld"
        xml_target = geoserver.base_path / "data" / "styles" / f"{style_name}.xml"
        shutil.copy(sld_file, sld_target)
        # And I need to create an according xml file.
        # We need to extract the version from the sld file.
        version = ElementTree.parse(sld_file).getroot().attrib.get("version", "1.0.0")
        GeoserverStyle(
            id_=style_name,
            name=style_name,
            format_="sld",
            version=version,
            filename=f"{style_name}.sld",
        ).write(xml_target)


@tasks.register
def step_tomcat_reload_settings():
    """Reload the tomcat apps."""
    apps = ["geoserver", "wps"]

    for app in apps:
        tomcat.reload_settings(app)


@tasks.register
def step_store_data():
    """Store the data that we collected while doing the init work."""
    init_wps_data.save()


if __name__ == "__main__":
    tasks.run()
