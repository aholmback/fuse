def extract_section(content, start, end):
    cr = '\n'
    lines = content.split(cr)
    start_index = None
    end_index = None

    for i, line in lines:
        if start_index is None and start in line:
            start_index = i

        if end in line:
            end_index = i+1

    if end_index is None and start_index is None:
        return content, '', ''

    if end_index is None:
        end_index = len(lines)

    if start_index is None:
        start_index = end_index - 1

    above = cr.join(lines[:start_index])
    content = cr.join(lines[start_index:end_index])
    below = cr.join(lines[end_index:])

    return above, content, below

