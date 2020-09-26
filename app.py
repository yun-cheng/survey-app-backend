
from load_credentials import *
from project import Project
from quiz import Quiz

app = Flask(__name__)


@app.route('/', methods=['GET'])
def main():
    # H_1 parameters
    create_new_project = request.args.get('create_project', '0')
    project_gsid = request.args.get('project_key', '')
    create_new_quiz = request.args.get('create_quiz', '0')
    quiz_gsid = request.args.get('quiz_id', '')
    project_id = request.args.get('project_id', '')
    interviewer_id = request.args.get('interviewer_id', '')
    update_type = request.args.get('update_type', '')
    delete_type = request.args.get('delete_type', '')
    email = request.args.get('email', '')  # TODO

    # H_2 credentials
    gsheets = load_gsheets()  # HIGHLIGHT 需開啟 Google Sheets API、Google Drive API
    db = load_firestore()

    # H_3-1 create new project
    if create_new_project == '1' and email:
        project = Project(gsheets=gsheets, db=db)
        return project.create(email=email)

    # H_3-2 update project
    if update_type == 'project' and project_gsid:
        project = Project(gsheets=gsheets, db=db)
        return project.update(gsid=project_gsid)

    # H_3-3 delete project
    if delete_type == 'project' and project_gsid:
        project = Project(gsheets=gsheets, db=db)
        return project.delete(gsid=project_gsid)

    # H_3-4 create new quiz
    if create_new_quiz == '1' and email:
        quiz = Quiz(gsheets=gsheets, db=db)
        return quiz.create(email=email)

    # H_3-5 更新測驗紀錄
    if update_type == 'quiz_result' and quiz_gsid and project_id and interviewer_id:
        quiz = Quiz(gsheets=gsheets, db=db)
        return quiz.update_result(gsid=quiz_gsid, project_id=project_id, interviewer_id=interviewer_id)

    # H_3-6 更新題庫、測驗資訊、測驗紀錄
    if update_type == 'quiz_all' and quiz_gsid:
        quiz = Quiz(gsheets=gsheets, db=db)

        return quiz.update(gsid=quiz_gsid) + \
               quiz.update_result(gsid=quiz_gsid, project_id=project_id, interviewer_id=interviewer_id)

    return 'Something wrong....'


if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
