# coding: utf-8
from __future__ import unicode_literals

from django.db import connection
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from edu_info.models import School
from auth_user.models import EduProfile


class Command(BaseCommand):
    DB_TABLE = 'eclass_user'
    """
    table : eclass_user
    +----------------------------+--------------+------+-----+---------+----------------+
    | Field                      | Type         | Null | Key | Default | Extra          |
    +----------------------------+--------------+------+-----+---------+----------------+
    | ECLASS_USER_ID             | bigint(20)   | NO   | PRI | NULL    | auto_increment |
    | ECLASS_USER_USERNAME       | varchar(255) | YES  |     | NULL    |                |
    | ECLASS_USER_USERPASSWORD   | varchar(255) | YES  |     | NULL    |                |
    | ECLASS_USER_USERNICKNAME   | varchar(255) | YES  |     | NULL    |                |
    | ECLASS_USER_OPENID         | varchar(255) | YES  |     | NULL    |                |
    | ECLASS_USER_REGTIME        | datetime     | YES  |     | NULL    |                |
    | ECLASS_USER_ISSUBSCRIBE    | int(11)      | YES  |     | NULL    |                |
    | ECLASS_USER_LASTLOGINTIME  | datetime     | YES  |     | NULL    |                |
    | ECLASS_USER_SCHOOLID       | bigint(20)   | YES  |     | NULL    |                |
    | ECLASS_USER_CLASSID        | bigint(20)   | YES  |     | NULL    |                |
    | ECLASS_USER_SCHOOLNAME     | varchar(255) | YES  |     | NULL    |                |
    | ECLASS_USER_PHONENUMBER    | varchar(255) | YES  |     | NULL    |                |
    | ECLASS_USER_EMAIL          | varchar(255) | YES  |     | NULL    |                |
    | ECLASS_USER_STATUS         | int(11)      | YES  |     | NULL    |                |
    | ECLASS_USER_TOKEN          | varchar(255) | YES  |     | NULL    |                |
    | ECLASS_USER_PROVINCE       | varchar(255) | YES  |     | NULL    |                |
    | ECLASS_USER_CITY           | varchar(255) | YES  |     | NULL    |                |
    | ECLASS_USER_DISTRICT       | varchar(255) | YES  |     | NULL    |                |
    | ECLASS_USER_COUNTRY        | varchar(255) | YES  |     | NULL    |                |
    | ECLASS_USER_UPDATETIME     | datetime     | YES  |     | NULL    |                |
    | ECLASS_USER_UNIONID        | varchar(255) | YES  |     | NULL    |                |
    | ECLASS_USER_AVATAR         | varchar(255) | YES  |     | NULL    |                |
    | ECLASS_USER_ASYNCWECHAT    | int(11)      | YES  |     | NULL    |                |
    | ECLASS_USER_REALLYNAME     | varchar(255) | YES  |     | NULL    |                |
    | ECLASS_USER_ADDRESS        | varchar(255) | YES  |     | NULL    |                |
    | ECLASS_USER_ROLEID         | bigint(20)   | YES  |     | NULL    |                |
    | ECLASS_USER_GENDER         | int(11)      | YES  |     | NULL    |                |
    | ECLASS_USER_STUNUMBER      | varchar(255) | YES  |     | NULL    |                |
    | ECLASS_USER_PARTNER_USERID | bigint(20)   | YES  |     | NULL    |                |
    | ECLASS_USER_LOGINTIMES     | int(11)      | YES  |     | NULL    |                |
    | ECLASS_USER_PARTNER_CODE   | int(11)      | NO   |     | 0       |                |
    +----------------------------+--------------+------+-----+---------+----------------+
    """

    def dictfetchall(self, cursor):
        "Return all rows from a cursor as a dict"
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    def _gen_techu_password(self, username, md5_password):
        return 'techu$yzy-' + username + '$' + md5_password

    def handle(self, *args, **options):
        sql = """SELECT ECLASS_USER_USERNAME as username,
                        ECLASS_USER_USERPASSWORD as password,
                        ECLASS_USER_USERNICKNAME as nickname,
                        ECLASS_USER_REGTIME as date_joined,
                        ECLASS_USER_LASTLOGINTIME as last_login,
                        ECLASS_USER_SCHOOLID as school_id,
                        ECLASS_USER_CLASSID as class_id,
                        ECLASS_USER_PHONENUMBER as mobile,
                        ECLASS_USER_EMAIL as email,
                        ECLASS_USER_REALLYNAME as real_name,
                        ECLASS_USER_ADDRESS as address,
                        ECLASS_USER_ROLEID as role_id,
                        ECLASS_USER_GENDER as gender
                        FROM {table};""".format(table=self.DB_TABLE)

        user_model = get_user_model()
        with connection.cursor() as c:
            c.execute(sql)
            for p in self.dictfetchall(c):
                if not (p.get('password') and p.get('username')):
                    self.stderr.write('illegal user: {p}'.format(p=p))
                    continue
                username = p['username']
                password = self._gen_techu_password(username, p['password'])
                new_user = {
                    'username': username,
                    'password': password,
                }
                if p.get('nickname'):
                    new_user['nickname'] = p.get('nickname')
                if p.get('date_joined'):
                    new_user['date_joined'] = p.get('date_joined')
                if p.get('last_login'):
                    new_user['last_login'] = p.get('last_login')
                if p.get('mobile'):
                    new_user['mobile'] = p.get('mobile')
                if p.get('email'):
                    new_user['email'] = p.get('email')
                if p.get('real_name'):
                    new_user['last_name'] = p.get('real_name')
                if p.get('address'):
                    new_user['address'] = p.get('address')
                if p.get('gender'):
                    new_user['gender'] = p.get('gender')
                user, created = user_model.objects.plain_update_or_create(
                    **new_user)
                if p.get('school_id'):
                    try:
                        school = School.objects.get(school_id=p['school_id'])
                    except School.DoesNotExist:
                        self.stderr.write(
                            'school({sid}) not exist, ignore'.format(
                                sid=p['school_id'])
                        )
                        continue
                    try:
                        if user.edu_profile:
                            user.edu_profile.school = school
                        else:
                            user_edu = EduProfile.objects.create(
                                school=school
                            )
                            user.edu_profile = user_edu
                        user.save()
                    except:
                        self.stderr.write(
                            'fail to insert edu info, user: {user}'.format(
                                user=user)
                        )
