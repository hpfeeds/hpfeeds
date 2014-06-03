#!/usr/bin/python
# -*- coding: utf8 -*-

import json
import sqlite3

import config

# inserting a user:
# sqlite3 db.sqlite3
# > insert into authkeys (owner, ident, secret, pubchans, subchans) values ('owner', 'ident', 'secret', '["chan1"]', '["chan1"]');

class Database(object):
    def __init__(self):
        self.sql = sqlite3.connect(config.DBPATH)
        self.check_db()

    def check_db(self):
        with self.sql:
            try:
                res = self.sql.execute("select * from logs, authkeys where 1=0")
            except sqlite3.OperationalError:
                print "setting up tables..."
                # create tables
                self.sql.execute("""
                create table logs (id integer primary key autoincrement,
                    data TEXT)
                """)
                self.sql.execute("""
                create table stats (id integer primary key autoincrement,
                    ak TEXT, uid TEXT, data TEXT)
                """)
                self.sql.execute("""
                create table authkeys (id integer primary key autoincrement,
                    owner TEXT, ident TEXT, secret TEXT,
                    pubchans TEXT, subchans TEXT)
                """)

    def log(self, row):
        enc = json.dumps(row)
        with self.sql:
            self.sql.execute("insert into logs (data) values (?)", (enc,))

    def close(self):
        self.sql.close()

    def connstats(self, ak, uid, stats):
        c = self.sql.cursor()
        try:
            c.execute("select * from stats where ak=?", (ak,))
            res = c.fetchone()
        except:
            import traceback
            traceback.print_exc()
            return None
        finally:
            c.close()

        if not res:
            enc = json.dumps(stats)
            with self.sql:
                self.sql.execute("insert into stats (ak, uid, data) values (?,?,?)", (ak, uid, enc))
        else:
            rid,_,_,data = res
            dec = json.loads(data)
            new = dict([(k, stats[k]+dec.get(k, 0)) for k in stats])
            enc = json.dumps(new)
            with self.sql:
                self.sql.execute("update stats set data=? where id=?", (enc, rid))

    def get_authkey(self, ident):
        c = self.sql.cursor()
        try:
            c.execute("select * from authkeys where ident=?", (ident,))
            res = c.fetchone()
        except:
            import traceback
            traceback.print_exc()
            return None
        finally:
            c.close()

        if not res: return None

        ak, owner, ident, secret, pubchans, subchans = res

        pubchans = json.loads(pubchans)
        subchans = json.loads(subchans)

        return dict(secret=secret, ident=ident, pubchans=pubchans,
            subchans=subchans, owner=owner
        )
