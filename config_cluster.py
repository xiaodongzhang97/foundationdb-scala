import fabric
import time
import sys

servers = {"sn": [], "db": [], "ts": []}

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
    remote_run(conn, "bash mount64.sh")
    remote_run(conn, "sudo bash restore.sh")
    if cur_sn_id % 2 == 0:
        config_file = read_config_file("sn.conf").replace("$ID", "\$ID")
    else:
        config_file = read_config_file("sn-r.conf").replace("$ID", "\$ID")
    remote_run(conn, f""" sudo sh -c "echo '{config_file}' > /etc/foundationdb/foundationdb.conf" """)


def initial_others(conn, config_file_name):
    remote_run(conn, "sudo service foundationdb stop")     
    remote_run(conn, "bash mount32.sh")
    remote_run(conn, "sudo bash restore.sh")
    config_file = read_config_file(config_file_name).replace("$ID", "\$ID")
    remote_run(conn, f""" sudo sh -c "echo '{config_file}' > /etc/foundationdb/foundationdb.conf" """)


def configure_cluster():
    cur_sn_id = 1
    master = servers["sn"][0]
    fdb_cluster = ""
    with fabric.Connection(master, user="ubuntu") as conn:
        initial_storage(conn, cur_sn_id)
        cur_sn_id += 1
        remote_run(conn, "sudo python3 /usr/lib/foundationdb/make_public.py")
        r = remote_run(conn, "sudo cat /etc/foundationdb/fdb.cluster")
        fdb_cluster = r.stdout
    
    for storage in servers["sn"]:
        if storage == master:
            continue
        with fabric.Connection(storage, user="ubuntu") as conn:
            initial_storage(conn, cur_sn_id)
            cur_sn_id += 1
            remote_run(conn, f""" sudo sh -c "echo '{fdb_cluster}' > /etc/foundationdb/fdb.cluster" """)

    for client in servers["db"]:
        with fabric.Connection(client, user="ubuntu") as conn:
            initial_others(conn, "db.conf")
            remote_run(conn, f""" sudo sh -c "echo '{fdb_cluster}' > /etc/foundationdb/fdb.cluster" """)

    for other in servers["ts"]:
        with fabric.Connection(other, user="ubuntu") as conn:
            initial_others(conn, "ts.conf")
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


def start_cluster_by_option(sn_num, db_num):
    for i in range(sn_num):
        start(servers["sn"][i])
    for i in range(db_num):
        start(servers["db"][i])
    start(servers["ts"][0])

def configure_new_single_memory(sn_num, db_num):
    master = servers["sn"][0]
    with fabric.Connection(master, user="ubuntu") as conn:
        remote_run(conn, 'fdbcli --exec "configure new triple memory"')
    time.sleep(30)
    master = servers["sn"][0]
    with fabric.Connection(master, user="ubuntu") as conn:
        remote_run(conn, f'fdbcli --exec "configure proxies={sn_num}"')
        remote_run(conn, f'fdbcli --exec "configure logs={sn_num}"')
        remote_run(conn, f'fdbcli --exec "configure resolvers={int(sn_num/2)}"')
    time.sleep(10)


def get_servers_ip():
    servers_file = open("servers.ip", "r")
    for line in servers_file.readlines():
        items = line.split(" ")
        servers[items[0]].append(items[1])


def run_tpcc(option):
    populate_scripts = f"""
testTitle=PopulateTPCCTest
testName=PopulateTPCC
clientsUsed=1
actorsPerClient=8
warehousesPerActor={2*option}
timeout=3600000
clearAfterTest=false
runConsistencyCheck=false
    """
    with fabric.Connection(servers["sn"][0], user="ubuntu") as conn:
        remote_run(conn, f"echo $'{populate_scripts}' > TPCC-Populate.txt")
        remote_run(conn, f"sudo fdbserver -f TPCC-Populate.txt -r multitest")
        for rp in [1]:
            scripts = f"""
testTitle=TPCCTest
testName=TPCC
warehousesNum={16*option}
clientProcessesUsed={14*option}
clientsUsed={48*option}
remoteProbability={rp}
testDuration=120
warmupTime=30
expectedTransactionsPerMinute=1
timeout=14400""" + "\n" 
    
            remote_run(conn, f"echo $'{scripts}' > TPCC.txt")
            remote_run(conn, f"mkdir results-{rp}")
            remote_run(conn, f"sudo fdbserver -f TPCC.txt -r multitest | tee -a results-{rp}/{option}.res")


def run_tpcc_scalability():
    for i in range(9)[1:]:
        reset_all()
        start_cluster_by_option(i)
        configure_new_single_memory(i)
        run_tpcc(i)


def umount_all():
    for type in servers:
        for ip in servers[type]:
            with fabric.Connection(ip, user="ubuntu") as conn:
                remote_run(conn, "sudo service foundationdb stop")
                remote_run(conn, "bash umount.sh")



if __name__ == "__main__":
    sn_num = int(sys.argv[1])
    db_num = int(sys.argv[2])
    get_servers_ip()
    reset_all()
    umount_all()
    configure_cluster()
    reset_all()
    start_cluster_by_option(sn_num,db_num)
    configure_new_single_memory(sn_num,db_num)