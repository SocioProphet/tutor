.. _edx_platform:

Working on edx-platform as a developer
======================================

Tutor supports running in development with ``tutor dev`` commands. Developers frequently need to work on a fork of some repository. The question then becomes: how to make their changes available within the "openedx" Docker container? 

For instance, when troubleshooting an issue in `edx-platform <https://github.com/openedx/edx-platform>`__, we would like to make some changes to a local fork of that repository, and then apply these changes immediately in the "lms" and the "cms" containers (but also "lms-worker", "cms-worker", etc.)

Similarly, when developing a custom XBlock, we would like to hot-reload any change we make to the XBlock source code within the containers.

Tutor provides a simple solution to these questions. In both cases, the solution takes the form of a ``tutor mounts add ...`` command.

Working on the "edx-platform" repository
----------------------------------------

Download the code from the upstream repository::

    cd /my/workspace/edx-plaform
    git clone https://github.com/openedx/edx-platform .

Check out the right version of the upstream repository. If you are working on the `current "zebulon" release <https://docs.openedx.org/en/latest/community/release_notes/index.html>`__ of Open edX, then you should checkout the corresponding branch::

    # "zebulon" is an example. You should put the actual release name here.
    # I.e: aspen, birch, cypress, etc.
    git checkout open-release/zebulon.master

On the other hand, if you are working on the Tutor :ref:`"nightly" <nightly>` branch then you should checkout the master branch::

    git checkout master

Then, mount the edx-platform repository with Tutor::

    tutor mounts add /my/workspace/edx-plaform

This command does a few "magical" things 🧙 behind the scenes:

1. Mount the edx-platform repository in the image at build-time. This means that when you run ``tutor images build openedx``, your custom repository will be used instead of the upstream. In particular, any change you've made to the installed requirements, static assets, etc. will be taken into account.
2. Mount the edx-platform repository at run time. Thus, when you run ``tutor dev start``, any change you make to the edx-platform repository will be hot-reloaded.

You can get a glimpse of how these auto-mounts work by running ``tutor mounts list``. It should output something similar to the following::

    $ tutor mounts list
    - name: /home/data/regis/projets/overhang/repos/edx/edx-platform
    build_mounts:
    - image: openedx
        context: edx-platform
    - image: openedx-dev
        context: edx-platform
    compose_mounts:
    - service: lms
        container_path: /openedx/edx-platform
    - service: cms
        container_path: /openedx/edx-platform
    - service: lms-worker
        container_path: /openedx/edx-platform
    - service: cms-worker
        container_path: /openedx/edx-platform
    - service: lms-job
        container_path: /openedx/edx-platform
    - service: cms-job
        container_path: /openedx/edx-platform

Working on edx-platform Python dependencies
-------------------------------------------

Quite often, developers don't want to work on edx-platform directly, but on a dependency of edx-platform. For instance: an XBlock. This works the same way as above. Let's take the example of the `"edx-ora2" <https://github.com/openedx/edx-ora2>`__ package, for open response assessments. First, clone the Python package::

    cd /my/workspace/edx-ora2
    git clone https://github.com/openedx/edx-ora2 .

Then, check out the right version of the package. This is the version that is indicated in the ``edx-platform/requirements/edx/base.txt``. Be careful that the version that is currently in use in your version of edx-platform is **not necessarily the latest version**.

    git checkout <my-version-tag-or-branch>

Then, mount this repository::

    tutor mounts add /my/workspace/edx-ora2

Verify that your repository is properly bind-mounted by running ``tutor mounts list``::

    $ tutor mounts list
    - name: /my/workspace/edx-ora2
    build_mounts:
    - image: openedx
        context: req-edx-ora2
    - image: openedx-dev
        context: req-edx-ora2
    compose_mounts:
    - service: lms
        container_path: /openedx/requirements/edx-ora2
    - service: cms
        container_path: /openedx/requirements/edx-ora2
    - service: lms-worker
        container_path: /openedx/requirements/edx-ora2
    - service: cms-worker
        container_path: /openedx/requirements/edx-ora2
    - service: lms-job
        container_path: /openedx/requirements/edx-ora2
    - service: cms-job
        container_path: /openedx/requirements/edx-ora2

It is quite possible that your package is not automatically recognized and bind-mounted by Tutor. In such a case, you will need to create a :ref:`Tutor plugin <plugin_development_tutorial>` that implements the :py:data:`tutor.hooks.Filters.EDX_PLATFORM_PYTHON_PACKAGES` patch::

    tutor.hooks.Filters.EDX_PLATFORM_PYTHON_PACKAGES.add_item("my-package")

After you implement and enable that plugin, ``tutor mounts list`` should display your directory among the bind-mounted directories.

You should then re-build the "openedx" Docker image to pick up your changes::

    tutor images build openedx

Then, whenever you run ``tutor dev start``, the "lms" and "cms" container should automatically hot-reload your changes.

Do I have to re-build the "openedx" Docker image after every change?
--------------------------------------------------------------------

No, you don't. Re-building the "openedx" Docker image may take a while, and you don't want to run this command every time you make a change to your local repositories. Because your host directory is bind-mounted in the containers at runtime, your changes will be automatically applied to the container. If you run ``tutor dev`` commands, then your changes will be automatically picked up.

If you run ``tutor local`` commands (for instance: when debugging a production instance) then your changes will *not* be automatically picked up. In such a case you should manually restart the containers::

    tutor local restart lms cms lms-worker cms-worker

Re-building the "openedx" image should only be necessary when you want to push your changes to a Docker registry, then pull them on a remote server.
