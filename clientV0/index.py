from flask import Flask, redirect, url_for, render_template, request, send_from_directory
app=Flask(__name__)
@app.route('/static/<file_name>')
def render_static(file_name):
    return send_from_directory('templates', file_name)
@app.route('/')
def render_index():
    return redirect('/static/sign.html')

if __name__=='__main__':
    app.run('127.0.0.1',8000)