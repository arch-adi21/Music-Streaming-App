# Music-Streaming-App

## Access the website here :- 
[Click to use the app](https://music-streaming-app-q9jm.onrender.com/loghome)

## Overview of the application :- 
TI developed a music streaming web-application using flask application
framework for a dynamic experience to the users. This application has all the basic
functionalities required to make this a scalable project. I have provided classifications
among users like Creator , Non-Creator , Admin , and provided features like , MP3 song
upload , Playlist that could work as album , ratings , statistical data and many more.
Basic CRUD features for songs and playlists are embedded in the application. Data
Validation and Schema relations are taken care of in the application.

![image](https://github.com/arch-adi21/Music-Streaming-App/assets/155255348/3e94ec2c-ca19-44fe-80c9-4c5932485417)
![image](https://github.com/arch-adi21/Music-Streaming-App/assets/155255348/59eca961-2167-4f81-aebc-7937dfaf7354)


## Tech Stacks Used :

* Flask
    * Flask, render_template, request, redirect, session, flash, url_for
* Flask-sqlalchemy, sqlalchemy
    * SQLAlchemy, IntegrityError, or_
* Matplotlib, Seaborn, io, base64, PIL
* HTML (Hypertext Markup Language)
* CSS (Cascading Style Sheets)
* Bootstrap
* SQLite database structure

## System Design:

`app.py` is the main file containing the application initialization and all relevant routes. It also includes the code for the database schema.

* **Flask framework:** Used for building the application
* **SQLite structure:** Used for the database
* **templates folder:** Contains all the HTML files
* **CSS:** I haven't created a separate file for CSS. Internal or inline CSS is used throughout the project. Basic Bootstrap's `min.css` is used for button and card styling.
* **static folder:** Contains MP3 and image files uploaded by users. The content in this folder keeps updating based on user uploads.
* **Instances folder:** Contains the schema's ER diagram and the database itself.
* **Default folders:**
    * `__pycache__` stores bytecode for faster execution (can be deleted as needed)
    * `.vscode` contains personal settings for VS Code (can be deleted to use default settings)


## Demo Video :-

[Click to view the video](https://drive.google.com/file/d/1Yakv4tKhH9TDuW-bReELpGBQV_gX1WB5/view?usp=sharing)
