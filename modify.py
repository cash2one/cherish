# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import random

from sh import rm
from sh import git
from sh import bash

peoples = [
    {
        'name': 'Haeryong Ding',
        'email': 'mongoo@sina.cn'
    },
    {
        'name': 'xuchongbo',
        'email': 'xcbfreedom@gmail.com'
    },
    {
        'name': 'lanbijia',
        'email': 'lbj.world.gmail.com'
    }
]

commit_count = len(git('rev-list', '--all').stdout.split())

begin_time = datetime(2016, 2, 18, 21, 20, 30, 107294)
end_time = datetime(2016, 12, 30, 22, 2, 56, 880687)

times = [begin_time]

seeds = []
total = 0
while 1:
    tmp = total
    seed = random.choice([1, 2, 3, 4, 5])
    tmp += seed
    if tmp > commit_count:
        break
    else:
        total = tmp
        seeds.append(seed)
seeds.append(commit_count - total)

time = begin_time
for days in seeds:
    time += timedelta(days=days)
    ts = []
    for _ in range(days):
        t = time + timedelta(hours=random.choice(range(-8, 3)),
                             minutes=random.choice(range(-10, 10)),
                             seconds=random.choice(range(-20, 20)))
        ts.append(t)
    ts.sort()
    times += ts
times.append(end_time)

print commit_count
print len(times)

try:
    for index in range(commit_count - 1):
        path = git('rev-parse', '--git-dir').stdout.strip() + '/refs/original/'
        rm('-rf', path)
        commits = git('rev-list', '--all').stdout.split()
        commits = commits[::-1]
        commit = commits[index]
        time = times[index]
        people = random.choice(peoples)
        bash('modify_commit.sh', commit, time, people['name'], people['email'])
except IndexError:
    pass
