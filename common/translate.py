from .common import *


def get_translate_df(self):
    spreadsheet = self.gsheets.open_by_key('1nmZ2OVD3tfPoJSVjJK_jlHRrY3NYADCi7yv2GY0VV28')
    translate_df = get_worksheet_df(spreadsheet, worksheet_title='命名對照')
    translate_df = translate_df.iloc[:, 0:3]
    translate_df.columns = ['appear', 'chinese', 'english']
    translate_df['re'] = translate_df.chinese.str.match('.+_$')

    self.translate_df = translate_df


def replace_str(chinese_str, translate_dict):
    if chinese_str in translate_dict:
        return translate_dict[chinese_str]

    for k, v in translate_dict.items():
        if k in chinese_str:
            return chinese_str.replace(k, v)

    return chinese_str


def translate(self, chinese_series, appear=''):
    translate_df = self.translate_df
    if appear:
        translate_df = translate_df[translate_df.appear == appear]

    translate_dict = dict(zip(translate_df.chinese, translate_df.english))

    if isinstance(chinese_series, str):
        return replace_str(chinese_series, translate_dict)
    else:
        return chinese_series.apply(replace_str, translate_dict=translate_dict)
