from common import *
from load_credentials import *
from project import Project
from quiz import Quiz

app = Flask(__name__)


@app.route('/', methods=['GET'])
def main():
    # NOTE parameters
    create_new_project = request.args.get('create_project', '0')
    project_key = request.args.get('project_key', '')
    create_new_quiz = request.args.get('create_quiz', '0')
    quiz_id = request.args.get('quiz_id', '')
    project_id = request.args.get('project_id', '')
    interviewer_id = request.args.get('interviewer_id', '')
    update_type = request.args.get('update_type', '')
    delete_type = request.args.get('delete_type', '')
    email = request.args.get('email', '')  # TODO

    # NOTE credentials
    load_credentials()
    gsheets = load_gsheets()  # HIGHLIGHT 需開啟 Google Sheets API
    db = load_firestore()

    # NOTE create new project
    if create_new_project == '1' and email:
        project = Project(gsheets=gsheets, db=db)
        return project.create(email=email)

    # NOTE update project
    if update_type == 'project' and project_key:
        project = Project(gsheets=gsheets, db=db)
        return project.update(gsid=project_key)

    # NOTE delete project
    if delete_type == 'project' and project_key:
        project = Project(gsheets=gsheets, db=db)
        return project.delete(gsid=project_key)

    # NOTE create new quiz
    if create_new_quiz == '1' and email:
        quiz = Quiz(gsheets=gsheets, db=db)
        return quiz.create(email=email)

    # NOTE 更新測驗紀錄
    if update_type == 'quiz_result' and quiz_id and project_id and interviewer_id:
        quiz = Quiz(gsheets=gsheets, db=db)
        return quiz.update_result(gsid=quiz_id, project_id=project_id, interviewer_id=interviewer_id)

    # NOTE 更新題庫、測驗資訊、測驗紀錄
    if update_type == 'quiz_all' and quiz_id:
        quiz = Quiz(gsheets=gsheets, db=db)

        return quiz.update(gsid=quiz_id) + \
               quiz.update_result(gsid=quiz_id, project_id=project_id, interviewer_id=interviewer_id)

    return 'Something wrong....'


if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
