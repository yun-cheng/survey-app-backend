from common.common import *


def reformat_expression(self, row, column):
    try:
        full_expression = row[column]

        # S_ 切開並保留分隔符號
        full_expression = re.split('([|&()])', full_expression)
        element_list = [e for e in full_expression if e.replace(' ', '') != '']

        full_expression_body = ''
        expression_dict = {}
        letters = string.ascii_uppercase
        i = 0

        for element in element_list:
            if element in ['(', ')']:
                full_expression_body += element
            elif element in ['|', '&']:
                full_expression_body += element * 2
            else:
                split_element = re.split('(!=|==|>=|<=|>|<| not in| in)', element)

                if len(split_element) == 1:
                    element = element.replace(' ', '')
                    split_element = re.split('(notin|notcontainsany|containsany|'
                                             'notcontainsall|containsall|notcontains|contains)',
                                             element)

                # S_ 去空格
                split_element = [e.replace(' ', '') for e in split_element]

                expression_id = letters[i]
                question_id = split_element[0]
                operator = split_element[1]
                value = split_element[2]
                value = ast.literal_eval(value)

                # S_ 如果 question_id 中有 *，則略過
                if '*' in question_id:
                    full_expression_body += '1 == 1'
                    continue

                if isinstance(value, int) or isinstance(value, float):
                    value = {
                        'type': 'string',
                        'withNote': False,
                        'stringValue': str(value),
                    }
                elif isinstance(value, list):
                    value = {
                        'type': 'choiceList',
                        'withNote': False,
                        'choiceListValue': [{'id': str(i), 'body': ''} for i in value],
                    }
                else:
                    value = {
                        'type': 'string',
                        'withNote': False,
                        'stringValue': value,
                    }

                if question_id == 'ANS':
                    question_id = row['questionId']

                operator = self.translate(operator, 'operator')

                full_expression_body += expression_id
                i += 1

                expression_dict[expression_id] = {
                    'field': question_id,
                    'operator': operator,
                    'comparisonValue': value  # TODO try catch
                }

        result = {
            'fullExpressionBody': full_expression_body,
            'expressionMap': expression_dict
        }

        return result

    except:
        self.set_where(3, f'題號 {row["questionId"]} 的 {row[column]}', error=True)
