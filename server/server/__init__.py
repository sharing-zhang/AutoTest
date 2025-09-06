import pymysql
pymysql.install_as_MySQLdb()

print("===============install pymysql==============")

# 导入Celery应用，确保Django启动时加载Celery
# 注意：这里不需要导入，因为celery_app是独立的应用