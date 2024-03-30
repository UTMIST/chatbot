import __main__


def process_data_from_file(file_path) :
    # Initialize lists and dictionary to store Q&A and point form representations
    qna_form = []
    point_form = []

    with open ( file_path, 'r' ) as file :
        lines = file.readlines ()

    i = 0
    while i < len ( lines ) :
        line = lines[i].strip ()
        if line.endswith ( '?' ) :
            # This line is a question
            question = line
            i += 1
            if i < len ( lines ) :
                # Check if there's an answer
                answer = lines[i].strip ()
                qna_form.append ( (question, answer) )
            else :
                qna_form.append ( (question, "") )  # If no answer, append an empty string
        else :
            # This is not a question, so treat it as point form
            point_form.append ( line )
        i += 1

    return qna_form, point_form


# Example usage:
# file_path = 'data.txt'  # Update with your file path
# qna, points = process_data_from_file ( file_path )
# print ( "Q&A Form:" )
# for q, a in qna :
#     print ( f"Q: {q}\nA: {a}" )
#
# print ( "\nPoint Form:" )
# for point in points :
#     print ( point )
