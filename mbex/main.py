from mbex.api.app import create_app


def initialize():
    app = create_app()
    return app
