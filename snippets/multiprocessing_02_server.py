import time
from contextlib import contextmanager
from multiprocessing import Process, Queue


def server_main(input_queue: Queue, output_queue: Queue) -> None:
    state = 0

    while True:
        item, sent_at = input_queue.get()
        latency = time.time() - sent_at
        print(f"1-direction latency {latency * 1000:.4f} ms")
        state += item
        output_queue.put(state)


def main() -> None:
    input_queue = Queue()
    output_queue = Queue()
    process = Process(
        target=server_main, args=(input_queue, output_queue), daemon=True
    )
    process.start()

    while True:
        user_input = input("Enter some number!")
        try:
            sanitized = int(user_input.strip())
        except ValueError:
            print(f"This ('{user_input}') is not a number, you rascal!")
        else:
            with took():
                sent_at = time.time()
                input_queue.put((sanitized, sent_at))
                state = output_queue.get()
            print(f"Current state is {state}")


@contextmanager
def took():
    start = time.time()
    yield
    print(f"It took {(time.time() - start) * 1000:.4f} ms")


if __name__ == "__main__":
    main()
