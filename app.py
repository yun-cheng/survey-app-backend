
from load_credentials import *
from team import Team
from project import Project
from quiz import Quiz
from survey import Survey
from survey_module import SurveyModule

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

    # H_3 action
    if on == 'team':
        target = Team(gsheets=gsheets, db=db)
    elif on == 'project':
        target = Project(gsheets=gsheets, db=db)
    elif on == 'quiz':
        target = Quiz(gsheets=gsheets, db=db)
    elif on == 'survey':
        target = Survey(gsheets=gsheets, db=db)
    elif on == 'survey_module':
        target = SurveyModule(gsheets=gsheets, db=db)

    if on:
        if action == 'create' and email:
            return target.create(email=email)

        elif action == 'update' and gsid:
            return target.update(gsid=gsid)

        elif action == 'delete' and gsid:
            return target.delete(gsid=gsid)

        elif on == 'quiz' and action == 'update_result' and gsid and project_gsid and interviewer_id:
            return target.update_result(gsid=gsid, project_gsid=project_gsid, interviewer_id=interviewer_id)

        elif on == 'quiz' and action == 'delete_result' and gsid:
            return target.delete_result(gsid=gsid)

    return '系統出現問題....'


if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
