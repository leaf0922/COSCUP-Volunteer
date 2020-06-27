import arrow
from flask import Blueprint
from flask import g
from flask import jsonify
from flask import render_template
from flask import request

from module.project import Project
from module.tasks import Tasks
from module.team import Team

VIEW_TASKS = Blueprint('tasks', __name__, url_prefix='/tasks')


@VIEW_TASKS.route('/')
def index():
    return u'hi'

@VIEW_TASKS.route('/<pid>', methods=('GET', 'POST'))
def project(pid):
    uid = g.get('user', {}).get('account', {}).get('_id')

    project = Project.get(pid=pid)
    if not project:
        return u'404', 404

    is_in_project = False
    if uid:
        is_in_project = bool(Team.participate_in(uid, pid))

    if request.method == 'GET':
        return render_template('./tasks_project.html', project=project)

    elif request.method == 'POST':
        post_data = request.get_json()

        def page_args(data, uid):
            data['_uid'] = uid
            data['_joined'] = False
            data['_login'] = False

            if uid:
                data['_login'] = True

                if uid in data['people']:
                    data['_joined'] = True

        if post_data['casename'] == 'get':
            datas = []

            for data in Tasks.get_by_pid(pid=pid):
                page_args(data=data, uid=uid)
                datas.append(data)

            return jsonify({'datas': datas, 'is_in_project': is_in_project})

        elif post_data['casename'] == 'join':
            if not uid:
                return jsonify({'info': 'Need login'}), 401

            data = Tasks.join(pid=pid, task_id=post_data['task_id'], uid=uid)
            page_args(data=data, uid=uid)

            return jsonify({'data': data})

        elif post_data['casename'] == 'cancel':
            if not uid:
                return jsonify({'info': 'Need login'}), 401

            data = Tasks.cancel(pid=pid, task_id=post_data['task_id'], uid=uid)
            page_args(data=data, uid=uid)

            return jsonify({'data': data})

@VIEW_TASKS.route('/<pid>/add', methods=('GET', 'POST'))
@VIEW_TASKS.route('/<pid>/edit/<task_id>', methods=('GET', 'POST'))
def add(pid, task_id=None):
    uid = g.get('user', {}).get('account', {}).get('_id')
    if not uid:
        return jsonify({'info': 'Need login'}), 401

    project = Project.get(pid=pid)
    if not project:
        return u'404', 404

    if request.method == 'GET':
        catelist = Tasks.get_cate(pid=pid)
        return render_template('./tasks_add.html', project=project, catelist=catelist)

    elif request.method == 'POST':
        post_data = request.get_json()

        if post_data['casename'] == 'add':
            data = post_data['data']
            starttime = arrow.get('%(date)s %(starttime)s' % data, tzinfo='Asia/Taipei').datetime
            endtime = None
            if 'endtime' in data and data['endtime']:
                endtime = arrow.get('%(date)s %(endtime)s' % data, tzinfo='Asia/Taipei').datetime

            raw = Tasks.add(pid=pid, title=data['title'].strip(), cate=data['cate'].strip(),
                    desc=data['desc'], limit=max((1, int(data['limit']))), starttime=starttime,
                    created_by=uid, endtime=endtime)

        return jsonify({'data': raw})
