from multiprocessing import Queue, Process


def worker_main(queue: Queue) -> None:
    while not queue.empty():
        item = queue.get()
        print(f"Now working on {item}")


def main() -> None:
    queue = Queue(maxsize=100)

    worker_proc = Process(target=worker_main, args=(queue, ), daemon=True)

    for item in range(10):
        queue.put(item)

    worker_proc.start()
    worker_proc.join()


if __name__ == '__main__':
    main()
