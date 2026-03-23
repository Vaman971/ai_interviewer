API Reference
=============

This section covers the core modules and endpoints of the FastAPI backend and AI Agents.

Main Application
----------------
.. automodule:: app.main
   :members:
   :undoc-members:
   :show-inheritance:

API Endpoints
-------------

Interviews Router
~~~~~~~~~~~~~~~~~
.. automodule:: app.api.interviews
   :members:
   :undoc-members:
   :show-inheritance:

Auth Router
~~~~~~~~~~~
.. automodule:: app.api.auth
   :members:
   :undoc-members:
   :show-inheritance:

Media & WebRTC Router
~~~~~~~~~~~~~~~~~~~~~
.. automodule:: app.api.media
   :members:
   :undoc-members:
   :show-inheritance:

Code Sandbox Router
~~~~~~~~~~~~~~~~~~~
.. automodule:: app.api.code_execution
   :members:
   :undoc-members:
   :show-inheritance:


AI Agents (LangGraph)
---------------------

Interviewer Agent
~~~~~~~~~~~~~~~~~
.. automodule:: agents.interviewer_agent
   :members:
   :undoc-members:
   :show-inheritance:

LangGraph Orchestrator
~~~~~~~~~~~~~~~~~~~~~~
.. automodule:: agents.orchestrator
   :members:
   :undoc-members:
   :show-inheritance:

Resume Parsing Agent
~~~~~~~~~~~~~~~~~~~~
.. automodule:: agents.resume_agent
   :members:
   :undoc-members:
   :show-inheritance:


Core Services
-------------

Speech & Audio Service
~~~~~~~~~~~~~~~~~~~~~~
.. automodule:: app.services.speech_service
   :members:
   :undoc-members:
   :show-inheritance:

Avatar (WebRTC) Service
~~~~~~~~~~~~~~~~~~~~~~~
.. automodule:: app.services.avatar_service
   :members:
   :undoc-members:
   :show-inheritance:

Database Models
---------------
.. automodule:: app.models.interview
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: app.models.result
   :members:
   :undoc-members:
   :show-inheritance:
