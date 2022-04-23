from flask import Flask, session, request
import sqlite3

# -!-! Flask configuration -!-!-
app = Flask(__name__)
app.secret_key = "super key much secrecy"

# -!-!- Endpoints -!-!-

# Starting point
@app.route("/", methods=['GET'])
def start():
    # Present the first page to a client
    post_form = open("getcsv.html", "r")
    return post_form.read()


# Extract data out of CSV file into HTML form
@app.route("/datatypes", methods=['GET', 'POST'])
def datatypes():
    if request.method == 'POST':

        # Collect necessary information about types of data in csv
        if request.form.get('datatype0') is None and request.form.get('queryType') is None:

            # Get the CSV file, store it for later, and prepare for further operations : )
            dataset_file = request.form.get('dataset')
            session['dataset'] = dataset_file
            dataset = open(dataset_file, 'r')

            # Get the CSV headline (containing names of the columns)
            headline = dataset.readline().split('\n')[0]

            # Format the headline into a list 'words' and store it for later
            words = format_csv_line(headline)
            session['headline'] = words

            # !!! This method is not safe, using it risks code injection !!!
            # Prepared HTML snippet
            snippet = '<label>Column {}: {}</label> <br> <input type="text" name="datatype{}"> <br>'

            # Form start
            form = '<form method="post" action="/csv_to_db">'

            # Server asks client for data type in each column of the CSV
            for i in range(len(words)):
                # form is being created based on CSV file content
                form += snippet.format(i, words[i], i)

            # Form ending
            form += '<input type="submit" value="upload"> </form>'

            # Html template
            html = open('datatypes.html', 'r').read()

            # proceed further
            return html + form


# Create a DB table filled with csv data
@app.route("/csv_to_db", methods=['GET', 'POST'])
def csv_to_db():
    # Prepare variables stored in session
    dataset = open(session['dataset'], 'r')
    headline = session['headline']

    # Prepare column names and types to match 'create table' query
    name_and_type = headline[0]
    name = headline[0]
    name_and_type += " " + request.form.get('datatype{}'.format(0))
    for i in range(1, len(headline)):
        name_and_type += ", " + headline[i]
        name += ", " + headline[i]
        name_and_type += " " + request.form.get('datatype{}'.format(i))

    # Connect to DB
    connection, cursor = connect_db()

    # Provide fresh DB table
    db_new_table(cursor, name_and_type)

    # Prepare variable to store data in a list
    data_list = []
    test = ""

    # Prepare dataset
    dataset = dataset.read().split('\n')

    # Prepare csv data for insertion into table
    for i in dataset:
        # Break the line into words
        words = format_csv_line(i)
        test += i

        # Skip the first line with column names
        if words != headline:
            # Used to store a single line of data
            # Tuple shares format with values in insert,
            # List words is cast to tuple and then into strings for easy format manipulation
            dataline = tuple(words)
            data_list.append(dataline)

    # Insert all the data from csv into DB
    for i in range(len(data_list)):
        cursor.execute("INSERT INTO CSV(" + name + ") VALUES" + str(data_list[i]) + ";")

    # Close the connection with DB
    close_connection(connection)

    # Proceed further
    queryhtml = open("query.html")
    return queryhtml.read()


# !!! Super vulnerable to code injection !!!
# Perform operations on DB
@app.route("/query", methods=['GET', 'POST'])
def query():
    # Simple select operation
    if request.form.get('queryType') == 'select':

        # Prepare the query
        query = "SELECT " + request.form.get('queryItems') + " FROM CSV;"

        # Connect to DB
        connection, cursor = connect_db()

        # Execute query
        cursor.execute(query)

        # Fetch the results
        result = cursor_to_html_table(cursor)

        # Close the connection with DB
        close_connection(connection)

        # Proceed further
        queryhtml = open("query.html")
        return queryhtml.read() + result

    # Select operation with condition
    elif request.form.get('queryType') == 'selectWhere':

        # Prepare the query
        query = 'SELECT ' + request.form.get('queryItems') + " FROM CSV WHERE " + request.form.get('queryCondition') + ';'

        # Connect to DB
        connection, cursor = connect_db()

        # Execute query
        cursor.execute(query)

        # Fetch the results
        result = cursor_to_html_table(cursor)

        # closing the connection with DB
        close_connection(connection)

        # proceeding further
        queryhtml = open("query.html")
        return queryhtml.read() + result

    # Query defined by client
    else:

        # Prepare the query
        query = request.form.get('queryOwn')

        # Connect to DB
        connection, cursor = connect_db()

        # Execute query
        cursor.execute(query)

        # Fetch the results
        result = cursor_to_html_table(cursor)

        # Close the connection with DB
        close_connection(connection)

        # Proceed further
        queryhtml = open("query.html")
        return queryhtml.read() + result


# -!-!- Functions -!-!-

# Format a line of CSV into a list of values
def format_csv_line(line):
    # Prepare the variables
    words = []
    word = ""

    # Format the data
    for char in line:
        if char == ',':
            words.append(word)
            word = ""
        else:
            word = word + char
    words.append(word)
    return words


# Connect to DB, return connection and cursor
def connect_db():
    connection = sqlite3.connect('local.db')
    cursor = connection.cursor()
    return connection, cursor


# Drop old table, prepare a new one with correct parameters
def db_new_table(cursor, name_and_type):
    # Drop old table
    drop = "DROP TABLE CSV;"
    cursor.execute(drop)

    # Create new table
    dataset_file = "CREATE TABLE CSV (" + name_and_type + ");"
    cursor.execute(dataset_file)


# Save changes and close the connection
def close_connection(connection):
    connection.commit()
    connection.close()


# Format data from cursor to a nice HTML table
def cursor_to_html_table(cursor):
    # Collect headline from session data
    headline = session['headline']

    # Declare the table
    html_table = ""

    # Used to count number of columns
    columns_number = 0

    # Fill the table with data
    for row in cursor:

        # Count the columns
        columns_number = 0

        # Move to a new row
        html_table += "</tr><tr>"

        # Put the data in columns
        for i in row:
            columns_number += 1
            html_table += "<td>" + str(i) + "</td>"

    # Create table header:

    # Used to create header that will never be too wide
    col_num = columns_number + 1

    # Declare the start of the table
    header = '<table><tr>'

    # Header contents
    for i in headline:
        col_num -= 1

        # Make the headline as wide as table content
        if col_num == 0:
            col_num = columns_number
            header += '<tr></tr>'

        # Fill header with data
        header += '<th>' + i + '</th>'

    # End the header
    header += '</tr>'

    # Write start and end to the table
    html_table = header + html_table
    html_table += '</tr></table>'

    # Return the table
    return html_table

# Starting aplication
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False, port="5000")