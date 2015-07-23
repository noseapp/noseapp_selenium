# -*- coding: utf-8 -*-

"""
Waiting for load page
"""

import time
from Queue import Queue

from noseapp.utils.common import waiting_for
from noseapp.utils.common import TimeoutException
from selenium.common.exceptions import WebDriverException

from noseapp_selenium.tools import get_query_from_driver


DEFAULT_STEPS = 5
DEFAULT_TRIES_AT_STEP = 5

SLEEP_BETWEEN_TRIES = 0.03


class WaitConfig(object):
    """
    Configuration for WaitComplete
    """

    def __init__(self,
                 timeout=30,
                 objects=None,
                 one_of_many=False,
                 wait_for_filling=True,
                 ready_state_complete=False):
        self.__timeout = timeout
        self.__one_of_many = one_of_many
        self.__objects = objects or tuple()
        self.__wait_for_filling = wait_for_filling
        self.__ready_state_complete = ready_state_complete

    @property
    def objects(self):
        return self.__objects

    @property
    def timeout(self):
        return self.__timeout

    @property
    def one_of_many(self):
        return self.__one_of_many

    @property
    def wait_for_filling(self):
        return self.__wait_for_filling

    @property
    def ready_state_complete(self):
        return self.__ready_state_complete


class WaitComplete(object):
    """
    Waiting for load page
    """

    def __init__(self, page):
        self.__page = page
        self.config = page.meta.get('wait_config', WaitConfig())

    def __call__(self):
        if self.config.ready_state_complete:
            self.__ready_state_complete__()

        if self.config.wait_for_filling:
            self.__page.wait_for_filling()

        wait_funcs = {
            False: self.__wait_all__,
            True: self.__wait_one_of_many__,
        }
        wait_funcs[bool(self.config.one_of_many)]()

    def __repr__(self):
        return '<WaitComplete of <{}>>'.format(self.__page.__class__.__name__)

    def __ready_state_complete__(self):
        waiting_for(
            lambda: self.__page.driver.execute_script(
                'return document.readyState == "complete"',
            ),
            timeout=self.config.timeout,
        )

    def __wait_all__(self):
        if not self.config.objects:
            return

        queue = Queue()
        map(queue.put_nowait, self.config.objects)
        t_start = time.time()

        query = get_query_from_driver(
            self.__page.driver,
            wrapper=self.__page.wrapper,
        )

        while (time.time() <= t_start + self.config.timeout) or (not queue.empty()):
            obj = queue.get()

            if not query.from_object(obj).exist:
                queue.put(obj)
        else:
            if not queue.empty():
                raise TimeoutException(
                    'Could not wait ready page "{}". Timeout "{}" exceeded.'.format(
                        self.__page.__class__.__name__, self.config.timeout,
                    ),
                )

    def __wait_one_of_many__(self):
        if not self.config.objects:
            return

        queue = Queue()
        map(queue.put_nowait, self.config.objects)
        t_start = time.time()

        query = get_query_from_driver(
            self.__page.driver,
            wrapper=self.__page.wrapper,
        )

        while time.time() <= t_start + self.config.timeout:
            obj = queue.get()

            if query.from_object(obj).exist:
                break

            queue.put(obj)
        else:
            raise TimeoutException(
                'Could not wait ready page "{}". Timeout "{}" exceeded.'.format(
                    self.__page.__class__.__name__, self.config.timeout,
                ),
            )


class ContentLength(object):
    """
    Length of HTML string at current moment
    """

    def __init__(self, client):
        self.__client = client
        self.__value = self._get()

    def __int__(self):
        return self.__value

    def __str__(self):
        return str(self.__value)

    def __repr__(self):
        return self.__str__()

    def __unicode__(self):
        return unicode(self.__value)

    def _get(self):
        if hasattr(self.__client, 'get_attribute'):
            client = self.__client
        else:
            client = self.__client.query.body().first()

        try:
            return len(client.obj.innerHTML)
        except WebDriverException:
            return 0

    def update(self):
        """
        To update value.
        If is updated then return True else False.

        :return: bool
        """
        current_value = self._get()
        is_update = current_value > self.__value or current_value < self.__value
        self.__value = current_value
        return is_update


class TriesStep(object):

    def __init__(self, content_length, tries=None):
        self.statuses = []
        self.tries = tries or DEFAULT_TRIES_AT_STEP

        for _ in xrange(self.tries):
            status = content_length.update()
            self.statuses.append(status)
            time.sleep(SLEEP_BETWEEN_TRIES)

    def been_update(self):
        return len(
            filter(
                lambda status: status is True,
                self.statuses,
            ),
        ) > 0


class WaitForFilling(object):

    def __init__(self, content_length, steps=None, tries_at_step=None):
        self.__steps = steps or DEFAULT_STEPS
        self.__tries_at_step = tries_at_step
        self.__content_length = content_length

    def perform(self):
        statuses = []

        for _ in xrange(self.__steps):
            step = TriesStep(
                self.__content_length,
                tries=self.__tries_at_step,
            )
            statuses.append(step.been_update())

        if True in statuses:
            self.perform()

        return int(self.__content_length)


def wait_for_filling(client=None, content_length=None, steps=None, tries_at_step=None):
    if not client and not content_length:
        raise ValueError('"client" or "content_length" param is required')

    content_length = content_length or ContentLength(client)

    wait = WaitForFilling(
        content_length,
        steps=steps,
        tries_at_step=tries_at_step,
    )

    return wait.perform()
