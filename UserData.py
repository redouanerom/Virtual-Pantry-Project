import sqlite3
import smtplib, ssl
import time


con1 = sqlite3.connect("userdata.db")
con2 = sqlite3.connect("FoodData.db")

cur1 = con1.cursor()
cur2 = con2.cursor()

cur1.execute("CREATE TABLE IF NOT EXISTS UserData (email, password, family size)")

userEmail = input("Enter your email: ")
userPassword = input("Enter your password: ")
userFamily = input("How many people are in your household: ")

cur1.execute("INSERT INTO UserData VALUES (?, ?, ?)", [userEmail, userPassword, userFamily])

con1.commit()

#Display data in the table
for row in cur1.execute("SELECT email, password, family size FROM UserData"):
    print(row)


def checkForNotifications():
    #Take the Average expiration date from each item and adds it to a table
    name = "Strawberries"
    days = cur2.execute("SELECT Avg days FROM Produce WHERE Name = ?", [name])
    expirationDate = cur1.execute('SELECT DATE("now", + ?)', [days])

    cur1.execute("CREATE TABLE IF NOT EXISTS ExpirationDate (name, date)")
    cur1.execute("INSERT INTO ExpirationDate (?, ?)", [name, expirationDate])

    #Selects the oldest expiration date
    cur1.execute("SELECT FROM ExpirationDate WHERE expirationDate > (SELECT MIN(expirationDate) from ExpirationDate)")
    newNotification = cur1.fetchall

    #Sending email notifications
    if newNotification:
    
        port = 465
        smtp_server = "smtp.gmail.com"
        sender_email = ""
        receiver_email = userEmail
        password = input
        message = """\
            Subject: Your produce is about to expire

            Hello,

            You have items that are about to expire. Please check Virtual Pantry for more information. 

        """

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)

    else:
        print("No new notifications")

while True:
    checkForNotifications()
    time.sleep(5)

con1.close()
con2.close()
