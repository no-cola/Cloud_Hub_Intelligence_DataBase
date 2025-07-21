listen_for_clients(15000)
socket = accept_client_connection(15000)

n = 1000

for i in range(2):
    x = personal.read_fix_from_socket(i, socket, n)
    sfix(x).write_fully_to_socket(socket)

res = sum(sfix.read_from_socket(socket, n))
print_ln('%s', res.reveal())
