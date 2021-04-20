from flask import Flask, render_template, request, redirect, url_for, flash
from pathlib import Path
import os
import pandas as pd
import time
import sqlite3


app = Flask(__name__)
app.config['TEMP_FOLDER'] = 'temp'
app.config['OUTPUT_FOLDER'] = 'output'

# dataframes = {} 
# operationDetailsTemplate = "Operation name: %s\nOperation status: %s\n"
# operationDetails = ''

class Operation:
    dataframes = {} 
    operationDetailsTemplate = "Operation name: %s\nOperation status: %s\n"
    operationDetails = ''
    dfTableDetails = []
    dfTableTitles = []
    dfShape = []
    commonColumns = []
    nthPercentileValues = {}

operation = Operation()

@app.route('/', methods=["GET", "POST"])
def index():
        return render_template('index.html', operation = operation)


@app.route('/uploadCSV', methods=["POST"])
def uploadCSV():
    uploaded_file = request.files['csvFile']
    uniqueDFName = Path(uploaded_file.filename).stem + time.strftime("%Y%m%d-%H%M%S") + '.csv'
    relativePath = os.path.join(app.config['TEMP_FOLDER'], uploaded_file.filename)
    absPath = os.path.abspath(relativePath)
    uploaded_file.save(relativePath)    
    df = pd.read_csv(absPath)
    operation.dataframes[uniqueDFName] = df
    operation.operationDetails = operation.operationDetailsTemplate%('LOAD DATA FROM CSV', 'SUCCESS')
    return redirect('/')

@app.route('/uploadDB', methods=["POST"])
def uploadDB():
    uploaded_file = request.files['dbFile']
    uniqueFileName = Path(uploaded_file.filename).stem + time.strftime("%Y%m%d-%H%M%S") + '.db'
    relativePath = os.path.join(app.config['TEMP_FOLDER'], uniqueFileName)
    absPath = os.path.abspath(relativePath)
    uploaded_file.save(relativePath)    
    conn = sqlite3.connect(absPath)
    cur = conn.cursor()
    cur.execute('SELECT name from sqlite_master where type= "table"')
    tables = cur.fetchall()
    for index, t in enumerate(tables):
        temp = t[0]
        uniqueTableName = 'Table' + str(index+1) + uniqueFileName
        queryString = "SELECT * FROM " + temp
        df = pd.read_sql_query(queryString, conn)
        operation.dataframes[uniqueTableName] = df
    
    operation.operationDetails = operation.operationDetailsTemplate%('LOAD DATA FROM DB', 'SUCCESS')
    return redirect('/')

@app.route('/writeDB', methods=["POST"])
def writeDB():
    dfSelectedName = request.form.get('DF_to_SQLite')
    dfSelected = operation.dataframes[dfSelectedName]
    dbFile = request.files['dbWriteFile']
    relativePath = os.path.join(app.config['OUTPUT_FOLDER'], dbFile.filename)
    absPath = os.path.abspath(relativePath)
    dbFile.save(relativePath)
    conn = sqlite3.connect(relativePath)
    cur = conn.cursor()
    dfSelected.to_sql('new_table', conn, if_exists='replace', index = False)
    cur.execute('select * from new_table')
    operation.operationDetails = operation.operationDetailsTemplate%('Write DF to SQLite DB', 'SUCCESS')
    return redirect('/')

@app.route('/commonColumns', methods=["GET", "POST"])
def showCommonColumns():
    firstDFName = request.form.get('First_DF_common_column')
    secondDFName = request.form.get('Second_DF_common_column')
    if firstDFName != '' and secondDFName != '':
        firstDF = operation.dataframes[firstDFName]
        secondDF = operation.dataframes[secondDFName]
        comCols = []
        for cols in list(firstDF.columns):
            if cols in list(secondDF.columns):
                comCols.append(cols)
        operation.commonColumns = comCols
        operation.operationDetails = operation.operationDetailsTemplate%('Common column names', 'SUCCESS')
    return redirect('/')

@app.route('/nthPercentile', methods=["GET", "POST"])
def calculateNthPercentile():
    dfSelectedName = request.form.get('DF_Nth_Percentile')
    if dfSelectedName != '':
        dfSelected = operation.dataframes[dfSelectedName]
        percentile = int(request.form.get('percentileRange'))
        operation.nthPercentileValues = {}
        if percentile in range(0,101):
            n = percentile/100
            for cols in list(dfSelected.columns):
                if (dfSelected[cols].dtype == 'int64'):
                    operation.nthPercentileValues[cols] = dfSelected[cols].quantile(n)
            operation.operationDetails = operation.operationDetailsTemplate%('Calculate Nth percentile of all the columns with numerical data', 'SUCCESS')
    return redirect('/')

@app.route('/showDetails', methods=["GET", "POST"])
def showDetails():
    dfSelected = request.form.get('DF_Details')
    if dfSelected != '':
        df = operation.dataframes[dfSelected]
        sampleDF = df.head(2)
        operation.dfTableDetails=[sampleDF.to_html(classes='data')]
        operation.dfTableTitles=sampleDF.columns.values
        operation.dfShape = 'Shape of the DF: ' + str(df.shape)
    return redirect('/')

app.run(debug=True)
