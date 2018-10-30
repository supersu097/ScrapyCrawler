from zhugefang.zhugefang.helper import SqliteDB, Proxy

sqlite = SqliteDB()
proxy = Proxy()
proxy_ip_pool = proxy.build_proxy_ip_pool()
for ip in proxy_ip_pool:
    print(sqlite.validate_proxy_ip_by_baidu(ip))
# if proxy_ip is None:
#     print('ip pool is empty.')
#     # 所有代理ip均不可用时更新DB代理池
#     sqlite.update_ip_pool_tb()
#     proxy_ip = sqlite.fetch_one_proxy_ip()
# print(proxy_ip)
