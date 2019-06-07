def underscore_to_camelcase(value):
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
