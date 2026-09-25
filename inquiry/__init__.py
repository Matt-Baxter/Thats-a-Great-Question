"""Every judgment the app makes.

This package decides what a valid request is, what to ask the model, whether
the model's reply is good enough to show, and what the user sees when something
goes wrong. The HTTP handler in api/ and the page in public/ only pass values
to and from it, so every decision here can be tested without a server.
"""
