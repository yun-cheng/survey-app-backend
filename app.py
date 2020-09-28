
from load_credentials import *
from unit import Unit
from project import Project
from quiz import Quiz

app = Flask(__name__)


@app.route('/', methods=['GET'])
def main():
    # H_1 parameters
    action = request.args.get('action', '')
    on = request.args.get('on', '')
    gsid = request.args.get('gsid', '')
    project_gsid = request.args.get('project_gsid', '')
    interviewer_id = request.args.get('interviewer_id', '')
    # TODO
    email = request.args.get('email', '')

    # H_2 credentials
    # HIGHLIGHT 需開啟 Google Sheets API、Google Drive API
    gsheets = load_gsheets()
    db = load_firestore()

    # H_3-c1 unit
    if on == 'unit':
        unit = Unit(gsheets=gsheets, db=db)

        if action == 'create' and email:
            return unit.create(email=email)

        elif action == 'update' and gsid:
            return unit.update(gsid=gsid)

        elif action == 'delete' and gsid:
            return unit.delete(gsid=gsid)

    # H_3-c2 project
    elif on == 'project':
        project = Project(gsheets=gsheets, db=db)

        if action == 'create' and email:
            return project.create(email=email)

        elif action == 'update' and gsid:
            return project.update(gsid=gsid)

        elif action == 'delete' and gsid:
            return project.delete(gsid=gsid)

    # H_3-c3 quiz
    elif on == 'quiz':
        quiz = Quiz(gsheets=gsheets, db=db)

        if action == 'create' and email:
            return quiz.create(email=email)

        elif action == 'update' and gsid:
            return quiz.update(gsid=gsid)

        elif action == 'update_result' and gsid and project_gsid and interviewer_id:
            return quiz.update_result(gsid=gsid, project_gsid=project_gsid, interviewer_id=interviewer_id)

        elif action == 'delete' and gsid:
            return quiz.delete(gsid=gsid)

        elif action == 'delete_result' and gsid:
            return quiz.delete_result(gsid=gsid)

    return '系統出現問題....'


if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
