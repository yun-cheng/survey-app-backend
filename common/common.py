import json
import string
import os
from datetime import datetime
import uuid
from collections import defaultdict
import pytz
import re
import ast
from dateutil.parser import parse

import firebase_admin
import pygsheets
import pandas as pd
import numpy as np
from firebase_admin import credentials
from firebase_admin import firestore
from flask import Flask, request
from google.cloud import storage
from google.cloud.exceptions import NotFound
from google.cloud.firestore_v1 import DocumentReference, CollectionReference, Query
from google.cloud.storage.bucket import Bucket


#
app_version = '211206_1'
tw_tz = pytz.timezone('Asia/Taipei')

# NOTE 切換 prod/dev
if os.environ['ENV'] == 'dev':
    main_url = 'https://survey-app-backend-hhbdnactua-de.a.run.app/'
else:
    main_url = 'https://interviewer-quiz-lrqnbewzdq-de.a.run.app/'


def set_where(self, index=0, str='', error=False):
    self.where[index] = str
    print(str)

    if index != 4:
        self.where[(index + 1):] = [''] * (4 - index)

    self.where_list.append((index, str))

    if error:
        raise ValueError


def where_to_str(self):
    where = [f'{".." * i * 2}{x}' for i, x in enumerate(self.where) if x != '']
    where_str = '<br/>'.join(where)

    return where_str


def where_list_to_str(self):
    where_list_str = ''
    for where in self.where_list:
        where_list_str += f'<br/>{".." * where[0] * 2}{where[1]}'

    return where_list_str


def get_worksheet_df(spreadsheet, worksheet_title, **kwargs):
    df = spreadsheet.worksheet_by_title(worksheet_title)\
        .get_as_df(numerize=False, include_tailing_empty=True, **kwargs)
    df = df.loc[:, df.columns != '']

    return df


def df_to_dict(df, new_column_names, index_column):
    df.columns = new_column_names
    df.index = df[index_column]
    dict = df.to_dict(orient='index')

    return dict


def dict_to_firestore(dict, doc, **kwargs):
    doc.set(dict, **kwargs)
    result_dict = doc.doc_to_dict()

    return result_dict


def doc_to_dict(self):
    doc = self.get()
    doc_dict = doc.to_dict()
    return doc_dict


def query_to_dict(self, first=False):
    docs = self.stream()

    query_dict = {}
    for doc in docs:
        if first:
            query_dict = doc.to_dict()
            break
        query_dict[doc.id] = doc.to_dict()

    return query_dict


def dict_to_storage(self, dict, filepath):
    blob = self.blob(filepath)
    blob.upload_from_string(
        data=json.dumps(dict),
        content_type='application/json'
    )


def dict_from_storage(self, filepath):
    blob = self.blob(filepath)
    dict = json.loads(blob.download_as_string())

    return dict


def df_to_storage(self, df, filepath):
    blob = self.blob(filepath)
    blob.upload_from_string(
        data=df.to_csv(index=False),
        content_type='text/csv'
    )
    blob.make_public()

    return blob.public_url


def delete_file(self, filepath):
    try:
        self.delete_blob(filepath)
    except NotFound:
        print(f'"{filepath}" not found')
        pass


DocumentReference.doc_to_dict = doc_to_dict
CollectionReference.query_to_dict = query_to_dict
Query.query_to_dict = query_to_dict
Bucket.dict_from_storage = dict_from_storage
Bucket.dict_to_storage = dict_to_storage
Bucket.df_to_storage = df_to_storage
Bucket.delete_file = delete_file


def set_cell(worksheet, pos, value, url=None, font_size=None, color=None, background_color=None,
             horizontal_alignment=None):
    color_map = {
        'red': (1, 0, 0, 0),
        'blue': (0, 0, 1, 0),
        'yellow': (1, 1, 0, 0),
        'orange': (1, 0.6, 0, 0),
        'white': (1, 1, 1, 0)
    }
    cell = pygsheets.Cell(pos, worksheet=worksheet)
    if color:
        cell.set_text_format('foregroundColor', color_map[color])
    if background_color:
        cell.color = color_map[background_color]
    if font_size:
        cell.set_text_format('fontSize', font_size)
    if horizontal_alignment == 'center':
        cell.set_horizontal_alignment(pygsheets.custom_types.HorizontalAlignment.CENTER)
    if url:
        cell.set_value(f'=HYPERLINK("{url}", "{value}")')
    else:
        cell.set_value(value)


def reorder_columns(self, col_name, position):
    temp_col = self[col_name]
    self.drop(columns=[col_name], inplace=True)
    if position < 0:
        position = len(self.columns) + 1 + position
    self.insert(loc=position, column=col_name, value=temp_col)


pd.DataFrame.reorder_columns = reorder_columns
