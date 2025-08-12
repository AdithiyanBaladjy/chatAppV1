from queue import PriorityQueue

pq=PriorityQueue()

pq.put(1,"a")
pq.put(1,"b")
pq.put(2,"c")

while not pq.empty():
    print(pq.get())
