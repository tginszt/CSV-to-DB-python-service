from flask import Flask, session, request
import sqlite3

#flask config
app = Flask(__name__)
app.secret_key = "super key much secrecy"

#get and post handler
@app.route("/login", methods=['GET', 'POST'])
def login():
    #POST
    if request.method == 'POST':
        #if we don't know CSV column datatypes yet
        if(request.form.get('datatype0') is None):
            #open the CSV file and save it for later : )
            datasetFile = request.form.get('dataset')
            session['dataset'] = datasetFile
            dataset = open(datasetFile, 'r')

            #get the CSV headline (containing names of the columns)
            headline = dataset.readline().split('\n')[0]

            #format the headline into a list of 'words' and store it for later
            words = FormatCSVLine(headline)
            session['headline'] = words

            # !!! This method is not safe, using it risks code injection !!!
            #prepared HTML snippet
            snippet = '<label>Column {}: {}</label> <br> <input type="text" name="datatype{}"> <br>'

            #form start
            form = '<form method="post" target="main.py">'

            #server asks client for data type in each column of the CSV
            for i in range(len(words)):
                #the form is described with data from the CSV file
                form += snippet.format(i,words[i], i)

            #ending the form
            form += '<input type="submit" value="upload"> </form>'

            #html template
            html = open('describe-columns.html', 'r').read()

            return html + form

        else:
            #prepare variables stored in session
            dataset = open(session['dataset'], 'r')
            headline = session['headline']

            #prepare column names and types to match create table query
            nameAndType = headline[0]
            name = headline[0]
            nameAndType += " " + request.form.get('datatype{}'.format(0))
            for i in range(1, len(headline)):
                nameAndType += ", " + headline[i]
                name += ", " + headline[i]
                nameAndType += " " + request.form.get('datatype{}'.format(i))

            #prepare the DB
            connection = sqlite3.connect('local.db')
            cursor = connection.cursor()

            #cleaning up
            truncate = "DROP TABLE CSV;"
            cursor.execute(truncate)

            #creating the table
            createTable = "CREATE TABLE CSV ("+ nameAndType +");"
            cursor.execute(createTable)

            #preparing variable to store data in a list
            datalist = []
            test = ""

            dataset = dataset.read().split('\n')

            #preparing csv data for insertion into table
            for i in dataset:
                #break the line into words
                words = FormatCSVLine(i)
                test+=i
                # skip the first line with column names
                if words != headline:

                    #used to store a single line of datae

                    dataline = tuple(words)
                    datalist.append(dataline)

            #Insertion of all the data from csv into DB
            for i in range(len(datalist)):
                cursor.execute("INSERT INTO CSV(" + name +") VALUES" + str(datalist[i]) + ";" )

            cursor.execute("SELECT * FROM CSV;")
            result = ""
            for row in cursor:
                result += str(row)

            connection.close()
            return result

            #selectForm = open("select.html")
            #return selectForm.read()

    # no POST
    else:
        #return the HTML form
        postForm = open("start.html", "r")
        return postForm.read()

# format a line of CSV into a list of values
def FormatCSVLine(line):
    words = []
    word = ""
    for char in line:
        if char == ',':
            words.append(word)
            word = ""
        else:
            word = word + char
    words.append(word)
    return words