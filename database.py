from flask import g
import psycopg2
from psycopg2.extras import DictCursor


def connect_db():
    conn = psycopg2.connect('postgres://mwlqltlpdarexo:'
                            'ad00628baa69f68549d62fa2a0ed51bd93579e729ae372af1a2563a6bb824a72@ec2-46-137-124-19'
                            '.eu-west-1.compute.amazonaws.com:5432/dcj297vtmlsrkc', cursor_factory=DictCursor)
    conn.autocommit = True
    sql = conn.cursor()
    return conn, sql


def get_db():
    if not hasattr(g, 'postgres_db_cur') or not hasattr(g, 'postgres_db_conn'):
        g.postgres_db_conn, g.postgres_db_cur = connect_db()
    return g.postgres_db_cur


def init_db():
    db = connect_db()
    db[1].execute(open('schema.sql', 'r').read())
    db[1].close()
    db[0].close()


def init_admin():
    db = connect_db()
    db[1].execute('update users set admin = True where name = %s', ('Admin',))
    db[1].close()
    db[0].close()
