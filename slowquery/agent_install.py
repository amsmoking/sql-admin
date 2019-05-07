#rsync 127.0.0.1::share/agent_install.py ./ --progress
#python3 ./agent_install.py
#*/10 * * * * /bin/bash /usr/local/bin/slowquery_analysis.sh > /dev/null 2>&1
#INSERT INTO slowquery.dbinfo(dbname, port) VALUES('snowflake_censor', 3306)

#mysql -uroot -p'rkTLkwsLs47kFT' -e "INSERT INTO slowquery.dbinfo VALUES (2,'10.8.9.150','fundx','admin','123456',3306);"
import subprocess

cmdlist = [
    "apt-get install rsync -y",
    "rm -f /usr/local/bin/slowquery_analysis.sh",
    "cd /usr/local/bin/ && rsync 127.0.0.1::share/slowquery_analysis.sh ./ --progress",
    "apt-get install percona-toolkit -y",
    "which pt-query-digest"
]

def assert_exec(cmd):
    status, output = subprocess.getstatusoutput(cmd)
    print('cmd:%s, status:%s, output:%s' % (cmd, status, output))
    if status != 0: raise Exception('exec failed')
    return output

def get_server_id():
    cmd = "cat /etc/mysql/my.cnf | grep 'server-id'"
    server_id = assert_exec(cmd).strip().split('=')[1].strip()
    if not server_id.isdigit(): raise Exception('server_id is not digit')
    return server_id

def get_pt_query_digest():
    cmd = "which pt-query-digest"
    output = assert_exec(cmd).strip()
    return output

server_id = get_server_id()
print('server_id:', server_id)
for cmd in cmdlist:
    assert_exec(cmd)
digest_path = get_pt_query_digest()
print('digest_path:', digest_path)
f = open('/usr/local/bin/slowquery_analysis.sh', 'r')
content = f.read()
f.close()
content = content.replace('{{pt_query_digest}}', digest_path).replace('{{mysql_server_id}}', server_id)
f = open('/usr/local/bin/slowquery_analysis.sh', 'w')
f.write(content)
f.close()
print('finish')