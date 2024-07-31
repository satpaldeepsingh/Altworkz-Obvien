from datetime import datetime

import dateutil.parser
import json
import os
import re

'''
start_date_format = '%y-%b'

org_end_time = result_item[self.fields['organization_end n'] + field_num]

if org_start_time.isnumeric():

    start_date_format = '%Y'

else:

    org_start_time = org_start_time if len(org_start_time.split('-')[0]) > 1 else '0' + org_start_time

end_date_format = '%y-%b'

if org_end_time.isnumeric():

    end_date_format = '%Y'

else:

    org_end_time = org_end_time if len(org_end_time.split('-')[0]) > 1 else '0' + org_end_time

org_start_time = datetime.strptime(org_start_time, start_date_format)

org_end_time = datetime.strptime(org_end_time, end_date_format) if not "PRESENT" else datetime.today().strftime("%y-%b")

print(org_end_time)
print(org_start_time)
'''


# print("Org start date " + str(org_start_time) + " Org end date " + str(org_end_time))

# print(abs(org_end_time - org_start_time).days)

# print(self.fields['organization_title n'] + " (" + org_start_time + ' - ' + org_end_time + ") in " + result_item[self.fields['organization n']+ field_num])

# result_item['weightage']['field_weightage'] += field_weightages.get(ri_field, self.sec_field_def_weight) # if field is among field_weightages then assign its weightage otherwise set default weight

def to_lower_and_split_if_name_field(ri_field, ri_value, fields):
    ri_value = ri_value.lower()

    if ri_field == fields['first_name'] or ri_field == fields['last_name'] or ri_field == fields['full_name']:
        ri_value = ri_value.split(' ')

    return ri_value


def convert_to_format(date):
    # print("actual date string")
    # print(date)
    # print("Parsed date : ")
    # print(dateutil.parser.parse(date))

    if date == "PRESENT" or date == 'present':
        # print_gen_date(datetime.today().strftime("%m-%d-%Y"), "%m-%d-%Y")

        return datetime.today().strftime("%m-%d-%Y")

    # print("Date str " + date)

    date_format = '%y-%b'

    if date.isnumeric():

        date_format = '%Y'

    else:

        period_separator = re.sub('[A-Za-z0-9]+', '', date)

        if period_separator == '-':

            date = date.split(period_separator)

            if date[0].isnumeric():

                if len(date[0]) == 1:
                    date[0] = '0' + date[0]

                date_format = f'%y{period_separator}%b'

            else:

                date_format = f'%b{period_separator}%y'

            date = period_separator.join(date)

        elif period_separator == '/':

            date_format = f'%m{period_separator}%Y'

    # print("Generated date ")
    # print(datetime.strptime(date, date_format).strftime('%m-%d-%Y'))

    return datetime.strptime(date, date_format).strftime('%m-%d-%Y')


# print generated date
def print_gen_date(date, date_format):
    print("Generated Date ....... ")
    print(datetime.strptime(date, date_format).strftime('%m-%d-%Y'))


def months_bw_date_intervals(end_date, start_date):
    # print("diff b/w " + end_date + " and " + start_date)

    if check_if_any_date_unknown([start_date, end_date]):
        return 0

    start_date = datetime.strptime(start_date, '%m-%d-%Y')
    end_date = datetime.strptime(end_date, '%m-%d-%Y')

    # print("Calculated diff " + str((end_date.year - start_date.year) * 12 + end_date.month - start_date.month))

    return (end_date.year - start_date.year) * 12 + end_date.month - start_date.month


def months_bw_date_intervals_fmt(end_date, start_date):

    if check_if_any_date_unknown([start_date, end_date]):

        return 0

    # print("start date fmt")
    end_date_fmt = convert_to_format(end_date)
    # print("end date fmt")
    start_date_fmt = convert_to_format(start_date)

    # print("-------------------------------")

    # print("Start Date " + start_date)
    # print("End Date " + end_date)

    # print("Start Date fmt " + start_date_fmt)
    # print("End Date fmt " + end_date_fmt)

    # print("Start Date fmt " + start_date_fmt)
    # print("End Date fmt " + end_date_fmt)

    # print("-------------------------------")

    return months_bw_date_intervals(end_date_fmt, start_date_fmt)


def print_json(json_obj):
    print(json.dumps(json_obj, sort_keys=False, indent=4))


# clear all contents on console screen before printing this screen
def print_json_clr(json_obj):
    os.system('cls')  # clear screen to refresh console messages
    print(json.dumps(json_obj, sort_keys=False, indent=4))


def json_fmt(json_obj):
    return json.dumps(json_obj, sort_keys=False, indent=4)


def get_field_n(field_name):
    field_words = field_name.split('_')
    field_num = field_words[len(field_words) - 1]

    return field_num


def check_if_any_date_unknown(dates_array):
    for date_ in dates_array:

        if date_ == '' or (date_ not in ['present', 'PRESENT'] and date_.isalpha()):
            return True

    return False






