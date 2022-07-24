import fabric
import time
import sys

servers = {"storage": [], "client": [], "stateless": []}

def remote_run(conn, cmd):
    try:
        r = conn.run(cmd)
        return r
    except Exception as e:
        print(e)


def read_config_file(file):
    with open(file, "r") as f:
        return f.read()


def initial_storage(conn, cur_sn_id):
    remote_run(conn, "sudo service foundationdb stop")     
    remote_run(conn, "bash mount32.sh")
    remote_run(conn, "sudo bash restore.sh")
    if cur_sn_id % 2 == 0:
        config_file = read_config_file("storage.conf").replace("$ID", "\$ID")
    else:
        config_file = read_config_file("storage-with-resolver.conf").replace("$ID", "\$ID")
    remote_run(conn, f""" sudo sh -c "echo '{config_file}' > /etc/foundationdb/foundationdb.conf" """)


def initial_others(conn, config_file_name):
    remote_run(conn, "sudo service foundationdb stop")     
    remote_run(conn, "bash mount32.sh")
    remote_run(conn, "sudo bash restore.sh")
    config_file = read_config_file(config_file_name).replace("$ID", "\$ID")
    remote_run(conn, f""" sudo sh -c "echo '{config_file}' > /etc/foundationdb/foundationdb.conf" """)


def initial_cluster():
    cur_sn_id = 1
    master = servers["storage"][0]
    fdb_cluster = ""
    with fabric.Connection(master, user="ubuntu") as conn:
        initial_storage(conn, cur_sn_id)
        cur_sn_id += 1
        remote_run(conn, "sudo python3 /usr/lib/foundationdb/make_public.py")
        r = remote_run(conn, "sudo cat /etc/foundationdb/fdb.cluster")
        fdb_cluster = r.stdout
    
    for storage in servers["storage"]:
        if storage == master:
            continue
        with fabric.Connection(storage, user="ubuntu") as conn:
            initial_storage(conn, cur_sn_id)
            cur_sn_id += 1
            remote_run(conn, f""" sudo sh -c "echo '{fdb_cluster}' > /etc/foundationdb/fdb.cluster" """)

    for client in servers["client"]:
        with fabric.Connection(client, user="ubuntu") as conn:
            initial_others(conn, "client.conf")
            remote_run(conn, f""" sudo sh -c "echo '{fdb_cluster}' > /etc/foundationdb/fdb.cluster" """)

    for other in servers["stateless"]:
        with fabric.Connection(other, user="ubuntu") as conn:
            initial_others(conn, "stateless.conf")
            remote_run(conn, f""" sudo sh -c "echo '{fdb_cluster}' > /etc/foundationdb/fdb.cluster" """)

    

def reset(ip):
    with fabric.Connection(ip, user="ubuntu") as conn:
        remote_run(conn, "sudo service foundationdb stop")
        remote_run(conn, "sudo bash restore.sh")


def reset_all():
    for type in servers:
        for ip in servers[type]:
            reset(ip)


def start(ip):
    with fabric.Connection(ip, user="ubuntu") as conn:
        remote_run(conn, "sudo service foundationdb start")


def start_cluster_by_option(storage_num, client_num):
    for i in range(storage_num):
        start(servers["storage"][i])
    for i in range(client_num):
        start(servers["client"][i])
    start(servers["stateless"][0])


def configure_new_triple_memory(storage_num, client_num):
    master = servers["storage"][0]
    with fabric.Connection(master, user="ubuntu") as conn:
        remote_run(conn, 'fdbcli --exec "configure new triple memory"')
    time.sleep(30)
    master = servers["storage"][0]
    with fabric.Connection(master, user="ubuntu") as conn:
        remote_run(conn, f'fdbcli --exec "configure proxies={storage_num}"')
        remote_run(conn, f'fdbcli --exec "configure logs={storage_num}"')
        remote_run(conn, f'fdbcli --exec "configure resolvers={int(storage_num/2)}"')
    time.sleep(10)


def get_servers_ip():
    servers_file = open("servers.ip", "r")
    for line in servers_file.readlines():
        items = line.split(" ")
        servers[items[0]].append(items[1])


def umount_all():
    for type in servers:
        for ip in servers[type]:
            with fabric.Connection(ip, user="ubuntu") as conn:
                remote_run(conn, "sudo service foundationdb stop")
                remote_run(conn, "bash umount.sh")



if __name__ == "__main__":
    storage_num = int(sys.argv[1])
    client_num = int(sys.argv[2])
    get_servers_ip()
    reset_all()
    umount_all()
    initial_cluster()
    reset_all()
    start_cluster_by_option(storage_num,client_num)
    configure_new_triple_memory(storage_num,client_num)