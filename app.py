
from common.load_credentials import *
from team import Team
from project.project import Project
from survey.survey import Survey
from survey_module import SurveyModule

app = Flask(__name__)


@app.route('/', methods=['GET'])
def main():
    # H_1 parameters
    action = request.args.get('action', '')
    on = request.args.get('on', '')
    gsid = request.args.get('gsid', '')
    # TODO
    email = request.args.get('email', '')

    # H_2 credentials
    # HIGHLIGHT 需開啟 Google Sheets API、Google Drive API
    gsheets = load_gsheets()
    db = load_firestore()
    bucket = load_storage()

    # H_3 action
    if on == 'team':
        target = Team(gsheets=gsheets, db=db, bucket=bucket)
    elif on == 'project':
        target = Project(gsheets=gsheets, db=db)
    elif on == 'survey':
        target = Survey(gsheets=gsheets, db=db, bucket=bucket)
    elif on == 'module':
        target = SurveyModule(gsheets=gsheets, db=db)
    elif on == 'recode_module':
        target = SurveyModule(gsheets=gsheets, db=db, module='recode')

    if on:
        if action == 'create' and email:
            return target.create(email=email)
        elif action == 'update' and gsid:
            return target.update(gsid=gsid)
        elif action == 'delete' and gsid:
            return target.delete(gsid=gsid)
        elif on == 'survey' and action == 'transfer' and gsid:
            return target.transfer(gsid=gsid)
        elif on == 'survey' and action == 'update_download_files' and gsid:
            return target.update_download_files(gsid=gsid)
        elif on == 'survey' and action == 'delete_all_responses' and gsid:
            return target.delete_all_responses(gsid=gsid)

    return '失敗了....'


if __name__ == '__main__':
    app.run(host='localhost', port=80, debug=True, use_reloader=False)
