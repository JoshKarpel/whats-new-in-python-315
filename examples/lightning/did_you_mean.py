import traceback

def hint(expression):
    try:
        eval(expression)
    except AttributeError as error:
        print(traceback.format_exception_only(error)[-1].strip())

hint("[1, 2].push(3)")
hint("'hi'.toUpperCase()")
