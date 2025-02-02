Library to make you services reliable
=====================================

Retry on specific exception
---------------------------

.. code-block:: python

  import yretry

  @yretry.decorators.retry(attempts_number=3,
                            retry_on=(MyException,))
  def reliable_function():
      raise MyException()


Specific function to make desicion about retries
------------------------------------------------

.. code-block:: python

  import yretry

  def is_my_mistake(error):
      return isinstance(error, MyMistake)

  @yretry.decorators.retry(attempts_number=3,
                            retry_on=is_my_mistake)
  def reliable_function():
      raise MyMistake()


Retry on network errors
-----------------------

You can use following code to add retries for your custom network
function:

.. code-block:: python

  import requests
  import yretry

  @yretry.network.retry()
  def reliable_function():
     response = requests.get('http://localhost:5002')
     response.raise_for_status()
     return response

  print reliable_function()


Logging
=======

Global logger
-------------

You can pass specific logger to decorator:

.. code-block:: python

  import logging
  import logging.config

  LOGGING = {
      'version': 1,
      'formatters': {
          'precise': {
              'datefmt': '%Y-%m-%d,%H:%M:%S',
              'format': '%(levelname)-7s %(asctime)15s '
                        '%(name)s:%(lineno)d %(message)s'
          }
      },
      'handlers': {
          'console': {
              'class': 'logging.StreamHandler',
              'formatter': 'precise',
              'stream': 'ext://sys.stderr'
          },
      },
      'root': {
          'level': 'INFO',
          'handlers': ['console']
      }
  }

  logging.config.dictConfig(LOGGING)

  LOGGER = logging.getLogger(__name__)

  @yretry.network.retry(logger=LOGGER)
  def reliable_function():
     response = requests.get('http://localhost:5002')
     response.raise_for_status()
     return response


Object-specific logger
----------------------

If you define method 'get_logger' and decorate some method with retry
decorator will be used object-specific logger:

.. code-block:: python

  class MyClass(object):
     def __init__(self):
         self._logger = logging.getLogger(__name__)

     def get_logger(self):
         return self._logger

     @yretry.network.retry()
     def reliable_method(self):
         pass

  obj = MyClass()
  obj.reliable_method()
  # obj._logger will be used to write warnings about retries
