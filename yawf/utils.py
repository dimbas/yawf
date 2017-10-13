def escape(s=None):
    if s is None:
        return ''

    elif not isinstance(s, str):
        s = str(s)

    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', "&quot;")
