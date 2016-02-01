# -*- coding: utf-8 -*-
# Copyright: 2015 Jens Carroll
# These sources are released under the terms of the MIT license: see LICENSE
import sqlite3, sys, binascii, time, os.path
from datetime import datetime, timedelta
from Crypto.Hash import SHA256
from Crypto import Random
from sys import getsizeof

class ResqStore:
  """ Utilizing a small SQLite database for resq-pi. """
  def __init__(self, db_path):
    self.db_path = db_path
    
  def _connect(self):
    self.db = sqlite3.connect(self.db_path, detect_types = sqlite3.PARSE_DECLTYPES)
    return self.db

  def _sql(self):
    with self._connect():
      try:
        self.db.row_factory = sqlite3.Row
        yield self.db.cursor()
      # Catch exception
      except sqlite3.Error, e:
        print "SQLite Error: %s" % e.args[0]

  def exist(self):
    return os.path.isfile(self.db_path)

  def create_tables(self):
    for cursor in self._sql(): 
      cursor.execute("""CREATE TABLE IF NOT EXISTS
        settings(id INTEGER PRIMARY KEY,
          salt TEXT NOT NULL,
          access_token TEXT NOT NULL,
          username TEXT NOT NULL,
          use_sms INTEGER NOT NULL DEFAULT 1,
          phone_number TEXT,
          use_email INTEGER NOT NULL DEFAULT 0,
          email_address TEXT,
          email_password TEXT,
          email_login TEXT,
          smtp TEXT,
          port INTEGER NOT NULL,
          credit_balance TEXT,
          credit_updated_at timestamp DEFAULT NULL,
          sms_notification TEXT NOT NULL,
          email_notification TEXT NOT NULL,
          email_subject TEXT NOT NULL,
          updated_at timestamp NOT NULL
        )""")
      cursor.execute("""CREATE TABLE IF NOT EXISTS
        resq_logs(id INTEGER PRIMARY KEY,
          comment TEXT DEFAULT NULL,
          test_alarm INTEGER NOT NULL,
          created_at timestamp NOT NULL          
        )""")
      cursor.execute("""CREATE TABLE IF NOT EXISTS
        participants(id INTEGER PRIMARY KEY,
          username TEXT UNIQUE ON CONFLICT IGNORE,
          phone_number TEXT,
          email_address TEXT,
          test_user INTEGER NOT NULL DEFAULT 0,
          created_at timestamp NOT NULL
        )""")
    return True

  def drop_tables(self):
    for cursor in self._sql(): 
      cursor.execute("DROP TABLE IF EXISTS settings")
      cursor.execute("DROP TABLE IF EXISTS resq_logs")
      cursor.execute("DROP TABLE IF EXISTS participants")
    return True

  def default_setting(self):
    for cursor in self._sql(): 
      salt = binascii.hexlify(Random.new().read(32)) # add a 256bit salt
      hash = SHA256.new()
      hash.update(salt + "admin") # default password
      access_token = hash.hexdigest()
      
      now = datetime.now()
      cursor.execute("""INSERT INTO settings(
        salt, access_token, username, use_sms, phone_number, use_email, 
        email_address, email_password, email_login, smtp, port,
        credit_balance, sms_notification, email_notification, email_subject,
        updated_at)
        VALUES
        (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (salt, access_token, "Admin", 1, "--", 0, 0,
          None, None, None, 25, "unknown", 
          "This is an Alarm-Pi SMS notification. We need help!",
          "This is an Alarm-Pi E-Mail notification. We need help!",
          "ATTENTION: We need help",
          now))
    return True

  def reset_tables(self):
    self.drop_tables()
    self.create_tables()
    self.default_setting()

  def reset_password(self):
    for cursor in self._sql():
      salt = binascii.hexlify(Random.new().read(32)) # add a 256bit salt
      hash = SHA256.new()
      hash.update(salt + "admin") # default password
      access_token = hash.hexdigest()

      cursor.execute("""UPDATE settings SET
        salt = ?, access_token = ?, updated_at = ? WHERE id = 1""", 
        (salt, access_token, datetime.now()))
    return True

  def test_password(self, access_code):
    for cursor in self._sql():
      cursor.execute("SELECT * FROM settings WHERE id = 1")
      permission = cursor.fetchone()

      if permission is None:
        return False # no entry found

      hash = SHA256.new()
      hash.update(permission['salt'] + access_code)

      if hash.hexdigest() == permission['access_token']:
        return True
      return False

  def change_password(self, old_access_code, new_access_code):
    if self.test_password(old_access_code):
      for cursor in self._sql():
        salt = binascii.hexlify(Random.new().read(32)) # add a 256bit salt
        hash = SHA256.new()
        hash.update(salt + new_access_code) # new password
        access_token = hash.hexdigest()

        cursor.execute("""UPDATE settings SET
          salt = ?, access_token = ?, updated_at = ? WHERE id = 1""", 
          (salt, access_token, datetime.now()))
      return True
    return False

  def add_log(self, test_alarm, comment=None):
    for cursor in self._sql(): 
      cursor.execute("""INSERT INTO resq_logs(comment, test_alarm, created_at)
        VALUES
        (?, ?, ?)""", (comment, test_alarm, datetime.now()))

  def clear_log(self):
    for cursor in self._sql(): 
      cursor.execute("DELETE FROM resq_logs WHERE 1")

  def use_email(self):
    for cursor in self._sql():
      cursor.execute("SELECT * FROM settings WHERE id = 1")
      setting = cursor.fetchone()
    return setting['use_email']

  def use_sms(self):
    for cursor in self._sql():
      cursor.execute("SELECT * FROM settings WHERE id = 1")
      setting = cursor.fetchone()
    return setting['use_sms']

  def list_participants(self, test):
    for cursor in self._sql():
      if test:
        cursor.execute("SELECT * FROM participants WHERE test_user > 0 ORDER BY created_at")
      else:
        cursor.execute("SELECT * FROM participants ORDER BY created_at")        
      return cursor.fetchall()

  def email_settings(self):
    for cursor in self._sql():
      cursor.execute("SELECT * FROM settings WHERE id = 1")
      setting = cursor.fetchone()
    return [setting['email_login'], setting['email_password'], setting['smtp'], setting['port']]


  def email_notification(self, test):
    for cursor in self._sql():
      cursor.execute("SELECT * FROM settings WHERE id = 1")
      setting = cursor.fetchone()
    add = " (Test Only)" if test > 0 else ""
    return [setting['email_subject']+add, setting['email_notification']]

  def sms_notification(self, test):
    for cursor in self._sql():
      cursor.execute("SELECT * FROM settings WHERE id = 1")
      setting = cursor.fetchone()
    add = "*** Test Only! ***\n" if test > 0 else ""
    return add+setting['sms_notification']

  def save_credit(self, credit):
    for cursor in self._sql():
      cursor.execute("""UPDATE settings SET
        credit_balance = ?, credit_updated_at = ? WHERE id = 1""", 
        (credit, datetime.now()))

if __name__ == "__main__":
  pi = AlarmStore(".resq_pi/resq_pi.db")
  assert pi.drop_tables()
  assert pi.create_tables()
  assert pi.default_setting()
  print "Tables created!"

  print "Starting tests ..."

  # Test default password
  assert pi.test_password("admin")
  assert not pi.test_password("bla")

  # Test password change
  assert not pi.change_password("bla", "yeah!") # wrong old password
  assert pi.change_password("admin", "yeah!") # correct old password
  assert pi.test_password("yeah!") # change of password was successful
  assert not pi.test_password("bla") # check wrong password

  # Test logging
  pi.add_log(True, "comment 1")
  pi.add_log(False, "comment 2")
#  assert getsizeof(pi.list_log() == 2)

  pi.clear_log()
#  assert getsizeof(pi.list_log() == 0)

  # Test participant handling
  assert pi.add_participant("Joe", "12345")
  assert pi.add_participant("Doe", None, "yeah@email.com")
  assert getsizeof(pi.list_participants() == 1)
  assert getsizeof(pi.list_participants(False) == 1)

  print "done"
