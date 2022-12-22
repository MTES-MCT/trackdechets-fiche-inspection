from os import environ

from app.app import dash_app

# To use `gunicorn run:server` (prod)
server = dash_app.server
# To use `python index.py` (dev)
if __name__ == "__main__":

    # Scalingo requires 0.0.0.0 as host, instead of the default 127.0.0.1
    host = environ.get("HOST", "127.0.0.1")
    debug = bool(environ.get("DEVELOPMENT"))
    port = int(environ.get("PORT", "8050"))
    dash_app.run(host=host, debug=debug, port=port)
