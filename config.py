replicas = {
    0:("127.0.0.1", 9100, "./logs/replica_0.json"),
    1:("127.0.0.1", 9102, "./logs/replica_1.json"),
    2:("127.0.0.1", 9104, "./logs/replica_2.json")
}

clients = {
    0:("127.0.0.1", 9200, "./logs/client_0.json", 0.1, 0.5),
    1:("127.0.0.1", 9202, "./logs/client_0.json", 0.1, 0.5)
}