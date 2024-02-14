import socket

def get_free_port():
    """Request a free port from the OS."""
    with socket.socket() as s:
        s.bind(('', 0))
        return s.getsockname()[1]
