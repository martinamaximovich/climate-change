
import os
from datetime import date
from decimal import Decimal

from flask import (Flask, Response, g, redirect, render_template, request,
                   session, url_for)
# Accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool

tmpl_dir = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = 'super secret key'

#
# Connect to Part 2 database to use the data.
#
DATABASEURI = "postgresql://mm5775:2072@34.75.94.195/proj1part2"

#
# Create a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)


@app.before_request
def before_request():
    """
    This function is run at the beginning of every web request
    (every time you enter an address in the web browser).
    We use it to setup a database connection that can be used thru request

    The variable g is globally accessible.
    """
    try:
        g.conn = engine.connect()
    except:
        print("Uh oh, problem connecting to database")
        import traceback
        traceback.print_exc()
        g.conn = None


@app.teardown_request
def teardown_request(exception):
    """
    At the end of web request, this makes sure to close database connection.
    If you don't, the database could run out of memory!
    """
    try:
        g.conn.close()
    except Exception as e:
        pass

# PROJECT FUNCTIONS
###############################################################################
# Welcome page


@app.route('/', methods=['GET'])
def welcome():
    print('welcome')
    return render_template("welcome.html")


###############################################################################
# Register as user

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    print('create_account')
    if request.method == 'POST':
        print('request method POST')
        username = request.form['username']
        print(username)
        password = request.form['password']
        print(password)

        # Execute a SQL query to check if username is already taken
        try:
            print('Verifying if username is available...')
            cursor = g.conn.execute(
                """SELECT DISTINCT UP.username
                FROM User_Password UP
                WHERE UP.username = %s""",
                username)

            # If NOT empty output, go back to create_account
            if cursor.fetchone() is not None:
                print('ERR: This username is already taken:(')
                print('Please choose another username')
                return redirect('/create_account')
        except:
            print('ERR: Account creation failed. Please try again')
            return redirect('/create_account')
        
        # Make sure that the user didn't just click on button
        if (len(username) == 0) or (len(password) == 0):
            print("ERR: Please provide a valid username-password pair")
            return redirect('/create_account')

        # Otherwise, succeeded:
        # 1. Save username
        session['username'] = username
        print(session['username'])
        # 2. Save password
        session['password'] = password
        print(session['password'])
        # 2. Send the user to user_info so that they can complete account
        print('Redirecting to user info')
        return redirect('/user_info')
    print('Going back to create_account...')
    return render_template('create_account.html')


###############################################################################
# Log into existing account as user

@app.route('/login', methods=['GET', 'POST'])
def login():
    print('login')
    print(request.method)
    if request.method == 'POST':
        print('request method POST')
        username = request.form['username']
        print(username)
        password = request.form.get('password')
        print(password)

        # Execute a SQL query to check if this user already exists
        try:
            print('Verifying if account exists...')
            cursor = g.conn.execute(
                """SELECT DISTINCT UP.username, UP.password
                FROM User_Password UP
                WHERE UP.username = %s AND UP.password = %s""",
                username,
                password)

            # If empty output, go back to login
            if cursor.fetchone() is None:
                print('ERR: An account with this username-password does not exist')
                print(
                    'Please provide valid username and password, or create a new account')
                return redirect('/login')
        except Exception as e: 
            print(e)
            print('ERR: Login failed. Please try again')
            return redirect('/login')

        # Otherwise, login succeeded:
        # 1. Save username
        session['username'] = username
        print(session['username'])
        # 2. Save hometown to use in guess
        try:
            cursor = g.conn.execute(
                """SELECT UR.hometown
                FROM Users_Registered UR
                WHERE UR.username = %s""",
                username)
            hometown = cursor.fetchone()[0]
            session['hometown'] = hometown
        except Exception as e: 
            print(e)
            print('ERR: Fetching hometown in login failed')
            return redirect('/login')
        # 3. Otherwise, send the user to user_dashboard
        print('Redirecting to user dashboard...')
        # return redirect('/user_dashboard')
        return redirect('/user_dashboard')
    print('Going back to login...')
    return render_template('login.html')

# Log out of session
@app.route('/logout')
def logout():
    # TO DO: Figure out how to initialize the value of session
    session.clear()
    return redirect('/')

###############################################################################
# Submit user info to complete account creation

@app.route('/user_info', methods=['GET', 'POST'])
def user_info():
    print('user_info')
    print(request.method)

    if request.method == 'POST':
        # Execute SQL query to insert into
        # table User_Password
        try:
            print('Executing query to create a new account')
            cursor = g.conn.execute(
                """INSERT INTO User_Password(username, password) VALUES (%s, %s)""",
                session['username'],
                session['password'])
        except Exception as e: 
            print(e)
            # If creating new account failed, redirect back to create_account
            # Failed most likely b/c such a username already exists in User_Password
            print("ERR: Creating new account failed. Please try again!")
            return redirect("/create_account")

        # Demographic info about the user
        gender = request.form['gender']
        print(gender)
        dob = request.form['dob']
        print(dob)
        race = request.form['race']
        print(race)
        ethnicity = request.form['ethnicity']
        print(ethnicity)
        education = request.form['education']
        print(education)
        political_views = request.form['political_views']
        print(political_views)

        # Info about user's hometown
        hometown = request.form['hometown']
        # Save hometown to use later
        session['hometown'] = hometown
        print(hometown)
        state = request.form['state']
        print(state)
        since = request.form['since']
        print(since)

        # Make sure that the user didn't just click on button
        if ((len(gender) == 0) or (len(dob) == 0) or (len(race) == 0) or 
        (len(ethnicity) == 0) or (len(education) == 0) or (len(political_views) == 0) or
        (len(hometown) == 0) or (len(state) == 0) or (len(since) == 0)):
            print("ERR: Please make sure to fill out every field")
            return redirect('/user_info')
            
        # Execute SQL query to check if hometown exists in City_Stat;
        # if not, replace hometown provided by user with capital of state
        try:
            print('Executing query to check if data available for hometown')
            print(hometown)
            cursor = g.conn.execute(
                """SELECT COUNT(*)
                FROM City_Stat CS
                WHERE CS.city_name=%s""",
                hometown)
            result = cursor.fetchone()[0]
            print("count query worked")
            print(result)

            if result == 0:
                try:
                    print('Executing query to get capital of state')
                    cursor = g.conn.execute(
                        """SELECT DISTINCT CS.city_name
                        FROM City_Stat CS
                        WHERE CS.state=%s""",
                        state)
                    state_capital = cursor.fetchone()[0]
                    print(state_capital)
                    hometown = state_capital
                    # Save hometown to use later
                    session['hometown'] = hometown
                except Exception as e: 
                    print(e)
                    print("ERR: Fetching state capital failed. Please try again!")
                    return redirect("/create_account")
        except Exception as e: 
            print(e)
            # If creating new account failed, redirect back to create_account
            # Failed most likely b/c such a username already exists in User_Password
            print("ERR: Checking if data available for hometown failed")
            print("Please try again!")
            try:
                g.conn.execute("""DELETE FROM User_Password
                WHERE username=%s""",
                session['username'])
            except Exception as e: 
                print(e)
                print('ERR: Deleting from User_Password failed. Please try again')
                return redirect('/user_info')
            return redirect("/create_account")

        # Execute a SQL query to add info to Users
        try:
            g.conn.execute("""INSERT INTO Users_Registered(username, gender, dob, race, ethnicity, education, political_views,
            hometown, state, since) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                           session['username'], gender, dob, race, ethnicity, education, political_views, hometown, state, since)
        except Exception as e: 
            print(e)
            print('ERR: Providing user info failed. Please try again')
            # If inserting into Users_Registered failed, need to also
            # remove the new record from User_Password
            try:
                g.conn.execute("""DELETE FROM User_Password
                WHERE username=%s""",
                session['username'])
            except Exception as e: 
                print(e)
                print('ERR: Deleting from User_Password failed. Please try again')
                return redirect('/user_info')
            return redirect('/user_info')
        # Account successfully created, so go to user dashboard
        print('Redirecting to user dashboard')
        return redirect('/user_dashboard')
    print('Going back to user_info')
    return render_template('user_info.html')

# User dashboard
@app.route('/user_dashboard', methods=['GET', 'POST'])
def user_dashboard():
    if request.method == 'POST':
        print('Redirecting to logout')
        return redirect('/logout')
    print("on user dashboard")
    print(request.method)
    return render_template('user_dashboard.html')


###############################################################################
# Submit quiz responses in the user dashboard

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    print('quiz')
    print(request.method)
    # Since one user can only submit a single quiz, send to view_quiz_results
    try:
        print('Checking if user has active quiz')
        cursor = g.conn.execute(
            """SELECT COUNT(*) 
            FROM Questionnaires Q
            WHERE Q.username=%s""",
            session['username'])
        result = cursor.fetchone()[0]
        print(result)
        if result != 0:
            print("Redirecting to view quiz results...")
            # Calculate score
            cursor = g.conn.execute(
                """SELECT Q.response1, Q.response2,
                Q.response3, Q.response4, Q.response5
                FROM Questionnaires Q 
                WHERE Q.username=%s""",
                session['username'])

            print("this is using fetchall() and list()")
            result = list(cursor.fetchall())
            print("Extracting values from Decimal...")
            user_responses = []
            for row in result:
                user_responses.append(list(map(str, list(row))))
            print(user_responses)

            # Calculating total score of user
            total_score = 0
            for i in range(len(user_responses)):
                total_score += int(user_responses[0][i])
            print(total_score)

            if (total_score > 32):
                return redirect('/view_responses_earthlover')
            elif (total_score > 16) and (total_score < 32):
                return redirect('/view_responses_unconcerned')
            else:
                return redirect('view_responses_averagejoe')
    except Exception as e: 
        print(e)
        # If inserting into Questionnaires failed, try again
        print("ERR: Quiz submission failed. Please try again!")
        return redirect("/quiz")

    if request.method == 'POST':

        # User's responses to quiz
        response1 = request.form['response1']
        response2 = request.form['response2']
        response3 = request.form['response3']
        response4 = request.form['response4']
        response5 = request.form['response5']

        # Make sure that the user didn't just click on button
        if ((len(response1) == 0) or (len(response2) == 0) or 
        (len(response3) == 0) or (len(response4) == 0) or 
        (len(response5) == 0)):
            print("ERR: Please make sure to fill out every field")
            return redirect('/quiz')

        # Get today's date
        submitted_on = date.today().strftime('%Y-%m-%d')

        # Execute SQL query to insert responses into Questionnaires
        try:
            print('Executing query to create a new account')
            cursor = g.conn.execute("""INSERT INTO Questionnaires(username, 
            response1, response2, response3, response4, response5, 
            submitted_on) VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                                    session['username'],
                                    response1, response2, response3, 
                                    response4, response5,
                                    submitted_on)
        except Exception as e: 
            print(e)
            # If inserting into Questionnaires failed, try again
            print("ERR: Quiz submission failed. Please try again!")
            return redirect("/quiz")

        # Calculate score
        score = (int(response1) + int(response2) + int(response3) + 
        int(response4) + int(response5))

        if (score > 32):
            return redirect('/view_responses_earthlover')

        elif (score > 16) and (score < 32):
            return redirect('/view_responses_unconcerned')

        else:
            return redirect('view_responses_averagejoe')
    print('Going back to quiz...')
    return render_template("quiz.html")

# View quiz results
@app.route('/view_quiz_results', methods=['GET'])
def view_quiz_results():
    # Fetch all guesses for the city
    # 1. Fetch compare_to_stat_id_actual of user's guess
    cursor = g.conn.execute("""SELECT UG.compare_to_stat_id_actual
    FROM User_Guesses UG
    WHERE UG.stat_id=%s""",
    session['guess_id'])
    compare_to_stat_id_actual = cursor.fetchone()[0]

    # 2. Fetch all guesses about that city
    cursor1 = g.conn.execute("""SELECT UG.username, 
    UG.hometown, ROUND(UG.temp_avg, 3), 
    ROUND(UG.min_temp_avg, 3), 
    ROUND(UG.max_temp_avg, 3), 
    UG.submitted_on, UG.accuracy 
    FROM User_Guesses UG 
    WHERE UG.compare_to_stat_id_actual=%s 
    ORDER BY UG.accuracy DESC""", 
    compare_to_stat_id_actual)
    responses = cursor1.fetchall()
    print(responses)
    
    # Fetch actual temp statistics for the city
    cursor2 = g.conn.execute("""SELECT ROUND(ATS.temp_avg, 3), 
    ROUND(ATS.min_temp_avg, 3), 
    ROUND(ATS.max_temp_avg, 3) 
    FROM Actual_Temp_Statistics ATS JOIN User_Guesses UG 
    ON ATS.stat_id=UG.compare_to_stat_id_actual
    WHERE UG.stat_id=%s""", 
    session['guess_id'])
    city_statistics = cursor2.fetchall()
    print(city_statistics)

    # Fetch compare_to_stat_id_actual for the user
    cursor3 = g.conn.execute("""SELECT ROUND(UG.temp_avg, 3), 
    ROUND(UG.min_temp_avg, 3), 
    ROUND(UG.max_temp_avg, 3)
    FROM User_Guesses UG
    WHERE UG.stat_id=%s""",
    session['guess_id'])
    user_responses = cursor3.fetchall()
    print(user_responses)

    return render_template("view_quiz_results.html", responses=responses, 
    city_statistics=city_statistics, user_responses=user_responses)

# View questionnaire responses --> earthlover
@app.route('/view_responses_earthlover', methods=['GET'])
def view_responses_earthlover():
    cursor = g.conn.execute("""SELECT UR.username, UR.gender, UR.dob, UR.race, 
    UR.ethnicity, UR.education, UR.political_views, UR.hometown, UR.state 
    FROM Users_Registered UR NATURAL JOIN Questionnaires Q 
    WHERE Q.response1 + Q.response2 + Q.response3 + 
    Q.response4 + Q.response5 > 32""")
    data = cursor.fetchall()
    return render_template('view_responses_earthlover.html', data=data)

# View questionnaire responses --> average joe
@app.route('/view_responses_averagejoe', methods=['GET'])
def view_responses_averagejoe():
    cursor = g.conn.execute("""SELECT UR.username, UR.gender, UR.dob, UR.race, 
    UR.ethnicity, UR.education, UR.political_views, UR.hometown, UR.state 
    FROM Users_Registered UR NATURAL JOIN Questionnaires Q 
    WHERE Q.response1 + Q.response2 + Q.response3 + 
    Q.response4 + Q.response5 BETWEEN 16 AND 32""")
    data = cursor.fetchall()
    return render_template('view_responses_averagejoe.html', data=data)

# View quiz responses
@app.route('/view_responses_unconcerned', methods=['GET'])
def view_responses():
    cursor = g.conn.execute("""SELECT UR.username, UR.gender, UR.dob, UR.race, 
    UR.ethnicity, UR.education, UR.political_views, UR.hometown, UR.state 
    FROM Users_Registered UR NATURAL JOIN Questionnaires Q 
    WHERE Q.response1 + Q.response2 + Q.response3 + 
    Q.response4 + Q.response5 < 16""")
    data = cursor.fetchall()
    return render_template('view_responses_unconcerned.html', data=data)


###############################################################################
# Make guesses regarding temperature changes

@app.route('/guess', methods=['GET', 'POST'])
def guess():
    guesses = []

    print("on guess page")
    print(request.method)
    if request.method == 'POST':
        # Get username and hometown
        username = session['username']
        print(username)
        hometown = session['hometown']

        # User's guesses about temperature change
        temp_avg = request.form["temp_avg"]
        guesses.append(temp_avg)
        min_temp_avg = request.form["min_temp_avg"]
        guesses.append(min_temp_avg)
        max_temp_avg = request.form["max_temp_avg"]
        guesses.append(max_temp_avg)

        # If hometown NOT in City_Stat, find nearest city
        # and get actual temp data for that
        try:
            print('Executing query to check if data available for hometown')
            print('If not, replace with closest city')
            print(hometown)
            cursor = g.conn.execute(
                """SELECT ATS.temp_avg 
                FROM Actual_Temp_Statistics ATS NATURAL JOIN City_Stat CS 
                WHERE CS.city_name=%s""",
                hometown)
            actual_temp_avg = cursor.fetchone()[0]
            print("ATS query worked")
            print(actual_temp_avg)
            # Get a new closest city until find one with non-null temp data
            count = 1
            closest_city = None
            while actual_temp_avg is None:
                # Find closest city with non-null temp data
                # 1. Fetch latitude of hometown
                try:
                    print('Fetching latitude of hometown')
                    cursor = g.conn.execute("""SELECT CS.latitude 
                    FROM City_Stat CS 
                    WHERE CS.city_name=%s""",
                    hometown)
                    latitude = cursor.fetchone()[0]
                except Exception as e: 
                    print(e)
                    print("ERR: Fetching latitude of hometown failed")
                    return redirect("/guess")

                # 2. Fetch longtiude of hometown
                try:
                    print('Fetching longitude of hometown')
                    cursor = g.conn.execute("""SELECT CS.longitude 
                    FROM City_Stat CS 
                    WHERE CS.city_name=%s""",
                    hometown)
                    longitude = cursor.fetchone()[0]
                except Exception as e: 
                    print(e)
                    print("ERR: Fetching longitude of hometown failed")
                    return redirect("/guess")

                # 3. Fetch name of closest city
                try:
                    print('Fetching closest city')
                    cursor = g.conn.execute("""SELECT CS.city_name, 
                    ( 3959 * acos( cos( radians(%s) ) * cos( radians( CS.latitude ) ) 
                    * cos( radians( CS.longitude ) - radians(%s) ) + sin( radians(%s) ) 
                    * sin( radians( CS.latitude ) ) ) ) AS distance FROM City_Stat CS 
                    WHERE CS.city_name!=%s ORDER BY distance ASC LIMIT %s;""",
                                            latitude, longitude, latitude,
                                            hometown,
                                            count)
                    row = cursor.fetchone()
                    while row is not None: 
                        closest_city = row[0]
                        row = cursor.fetchone()
                    # Increment count
                    count += 1
                    # Update temp_avg
                    cursor = g.conn.execute(
                        """SELECT ATS.temp_avg 
                        FROM Actual_Temp_Statistics ATS NATURAL JOIN City_Stat CS 
                        WHERE CS.city_name = %s""",
                        closest_city)
                    actual_temp_avg = cursor.fetchone()[0]

                except Exception as e: 
                    print(e)
                    print("ERR: Fetching closest city failed")
                    return redirect("/guess")

            if closest_city is not None:
                hometown = closest_city
            
        except Exception as e: 
            print(e)
            print('ERR: Query to check if data available for hometown failed')
            return redirect('/guess')

        # Calculate stat_id
        # 1. Check if User_Guesses table is empty
        # If yes, fetch largest stat_id from Actual_Temp_Statistics
        # and assign stat_id to that + 1
        # Otherwise, get largest stat_id from User_Guesses
        try:
            print('Checking if User_Guesses empty')
            cursor = g.conn.execute(
                """SELECT COUNT(*) 
                FROM User_Guesses""")
            result = cursor.fetchone()[0]
            print(result)
            if result == 0:
                try:
                    cursor = g.conn.execute(
                        """SELECT MAX(ATS.stat_id)
                        FROM Actual_Temp_Statistics ATS""")
                    stat_id = cursor.fetchone()[0] + 1
                    #assign to variable?
                    print(stat_id)
                except Exception as e: 
                    print(e)
                    print("ERR: Fetching largest stat_id from ")
                    print("Actual_Temp_Statistics failed")
                    return redirect("/guess")
            else:
                try:
                    cursor = g.conn.execute(
                        """SELECT MAX(UG.stat_id)
                        FROM User_Guesses UG""")
                    stat_id = cursor.fetchone()[0] + 1
                    print(stat_id)
                except Exception as e: 
                    print(e)
                    print("ERR: Fetching largest stat_id from ")
                    print("User_Guesses failed")
                    return redirect("/guess")
            # Set session variable guess_id
            session['guess_id'] = stat_id
        except Exception as e:
            print(e)
            print("ERR: Checking if User_Guesses is empty failed")
            return redirect("/guess")

        # Get compare_to_stat_id_actual from City_Stat
        # 1. Fetch stat_id from City_Stat where city_name == hometown
        try:
            cursor = g.conn.execute(
                """SELECT CS.stat_id
                FROM City_Stat CS
                WHERE CS.city_name=%s""",
                hometown)
            compare_to_stat_id_actual = cursor.fetchone()[0]
            print(compare_to_stat_id_actual)
        except Exception as e:
            print(e)
            print("ERR: Fetching stat_id from City_Stat failed")
            return redirect("/guess")

        # Calculate accuracy
        # 1. Iterate through list guesses
        # 2. Compare every element to result of SQL query,
        # which fetches corresponding temp metric from
        accuracy = 0
        i = 0
        #actual_statistics = []
        # Fetch actual statistics from Actual_Temp_Statistics
        try:
            print("fetching temps from ATS")
            cursor = g.conn.execute(
                """SELECT ATS.temp_avg, ATS.min_temp_avg, ATS.max_temp_avg 
                FROM Actual_Temp_Statistics ATS 
                WHERE ATS.stat_id=%s""",
                compare_to_stat_id_actual)

            print("this is using fetchall() and list()")
            result = list(cursor.fetchall())
            print("Extracting values from Decimal...")
            actual_temp = []
            for row in result:
                actual_temp.append(list(map(str, list(row))))
            print(actual_temp)

            # Calculating total accuracy of guesses
            # If value within +/-30% of actual, increment accuracy
            for i in range(len(guesses)):
                print(float(actual_temp[0][i]))
                print(float(guesses[i]))
                if abs((float(actual_temp[0][i]) - float(guesses[i])) / float(actual_temp[0][i])) <= 0.3:
                    accuracy += 1
            print(accuracy)
        except Exception as e: 
            print(e)
            print("ERR: Fetching stats from Actual_Temp_Statistics failed")
            return redirect("/guess")
        
        # Get today's date
        submitted_on = date.today().strftime('%Y-%m-%d')

        # Execute SQL query to insert responses into Questionnaires
        try:
            print('executing query to create a new account')
            cursor = g.conn.execute("""INSERT INTO User_Guesses(stat_id, 
            temp_avg, min_temp_avg, max_temp_avg, 
            hometown, submitted_on, username, 
            accuracy, compare_to_stat_id_actual) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            stat_id,
            temp_avg, min_temp_avg, max_temp_avg,
            hometown, submitted_on, username,
            accuracy, compare_to_stat_id_actual)
        except Exception as e: 
            print(e)
            # If inserting into User_Guesses failed, try again
            print("ERR: Submission of guesses failed. Please try again!")
            return redirect("/guess")

        # Quiz successfully submitted, so go to quiz_results
        print('Redirecting to quiz_results...')
        return redirect('/view_quiz_results')
    # Should we remove this completely?? If not post, then just stay on the page
    print('Going back to guess...')
    return render_template("guess.html")


###############################################################################
# Main method
if __name__ == "__main__":
    import click

    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):

        HOST, PORT = host, port
        print("running on %s:%d" % (HOST, PORT))
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

    run()
