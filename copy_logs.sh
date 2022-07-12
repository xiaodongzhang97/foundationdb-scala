scp -r ubuntu@172.31.1.214:/mnt/ramdisk/log ~/all_logs/172.31.1.214
scp -r ubuntu@172.31.7.179:/mnt/ramdisk/log ~/all_logs/172.31.7.179
scp -r ubuntu@172.31.13.146:/mnt/ramdisk/log ~/all_logs/172.31.13.146
scp -r ubuntu@172.31.11.160:/mnt/ramdisk/log ~/all_logs/172.31.11.160
scp -r ubuntu@172.31.12.60:/mnt/ramdisk/log ~/all_logs/172.31.12.60
scp -r ubuntu@172.31.8.7:/mnt/ramdisk/log ~/all_logs/172.31.8.7
scp -r ubuntu@172.31.12.169:/mnt/ramdisk/log ~/all_logs/172.31.12.169
scp -r ubuntu@172.31.10.250:/mnt/ramdisk/log ~/all_logs/172.31.10.250
scp -r ubuntu@172.31.2.122:/mnt/ramdisk/log ~/all_logs/172.31.2.122
scp -r ubuntu@172.31.12.137:/mnt/ramdisk/log ~/all_logs/172.31.12.137
scp -r ubuntu@172.31.12.216:/mnt/ramdisk/log ~/all_logs/172.31.12.216
scp -r ubuntu@172.31.7.205:/mnt/ramdisk/log ~/all_logs/172.31.7.205
scp -r ubuntu@172.31.13.253:/mnt/ramdisk/log ~/all_logs/172.31.13.253
scp -r ubuntu@172.31.9.92:/mnt/ramdisk/log ~/all_logs/172.31.9.92
scp -r ubuntu@172.31.5.225:/mnt/ramdisk/log ~/all_logs/172.31.5.225
scp -r ubuntu@172.31.6.198:/mnt/ramdisk/log ~/all_logs/172.31.6.198
scp -r ubuntu@172.31.2.71:/mnt/ramdisk/log ~/all_logs/172.31.2.71
scp -r ubuntu@172.31.8.194:/mnt/ramdisk/log ~/all_logs/172.31.8.194
scp -r ubuntu@172.31.6.122:/mnt/ramdisk/log ~/all_logs/172.31.6.122
cd ..
find all_logs/ -name '*.xml' -exec cat {} \; > all_logs.xml
cat all_logs.xml | grep TransactionComplete | grep "Success=\"1\"" | awk '{print $7, $8}' > simple_lat.xml