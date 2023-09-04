from __future__ import annotations

import os
import re
import typing as t

from tutor import bindmount
from tutor import hooks


@hooks.Filters.APP_PUBLIC_HOSTS.add()
def _edx_platform_public_hosts(
    hosts: list[str], context_name: t.Literal["local", "dev"]
) -> list[str]:
    if context_name == "dev":
        hosts += ["{{ LMS_HOST }}:8000", "{{ CMS_HOST }}:8001"]
    else:
        hosts += ["{{ LMS_HOST }}", "{{ CMS_HOST }}"]
    return hosts


@hooks.Filters.IMAGES_BUILD_MOUNTS.add()
def _mount_edx_platform_build(
    volumes: list[tuple[str, str]], path: str
) -> list[tuple[str, str]]:
    """
    Automatically add an edx-platform repo from the host to the build context whenever
    it is added to the `MOUNTS` setting.
    """
    if os.path.basename(path) == "edx-platform":
        volumes += [
            ("openedx", "edx-platform"),
            ("openedx-dev", "edx-platform"),
        ]
    return volumes


@hooks.Filters.COMPOSE_MOUNTS.add()
def _mount_edx_platform_compose(
    volumes: list[tuple[str, str]], name: str
) -> list[tuple[str, str]]:
    """
    When mounting edx-platform with `tutor mounts add /path/to/edx-platform`,
    bind-mount the host repo in the lms/cms containers.
    """
    if name == "edx-platform":
        path = "/openedx/edx-platform"
        volumes += [
            ("lms", path),
            ("cms", path),
            ("lms-worker", path),
            ("cms-worker", path),
            ("lms-job", path),
            ("cms-job", path),
        ]
    return volumes


# Auto-magically bind-mount xblock directories and some common dependencies.
hooks.Filters.EDX_PLATFORM_PYTHON_PACKAGES.add_items(
    [
        r".*[xX][bB]lock.*",
        "edx-enterprise",
        "edx-ora2",
        "edx-search",
    ]
)


def iter_mounted_edx_platform_python_requirements(mounts: list[str]) -> t.Iterator[str]:
    """
    Parse the list of mounted directories and yield the directory names that are for
    edx-platform python requirements. Names are yielded in alphabetical order.
    """
    names: set[str] = set()
    for mount in mounts:
        for _service, host_path, _container_path in bindmount.parse_mount(mount):
            name = os.path.basename(host_path)
            for regex in hooks.Filters.EDX_PLATFORM_PYTHON_PACKAGES.iterate():
                if re.match(regex, name):
                    names.add(name)
                    break

    yield from sorted(names)


hooks.Filters.ENV_TEMPLATE_VARIABLES.add_item(
    (
        "iter_mounted_edx_platform_python_requirements",
        iter_mounted_edx_platform_python_requirements,
    )
)


@hooks.Filters.IMAGES_BUILD_MOUNTS.add()
def _mount_edx_platform_python_requirements_build(
    volumes: list[tuple[str, str]], path: str
) -> list[tuple[str, str]]:
    """
    Automatically bind-mount edx-platform Python requirements at build-time.
    """
    name = os.path.basename(path)
    for regex in hooks.Filters.EDX_PLATFORM_PYTHON_PACKAGES.iterate():
        if re.match(regex, name):
            volumes.append(("openedx", f"req-{name}"))
            volumes.append(("openedx-dev", f"req-{name}"))
            break
    return volumes


@hooks.Filters.COMPOSE_MOUNTS.add()
def _mount_edx_platform_python_requirements_compose(
    volumes: list[tuple[str, str]], name: str
) -> list[tuple[str, str]]:
    """
    Automatically bind-mount edx-platform Python requirements at runtime.
    """
    for regex in hooks.Filters.EDX_PLATFORM_PYTHON_PACKAGES.iterate():
        if re.match(regex, name):
            # Bind-mount requirement
            path = f"/openedx/requirements/{name}"
            volumes += [
                ("lms", path),
                ("cms", path),
                ("lms-worker", path),
                ("cms-worker", path),
                ("lms-job", path),
                ("cms-job", path),
            ]
    return volumes
