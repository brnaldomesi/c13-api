import re


def snakecase_to_camelcase(value):
    output = ''
    is_first_word = False
    for word in value.split('_'):
        if not word:
            output += '_'
            continue
        if is_first_word:
            output += word.capitalize()
        else:
            output += word.lower()
        is_first_word = True
    return output


regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'

def check_email_validity(email):
    if re.search(regex,email):
        return True
    else:  
        return False
