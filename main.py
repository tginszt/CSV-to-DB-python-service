from flask import Flask, session, request
import sqlite3

# -!-! Flask configuration -!-!-
app = Flask(__name__)
app.secret_key = "super key much secrecy"


# -!-!- GET and POST handler -!-!-
@app.route("/login", methods=['GET', 'POST'])
def login():
    # -!- POST -!-
    if request.method == 'POST':

        # Collect necessary information about types of data in csv
        if request.form.get('datatype0') is None and request.form.get('queryType') is None:

            # Get the CSV file, store it for later, and prepare for further operations : )
            datasetFile = request.form.get('dataset')
            session['dataset'] = datasetFile
            dataset = open(datasetFile, 'r')

            # Get the CSV headline (containing names of the columns)
            headline = dataset.readline().split('\n')[0]

            # Format the headline into a list 'words' and store it for later
            words = FormatCSVLine(headline)
            session['headline'] = words

            # !!! This method is not safe, using it risks code injection !!!
            # Prepared HTML snippet
            snippet = '<label>Column {}: {}</label> <br> <input type="text" name="datatype{}"> <br>'

            # Form start
            form = '<form method="post" target="main.py">'

            # Server asks client for data type in each column of the CSV
            for i in range(len(words)):
                # form is being created based on CSV file content
                form += snippet.format(i, words[i], i)

            # Form ending
            form += '<input type="submit" value="upload"> </form>'

            # Html template
            html = open('describe-columns.html', 'r').read()

            return html + form

        # CSV datatypes are known,DB table can be created
        elif request.form.get('datatype0'):

            # Prepare variables stored in session
            dataset = open(session['dataset'], 'r')
            headline = session['headline']

            # Prepare column names and types to match create table query
            nameAndType = headline[0]
            name = headline[0]
            nameAndType += " " + request.form.get('datatype{}'.format(0))
            for i in range(1, len(headline)):
                nameAndType += ", " + headline[i]
                name += ", " + headline[i]
                nameAndType += " " + request.form.get('datatype{}'.format(i))

            # Connect to DB
            connection, cursor = ConnectDB()

            # Provide fresh DB table
            DBNewTable(cursor, nameAndType)

            # Prepare variable to store data in a list
            datalist = []
            test = ""

            # Prepare dataset
            dataset = dataset.read().split('\n')

            # Prepare csv data for insertion into table
            for i in dataset:
                # Break the line into words
                words = FormatCSVLine(i)
                test += i

                # Skip the first line with column names
                if words != headline:
                    # Used to store a single line of data
                    dataline = tuple(words)
                    datalist.append(dataline)

            # Insert all the data from csv into DB
            for i in range(len(datalist)):
                cursor.execute("INSERT INTO CSV(" + name + ") VALUES" + str(datalist[i]) + ";")

            # Close the connection with DB
            CloseConnection(connection)

            # Proceed further
            selectForm = open("select.html")
            return selectForm.read()

        # !!! Super vulnerable to code injection !!!
        # Perform operations on DB
        else:

            # Simple select operation
            if request.form.get('queryType') == 'select':

                # Prepare the query
                query = 'SELECT ' + request.form.get('queryItems') + " FROM CSV;"

                # Connect to DB
                connection, cursor = ConnectDB()

                # Execute query
                cursor.execute(query)

                # Fetch the results
                result = CursorToString(cursor)

                # Close the connection with DB
                CloseConnection(connection)

                # Proceed further
                selectForm = open("select.html")
                return selectForm.read() + result

            # Select operation with condition
            elif request.form.get('queryType') == 'selectWhere':

                # Prepare the query
                query = 'SELECT ' + request.form.get('queryItems') + " FROM CSV WHERE " + request.form.get(
                    'queryCondition') + ";"

                # Connect to DB
                connection, cursor = ConnectDB()

                # Execute query
                cursor.execute(query)

                # Fetch the results
                result = CursorToString(cursor)

                # closing the connection with DB
                CloseConnection(connection)

                # proceeding further
                selectForm = open("select.html")
                return selectForm.read() + result

            # Query defined by client
            else:

                # Prepare the query
                query = request.form.get('queryOwn')

                # Connect to DB
                connection, cursor = ConnectDB()

                # Execute query
                cursor.execute(query)

                # Fetch the results
                result = CursorToString(cursor)

                # Close the connection with DB
                CloseConnection(connection)

                # Proceed further
                selectForm = open("select.html")
                return selectForm.read() + result

    # -!- GET -!-
    else:
        # Return starting page
        postForm = open("start.html", "r")
        return postForm.read()


# -!-!- Functions -!-!-

# Format a line of CSV into a list of values
def FormatCSVLine(line):
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
def ConnectDB():
    connection = sqlite3.connect('local.db')
    cursor = connection.cursor()
    return connection, cursor


# Drop old table, prepare a new one with correct parameters
def DBNewTable(cursor, nameAndType):
    # Drop old table
    drop = "DROP TABLE CSV;"
    cursor.execute(drop)

    # Create new table
    createTable = "CREATE TABLE CSV (" + nameAndType + ");"
    cursor.execute(createTable)


# Save changes and close the connection
def CloseConnection(connection):
    connection.commit()
    connection.close()


# Collect data from cursor into a string
def CursorToString(cursor):
    result = ""
    for row in cursor:
        result += str(row) + "<br>"
    return result
