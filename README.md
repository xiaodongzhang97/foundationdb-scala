This repository is used to deploy FoundationDB cluster and evaluate its performance as the description in the paper **Fine-Grained Re-Execution for Efficient Batched Commit of Distributed Transactions**.

1. Create a cluster

    Create aws ec2 instances with specified public AMI (ami-0b73d84dde593007a) in the same sub-network.
    Ensure that these instances can connect with each other through ssh (username->ubuntu and no password).

2. Add the private IP of all instances address into servers.ip

3. Clone this repository into one of the cluster and build the cluster by running:

    ```shell
    python3 config_cluster.py storage_num client_num
    ```

4. Execute benchmark scripts by running:

    sudo fdbserver -f micro.txt -r multitest

5. Supported benchmark include micro.txt, tpcc-populate.txt (used to populate initial data for tpcc) and tpcc.txt. The benchmark parameter in the TXT file can be changed accordingly. 