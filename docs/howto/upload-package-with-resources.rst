.. _howto-upload_package_with_resources:

Uploading and releasing a package with resources
================================================

One of the most common workflows when communicating with the store API is to
release a package. This guide explains how to upload and release a package with
an associated resource. We will use a charm as an example.

This performs roughly the same store operations as running:

.. code-block:: bash

    charmcraft upload-resource my-charm my-file --filepath cat.gif
    charmcraft upload my-charm.charm
    charmcraft release my-charm

Get a Charmhub client
---------------------
Create a :py:class:`StoreClient` instance that points to the staging instance
of CharmHub:

.. literalinclude:: code/upload-package-with-resources/upload_package.py
    :language: python
    :start-after: [docs:get-client]
    :end-before: [docs:get-client-end]
    :dedent: 4

Push the resource
-----------------

Next, you'll need to:

1. Upload the resource file.
2. Connect that uploaded file with the charm resource.
3. Poll the status while CharmHub processes the file.
4. Retrieve the revision number assigned to the file.

.. literalinclude:: code/upload-package-with-resources/upload_package.py
    :language: python
    :start-after: [docs:upload-resource]
    :end-before: [docs:upload-resource-end]
    :dedent: 4

The snippet above uses a ``check_status`` helper function that polls CharmHub
every three seconds while the file processes.

.. collapse:: check_status function

    .. literalinclude:: code/upload-package-with-resources/upload_package.py
        :language: python
        :pyobject: check_status

This demo uploads the file silently, but the upload progress can also be
monitored interactively through a callback, as demonstrated in
:ref:`howto-craft_cli_upload_progress`. Likewise, polling the resource's status
URL may be done in other (perhaps more user-friendly) ways.

For Charmhub, resources may optionally include a list of bases.

Push the package
----------------
This next segment is very similar, as it:

1. Uploads the charm
2. Connects that uploaded file with the charm revision
3. Polls Charmhub while it processes the charm.
4. Retrieves the revision number assigned to the charm upload.

.. literalinclude:: code/upload-package-with-resources/upload_package.py
    :language: python
    :start-after: [docs:upload-charm]
    :end-before: [docs:upload-charm-end]
    :dedent: 4

Release the Kraken
------------------

Now that the charm and its resource have been uploaded, they can be released to
a channel. Upon release, the revision is tied to the relevant resources.

.. literalinclude:: code/upload-package-with-resources/upload_package.py
    :language: python
    :start-after: [docs:release]
    :end-before: [docs:release-end]
    :dedent: 4


Below is a full file containing an executable version of the script in this
guide.

.. collapse:: Full example

    .. literalinclude:: code/upload-package-with-resources/upload_package.py
        :language: python

You can run it as such:

.. literalinclude:: code/upload-package-with-resources/task.yaml
    :language: bash
    :start-after: [docs:run]
    :end-before: [docs:run-end]
