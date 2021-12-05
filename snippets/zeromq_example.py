import time
from contextlib import contextmanager
from multiprocessing import Process, Queue

import zmq


PORT = 8001
TCP_SERVER = f"tcp://*:{PORT}"
TCP_CLIENT = f"tcp://localhost:{PORT}"

# IPC_SERVER = "ipc:///tmp/zermq_example_st"
# IPC_CLIENT = IPC_SERVER  # same

SERVER = TCP_SERVER
CLIENT = TCP_CLIENT

# SERVER = IPC_SERVER
# CLIENT = IPC_CLIENT


def server_main() -> None:
    state = 0

    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(SERVER)
    while True:
        number, sent_at = socket.recv_pyobj()
        latency = time.time() - sent_at
        print(f"1-direction latency {latency * 1000:.4f} ms")
        state += number
        socket.send_pyobj(state)


def main() -> None:
    process = Process(
        target=server_main, daemon=True
    )
    process.start()

    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(CLIENT)

    while True:
        user_input = input("Enter some number!")
        try:
            sanitized = int(user_input.strip())
        except ValueError:
            print(f"This ('{user_input}') is not a number, you rascal!")
        else:
            with took():
                sent_at = time.time()
                socket.send_pyobj((sanitized, sent_at))
                state = socket.recv_pyobj()
            print(f"Current state is {state}")


@contextmanager
def took():
    start = time.time()
    yield
    print(f"It took {(time.time() - start) * 1000:.4f} ms")


if __name__ == "__main__":
    main()
