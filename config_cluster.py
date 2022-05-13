import fabric
import time


servers = {"storage": [], "lp": [], "client": [], "other": []}

def remote_run(conn, cmd):
    try:
        r = conn.run(cmd)
        return r
    except Exception as e:
        print(e)


def read_config_file(file):
    with open(file, "r") as f:
        return f.read()


def initial_storage(conn):
    remote_run(conn, "sudo service foundationdb stop")     
    remote_run(conn, "bash mount64.sh")
    remote_run(conn, "sudo bash restore.sh")
    config_file = read_config_file("storage-foundationdb.conf").replace("$ID", "\$ID")
    remote_run(conn, f""" sudo sh -c "echo '{config_file}' > /etc/foundationdb/foundationdb.conf" """)


def initial_others(conn, config_file_name):
    remote_run(conn, "sudo service foundationdb stop")     
    remote_run(conn, "bash mount32.sh")
    remote_run(conn, "sudo bash restore.sh")
    config_file = read_config_file(config_file_name).replace("$ID", "\$ID")
    remote_run(conn, f""" sudo sh -c "echo '{config_file}' > /etc/foundationdb/foundationdb.conf" """)


def configure_cluster():
    master = servers["storage"][0]
    fdb_cluster = ""
    with fabric.Connection(master, user="ubuntu") as conn:
        initial_storage(conn)
        remote_run(conn, "sudo python3 /usr/lib/foundationdb/make_public.py")
        r = remote_run(conn, "sudo cat /etc/foundationdb/fdb.cluster")
        fdb_cluster = r.stdout
    
    for storage in servers["storage"]:
        if storage == master:
            continue
        with fabric.Connection(storage, user="ubuntu") as conn:
            initial_storage(conn)
            remote_run(conn, f""" sudo sh -c "echo '{fdb_cluster}' > /etc/foundationdb/fdb.cluster" """)
    
    for lp in servers["lp"]:
        with fabric.Connection(lp, user="ubuntu") as conn:
            initial_others(conn, "lp-foundationdb.conf")
            remote_run(conn, f""" sudo sh -c "echo '{fdb_cluster}' > /etc/foundationdb/fdb.cluster" """)


    for client in servers["client"]:
        with fabric.Connection(client, user="ubuntu") as conn:
            initial_others(conn, "client-foundationdb.conf")
            remote_run(conn, f""" sudo sh -c "echo '{fdb_cluster}' > /etc/foundationdb/fdb.cluster" """)

    for other in servers["other"]:
        with fabric.Connection(other, user="ubuntu") as conn:
            initial_others(conn, "other-foundationdb.conf")
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


def start_cluster_by_option(option):
    for i in range(option):
        for type in servers:
            if i < len(servers[type]):
                start(servers[type][i])
    time.sleep(10)
    master = servers["storage"][0]
    with fabric.Connection(master, user="ubuntu") as conn:
        remote_run(conn, f'fdbcli --exec "configure proxies={4*i}"')
        remote_run(conn, f'fdbcli --exec "configure logs={4*i}"')

def configure_new_single_memory():
    master = servers["storage"][0]
    with fabric.Connection(master, user="ubuntu") as conn:
        remote_run(conn, 'fdbcli --exec "configure new single memory"')
    time.sleep(60)

def get_servers_ip():
    servers_file = open("servers.ip", "r")
    for line in servers_file.readlines():
        items = line.split(" ")
        servers[items[0]].append(items[1])


def run_test(option):
    scripts = f"""testTitle=PopulateTPCCTest
testName=PopulateTPCC
clientsUsed=1
actorsPerClient=2
warehousesPerActor={8*option}
timeout=3600000
clearAfterTest=false
runConsistencyCheck=false

testTitle=TPCCTest
testName=TPCC
warehousesNum={16*option}
clientProcessesUsed={8*option}
clientsUsed={48*option}
testDuration=100
warmupTime=20
expectedTransactionsPerMinute=1
timeout=14400""" + "\n" 
    
    with fabric.Connection(servers["storage"][0], user="ubuntu") as conn:
        remote_run(conn, f"echo $'{scripts}' > TPCC.txt")
        remote_run(conn, "mkdir results")
        remote_run(conn, f"sudo fdbserver -f TPCC.txt -r multitest | tee -a results/{option}.res")


def run_all():
    for i in range(9)[1:]:
        reset_all()
        start_cluster_by_option(i)
        configure_new_single_memory()
        run_test(i)


def umount_all():
    for type in servers:
        for ip in servers[type]:
            with fabric.Connection(ip, user="ubuntu") as conn:
                remote_run(conn, "sudo service foundationdb stop")
                remote_run(conn, "bash umount.sh")

get_servers_ip()
reset_all()
start_cluster_by_option(1)
configure_new_single_memory()
run_test(1)