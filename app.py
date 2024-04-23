from flask import Flask, render_template, request, redirect, session, flash, url_for
import os
from PIL import Image
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_ 
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64


app = Flask(__name__)
app.secret_key = 'adityadb1'

########## Configuration#########

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///appdb.sqlite3"
app.config['UPLOAD_FOLDER'] = 'static'
db = SQLAlchemy(app)
app.app_context().push()


class User(db.Model):
    __tablename__ = 'User'
    email = db.Column(db.Text, nullable=False, unique=True)
    UID = db.Column(db.Integer, nullable=False, unique=True, primary_key=True)
    Full_name = db.Column(db.Text, nullable=False)
    Role = db.Column(db.Text, nullable=False, default='Gen')
    password = db.Column(db.Text, nullable=False)
    is_flagged = db.Column(db.Boolean, nullable=False, default=False)
    
    Uplaylist = db.relationship('Playlist', cascade='all, delete-orphan', lazy=True)
    Usongs = db.relationship('Songs', cascade='all, delete-orphan', lazy=True)

class Songs(db.Model):
    __tablename__ = 'Songs'
    SID = db.Column(db.Integer, nullable=False, unique=True, primary_key=True)
    user_ID = db.Column(db.Integer, db.ForeignKey('User.UID'), nullable=False)
    S_name = db.Column(db.Text, nullable=False, unique=True)
    Lyrics = db.Column(db.Text, nullable=False)
    Genre = db.Column(db.Text, nullable=False)
    Artist = db.Column(db.Text, nullable=False)
    Total_Rating = db.Column(db.Integer, nullable=False, default=0)
    Num_Ratings = db.Column(db.Integer, nullable=False, default=0)
    Average_Rating = db.Column(db.Float, nullable=True)
    is_flagged = db.Column(db.Boolean, nullable=False, default=False)
    S_M = db.Column(db.String, nullable= False) #Location of MP3 file
    S_I = db.Column(db.String, nullable=False) #Location of image file
    
    Splaylists = db.relationship('Playlist', cascade='all, delete-orphan', lazy=True)
    Spratings = db.relationship('Rating', cascade='all, delete-orphan', lazy=True)
    
class Playlist(db.Model):
    __tablename__ = "Playlist"
    PID = db.Column(db.Integer , nullable=False, unique=True, primary_key=True)
    User_ID = db.Column(db.Integer , db.ForeignKey('User.UID'), nullable=False)
    P_name = db.Column(db.Text, nullable=False)
    SID = db.Column(db.Integer , db.ForeignKey('Songs.SID'))
    is_flagged = db.Column(db.Boolean, nullable=False, default=False)
    
class Rating(db.Model):
    __tablename__ = 'Rating'
    rating_id = db.Column(db.Integer, primary_key=True)
    user_ID = db.Column(db.Integer, db.ForeignKey('User.UID'), nullable=False)
    song_ID = db.Column(db.Integer, db.ForeignKey('Songs.SID'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    
    
# routing to home page
@app.route('/')
def home():
    return render_template('index.html')

# creating route for signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # creates an existing user instance which will be used to check the uniqueness of email id and password
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return "Registration failed. Email already exists."
        else:
            # collect remaining user data
            full_name = request.form.get('Full_name')
            role = request.form.get('Role')

            # create a new instance for new user to push in database
            n_user = User(email=email, Full_name=full_name,
                          password=password, Role=role)
            db.session.add(n_user)
            db.session.commit()
            flash("Account created successfully")
            return redirect('/login')
    else:
        return render_template("signup.html")

# creating route for login


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('pswd')

        # Check if a user with the provided email and password exists in the database
        user = User.query.filter_by(email=email, password=password).first()

        if user:
            if user.is_flagged:
                flash("This account is flagged. Please contact the administrator for assistance.")
                return redirect('/login')

            session['user_id'] = user.UID
            user_id = session['user_id']
            if user.Role == "Creator":
                return redirect('/loghome')
            elif user.Role == "Gen":
                return redirect('/loghome')
        else:
            flash("No such user found")
            return redirect('/login')

    return render_template("login.html")

@app.route('/loghome')
def loghome():
    if 'user_id' not in session:
        # If the user is not logged in, redirect to the login page
        return redirect('/login')
    
    # Fetch logged-in user's ID
    user_id = session['user_id']

    # Fetch user details
    user = User.query.filter_by(UID=user_id).first()

    if user.Role == "Creator":
        # If the user is a creator, fetch their playlists
        playlists = Playlist.query.all()
        songs = Songs.query.filter_by(is_flagged=False).all()
        psongs = Songs.query.filter_by(is_flagged=False).all()
        for playlist in playlists:
            playlist.songs = (
                db.session.query(Songs)
                .join(Playlist, (Songs.SID == Playlist.SID) & ~Songs.is_flagged)
                .filter(Playlist.PID == playlist.PID)
                .all()
            )
        return render_template("creatordab.html", playlists=playlists, user_name=user.Full_name , songs = songs , psongs=psongs)
    elif user.Role == "Gen":
        return redirect('/allsongs')
    else:
        return redirect('/login')  

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    # Fetch user details
    user = User.query.filter_by(UID=user_id).first()

    return render_template('user_profile.html', user=user)

@app.route('/songp')
def songp():
    return render_template('songp.html')


@app.route('/csong', methods=['GET', 'POST'])
def csong():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']

    # Fetch songs associated with the logged-in user
    user_songs = Songs.query.filter_by(user_ID=user_id).all()

    if request.method == 'POST':
        song_id = request.form.get('song_id')
        action = request.form.get('action')

        if action == 'update':
            # Redirect to the update route with the song ID
            return redirect(f'/updatesong/{song_id}')

        elif action == 'delete':
            # Delete the song from the database
            song_to_delete = Songs.query.get(song_id)
            db.session.delete(song_to_delete)
            db.session.commit()
            flash("Song deleted")
            return redirect('/csong')

        elif action == 'show':
            # show the song button from the database
            return redirect(f'/showsong/{song_id}')

    # Render the songedit.html page with the list of songs
    return render_template('songedit.html', songs=user_songs)


@app.route('/createsong', methods=['GET', 'POST'])
def createsong():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    user = User.query.filter_by(
            UID=user_id).first()
    if request.method == 'POST':
        # Process the form data to create a new song
        song_name = request.form.get('S_Name')
        artist_name = user.Full_name
        lyrics = request.form.get('Lyrics')
        genre = request.form.get('Genre')
        
        #Fetching the uploaded file
        song_file = request.files['song_file']
        image_file = request.files['image_file']

        # Check if the song with the same name and artist already exists
        existing_song = Songs.query.filter_by(
            user_ID=user_id, S_name=song_name, Artist=artist_name).first()

        if existing_song:
            flash(
                "Song creation failed. This song already exists in your collection.", category='error')
            session.modified = True
            return redirect('/csong')

        # Create a new song instance and add it to the database
        new_song = Songs(user_ID=user_id, S_name=song_name,
                         Artist=artist_name, Lyrics=lyrics, Genre=genre , S_M="Null" , S_I="Null" )
        try:
            db.session.add(new_song)
            db.session.commit()
            if song_file and image_file:
                # Securely save the files with the SID as their filenames
                sid = new_song.SID
                song_filename = f"{sid}_song.mp3"
                image_filename = f"{sid}_image.jpg"

                # Save the files to the static folder
                song_file.save(os.path.join(app.config['UPLOAD_FOLDER'], song_filename))
                image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
                
                # Open the uploaded image file
                img = Image.open(image_file)

                # Crop the image to a square ratio
                size = min(img.size)
                img_cropped = img.crop((0, 0, size, size))

                # Save the cropped image to the static folder
                img_cropped.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

                # Update the new_song instance with the file names
                new_song.S_M = song_filename
                new_song.S_I = image_filename

                db.session.commit()  # uploading the file name

            flash("Song uploaded successfully!")
            return redirect('/csong')
        except IntegrityError:
            db.session.rollback()
            flash("Song creation failed. This song already exists in your collection.")
            return redirect('/csong')
    return render_template('createsong.html')\



@app.route('/updatesong/<int:song_id>', methods=['GET', 'POST'])
def update_song(song_id):
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    song_to_update = Songs.query.get(song_id)

    # Check if the song exists and belongs to the logged-in user
    if song_to_update is None or song_to_update.user_ID != user_id:
        flash("Song not found or unauthorized access.")
        return redirect('/csong')

    if request.method == 'POST':
        # Update the song data based on the form input
        song_to_update.S_name = request.form.get('S_Name')
        song_to_update.A_Name = request.form.get('A_Name')
        song_to_update.Lyrics = request.form.get('Lyrics')
        song_to_update.Genre = request.form.get('Genre')
        
        try:
            db.session.commit()
            flash("Song updated!")
            return redirect('/csong')
        except IntegrityError:
            db.session.rollback()
            flash("Song update failed. This song already exists in your collection.")
            return redirect('/csong')
    return render_template('updatesong.html', song=song_to_update)

@app.route('/createplaylist', methods=['GET','POST'])
def createplaylist():
    if request.method == 'POST':
        playlist_name = request.form.get('P_Name')
        if 'user_id' not in session:
            flash("Please log in to create a playlist.")
            return redirect('/login')
        user_id = session['user_id']

        # Check if the playlist with the same name already exists for this user
        existing_playlist = Playlist.query.filter_by(User_ID=user_id, P_name=playlist_name).first()

        if existing_playlist:
            flash("Playlist creation failed. This playlist already exists.")
            return redirect('/csong')
        else:
            # Create a new playlist instance and add it to the database
            new_playlist = Playlist(User_ID=user_id, P_name=playlist_name)
            db.session.add(new_playlist)
            db.session.commit()
            flash("Playlist created successfully!")
            return redirect('/csong')

    return render_template('createplaylist.html')

@app.route('/createplaylistuser', methods=['GET','POST'])
def createplaylistuser():
    if request.method == 'POST':
        playlist_name = request.form.get('P_Name')
        if 'user_id' not in session:
            flash("Please log in to create a playlist.")
            return redirect('/login')
        user_id = session['user_id']
        existing_playlist = Playlist.query.filter_by(User_ID=user_id, P_name=playlist_name).first()

        if existing_playlist:
            flash("Playlist creation failed. This playlist already exists.")
            return render_template('playlistedituser.html')
        else:
            # Create a new playlist instance and add it to the database
            new_playlist = Playlist(User_ID=user_id, P_name=playlist_name)
            db.session.add(new_playlist)
            db.session.commit()
            flash("Playlist created successfully!")

        return redirect('/playlistedituser')

    return render_template('createplaylistuser.html')

@app.route('/addtoplaylist/<int:song_id>', methods=['POST'])
def add_to_playlist(song_id):
    if 'user_id' not in session:
        flash("Please log in to add a song to a playlist.")
        return redirect('/login')
    user_id = session['user_id']
    playlist_id = request.form.get('playlist_id')

    # Check if the playlist and song exist and belong to the logged-in user
    playlist = Playlist.query.filter_by(User_ID=user_id, PID=playlist_id).first()
    song = Songs.query.get(song_id)

    if not (playlist and song):
        flash("Invalid playlist or song.")
        return redirect(f'/showsong/{song_id}')

    # Check if the song is already in the playlist
    if playlist.SID is not None:
        # If there is already a song in the playlist, create a new entry for the new song
        new_playlist_entry = Playlist(User_ID=user_id, P_name=playlist.P_name, SID=song_id)
        db.session.add(new_playlist_entry)
        db.session.commit()
    else:
        # If there is no song in the playlist, update the existing playlist entry
        playlist.SID = song_id
        db.session.commit()

    flash("Song added to playlist successfully!")
    return redirect(f'/showsong/{song_id}')
    
@app.route('/playlistedit', methods=['GET', 'POST'])
def playlist_edit():
    # Ensure the user is logged in
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    playlists = Playlist.query.filter_by(User_ID=user_id).distinct(Playlist.PID).all()
    
    Dplaylists =  (
    db.session.query(Playlist.P_name, Playlist.PID, Playlist.is_flagged)
    .filter_by(User_ID=user_id)
    .distinct(Playlist.P_name)
    .all()
)

    # Check if there are no playlists
    if not playlists:
        flash("You don't have any playlists yet.")
        return render_template('playlistedit.html')

    # Add associated songs for each playlist
    for playlist in playlists:
        playlist.songs = Songs.query.join(Playlist).filter(Playlist.PID == playlist.PID).all()

    # Handle song or playlist deletion from playlist
    if request.method == 'POST':
        song_id_to_delete = request.form.get('song_id')
        playlist_id_to_delete = request.form.get('playlist_id')

        if song_id_to_delete:
            # Delete individual song from the playlist
            playlist_song_to_delete = Playlist.query.filter_by(User_ID=user_id, PID=playlist_id_to_delete, SID=song_id_to_delete).first()

            if playlist_song_to_delete:
                db.session.delete(playlist_song_to_delete)
                flash("Song deleted from the playlist.")
                db.session.commit()

        elif playlist_id_to_delete:
            # Delete the entire playlist
            playlist_to_delete = Playlist.query.filter_by(User_ID=user_id, PID=playlist_id_to_delete).first()

            if playlist_to_delete:
                db.session.delete(playlist_to_delete)
                flash("Playlist deleted successfully.")
                db.session.commit()

    # Fetch all playlists for the user after deletion
    playlists = Playlist.query.filter_by(User_ID=user_id).all()

    # Add associated songs for each playlist after deletion
    for playlist in playlists:
        playlist.songs = Songs.query.join(Playlist).filter(Playlist.PID == playlist.PID).all()

    return render_template('playlistedit.html', playlists=playlists , Dplaylists=Dplaylists)

@app.route('/playlistedituser', methods=['GET', 'POST'])
def playlist_edit_user():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']

    playlists = Playlist.query.filter_by(User_ID=user_id).all()

    # Check if there are no playlists
    if not playlists:
        flash("You don't have any playlists yet.")
        return render_template('playlistedituser.html')

    # Add associated songs for each playlist
    for playlist in playlists:
        playlist.songs = Songs.query.join(Playlist).filter(Playlist.PID == playlist.PID).all()

    # Handle song or playlist deletion from playlist
    if request.method == 'POST':
        song_id_to_delete = request.form.get('song_id')
        playlist_id_to_delete = request.form.get('playlist_id')

        if song_id_to_delete:
            # Delete individual song from the playlist
            playlist_song_to_delete = Playlist.query.filter_by(User_ID=user_id, PID=playlist_id_to_delete, SID=song_id_to_delete).first()

            if playlist_song_to_delete:
                db.session.delete(playlist_song_to_delete)
                flash("Song deleted from the playlist.")
                db.session.commit()

        elif playlist_id_to_delete:
            # Delete the entire playlist
            playlist_to_delete = Playlist.query.filter_by(User_ID=user_id, PID=playlist_id_to_delete).first()

            if playlist_to_delete:
                db.session.delete(playlist_to_delete)
                flash("Playlist deleted successfully.")
                db.session.commit()
                

    # Fetch all playlists for the user after deletion
    playlists = Playlist.query.filter_by(User_ID=user_id).all()

    # Add associated songs for each playlist after deletion
    for playlist in playlists:
        playlist.songs = Songs.query.join(Playlist).filter(Playlist.PID == playlist.PID).all()

    return render_template('playlistedituser.html', playlists=playlists)

@app.route('/showsong/<int:song_id>', methods=['GET','POST'])
def showsong(song_id):
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']

    # Fetch the song to display
    song_to_show = Songs.query.get(song_id)

    # Check if the song exists and belongs to the logged-in user
    if song_to_show is None :
        flash("Song not found or unauthorized access.")
        return redirect('/allsongs')
    user = User.query.filter_by(UID=user_id).first()
    user_name = user.Full_name 
    genre = song_to_show.Genre
    song_name = song_to_show.S_name
    Artist = song_to_show.Artist
    S_M = song_to_show.S_M
    S_I = song_to_show.S_I
    Lyrics = song_to_show.Lyrics
    Avg_Rat = song_to_show.Average_Rating
    user_playlists = [(playlist.PID, playlist.P_name) for playlist in Playlist.query.filter_by(User_ID=user_id).distinct(Playlist.P_name).all()]
    return render_template('songp.html', song=song_to_show , S_M = S_M , S_I = S_I ,user_name=user_name , genre=genre ,song_name=song_name , Lyrics = Lyrics, user_playlists=user_playlists , song_id=song_id , Avg_Rat=Avg_Rat , user_id=user_id , Artist=Artist)


@app.route('/allsongs', methods=['GET','POST'])
def all_songs():
    if 'user_id' not in session:
        return redirect('/login')
    
    user_id = session['user_id']
    user = User.query.filter_by(UID=user_id).first()
    playlists = Playlist.query.all()
    songs = Songs.query.filter_by(is_flagged=False).all()
    psongs = Songs.query.filter_by(is_flagged=False).all()
    for playlist in playlists:
        playlist.songs = Songs.query.join(Playlist).filter(Playlist.PID == playlist.PID).all()
    return render_template('userdab.html', playlists=playlists, user_name=user.Full_name , songs = songs , psongs=psongs)

@app.route('/upgrade_account', methods=['GET', 'POST'])
def upgrade_account():
    if 'user_id' not in session:
        return redirect('/login')
    user_id = session['user_id']
    user = User.query.filter_by(UID=user_id).first()

    if request.method == 'POST':
        user.Role = 'Creator'
        db.session.commit()

        flash("Account upgraded successfully! You are now a Creator.")
        return redirect('/loghome')

    return render_template('upgrade_account.html')  

@app.route('/decline_upgrade')
def decline_upgrade():
    flash("Account upgrade declined. Your role remains unchanged.")
    return redirect('/loghome') 

@app.route('/rate_song/<int:song_id>', methods=['POST'])
def rate_song(song_id):
    if 'user_id' not in session:
        flash("Please log in to rate songs.")
        return redirect('/login')
    user_id = session['user_id']

    # Fetch the song to rate
    song = Songs.query.get(song_id)

    if song is None:
        flash("Song not found.")
        return redirect('/allsongs')

    # Check if the user has already rated the song
    existing_rating = Rating.query.filter_by(user_ID=user_id, song_ID=song_id).first()

    if existing_rating:
        flash("You have already rated this song.")
        return redirect(f'/showsong/{song_id}')

    # Get the rating from the form submission
    rating = int(request.form.get('rating'))

    # Record the user's rating in the Rating table
    new_rating = Rating(user_ID=user_id, song_ID=song_id, rating=rating)
    db.session.add(new_rating)
    db.session.commit()

    # Update the song's total rating and number of ratings
    song.Total_Rating += rating
    song.Num_Ratings += 1
    db.session.commit()

    # Calculate the average rating
    song.Average_Rating = song.Total_Rating / song.Num_Ratings
    db.session.commit()

    flash("Song rated successfully!")
    return redirect(f'/showsong/{song_id}')

@app.route('/user_statistics')
def user_statistics():
    user_id = session.get('user_id')
    user = User.query.filter_by(UID=user_id).first()

    # Get user-specific statistics
    total_uploaded_songs = Songs.query.filter_by(user_ID=user_id).count()
    total_created_playlists = Playlist.query.filter_by(User_ID=user_id).count()
    
    # Get top 5 songs with the best user rating
    top_songs = Songs.query.order_by(Songs.Average_Rating.desc()).limit(5).all()

    # Create a bar plot for top 5 songs
    plt.figure(figsize=(10, 6))
    sns.barplot(x=[song.S_name for song in top_songs], y=[song.Average_Rating for song in top_songs])
    plt.title('Top 5 Songs with Best User Rating')
    plt.xlabel('Song Name')
    plt.ylabel('Average Rating')
    
    # Save the plot to a BytesIO object
    img_stream = io.BytesIO()
    plt.savefig(img_stream, format='png')
    img_stream.seek(0)
    
    # Convert the plot to base64 for embedding in HTML
    plot_img = base64.b64encode(img_stream.getvalue()).decode('utf-8')
    img_stream.close()

    # Render the HTML template with the collected data
    return render_template('user_statistics.html',
                           user=user,
                           total_uploaded_songs=total_uploaded_songs,
                           total_created_playlists=total_created_playlists,
                           top_songs=top_songs,
                           plot_img=plot_img)
    
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        # Get the search query from the form submission
        search_query = request.form.get('search_query')

        # Perform a case-insensitive search across multiple fields in the database
        search_results = Songs.query.with_entities(
    Songs.SID, Songs.S_name, Songs.Artist, Songs.Genre, Playlist.P_name
).filter(
    or_(
        Songs.S_name.ilike(f"%{search_query}%"),
        Songs.Artist.ilike(f"%{search_query}%"),
        Songs.Genre.ilike(f"%{search_query}%"),
        Playlist.P_name.ilike(f"%{search_query}%"),
    )
).join(Playlist, Playlist.SID == Songs.SID).all()

        return render_template('search_results.html', search_results=search_results, query=search_query)

    return render_template('search.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('pswd')

        # Check if the provided credentials match the default admin credentials
        if email == "admin1@gmail.com" and password == "admin1111":
            # Redirect to the admin page or perform admin-related actions
            return redirect('/admin_page')

        # If credentials do not match, show an error message
        flash("Invalid admin credentials. Please try again.", 'error')

    return render_template('admin_login.html')  

@app.route('/admin_page')
def admin_page():
    # Query database to get Creator Users
    creator_users = User.query.filter_by(Role='Creator').all()

    # Calculate total number of unique songs and playlists for Creator Users
    for user in creator_users:
        user.total_songs_uploaded = Songs.query.filter_by(user_ID=user.UID).count()
        user.total_playlists_created = Playlist.query.filter_by(User_ID=user.UID).count()

    # Query database to get Gen Users
    gen_users = User.query.filter_by(Role='Gen').all()

    # Calculate total number of unique playlists for Gen Users
    for user in gen_users:
        user.total_playlists_created = Playlist.query.filter_by(User_ID=user.UID).count()

    return render_template('admin_page.html', creator_users=creator_users, gen_users=gen_users)

@app.route('/flag_user/<int:user_id>', methods=['POST'])
def flag_user(user_id):
    # Ensure the user is flagged or unflagged based on the current status
    user = User.query.get(user_id)

    if user:
        user.is_flagged = not user.is_flagged
        db.session.commit()

    return redirect('/admin_page') 

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get(user_id)

    if user:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted successfully!")

    return redirect('/admin_page') 

@app.route('/creator_details/<int:user_id>')
def creator_details(user_id):

    # Fetch the Creator user details
    creator_user = User.query.filter_by(UID=user_id).first()

    if not creator_user:
        flash("Creator user not found.")
        return redirect('/loghome')

    # Fetch the songs and playlists associated with the Creator user
    creator_songs = Songs.query.filter_by(user_ID=user_id).all()
    creator_playlists = Playlist.query.filter_by(User_ID=user_id).all()

    # Add associated songs for each playlist
    for playlist in creator_playlists:
        playlist.songs = Songs.query.join(Playlist).filter(Playlist.PID == playlist.PID).all()

    return render_template('creator_details.html', user=creator_user, songs=creator_songs, playlists=creator_playlists)

@app.route('/flag_song/<int:user_id>/<int:song_id>', methods=['POST'])
def flag_song(user_id, song_id):
    # Fetch the song to flag
    song = Songs.query.get(song_id)
    user_id=user_id

    if song:
        song.is_flagged = True
        db.session.commit()

    return redirect(f'/creator_details/{user_id}')

@app.route('/unflag_song/<int:user_id>/<int:song_id>', methods=['POST'])
def unflag_song(user_id, song_id):
    # Fetch the song to unflag
    song = Songs.query.get(song_id)
    user_id=user_id

    if song:
        song.is_flagged = False
        db.session.commit()

    return redirect(f'/creator_details/{user_id}')

@app.route('/delete_song/<int:user_id>/<int:song_id>', methods=['POST'])
def delete_song(user_id, song_id):
    # Fetch the song to delete
    song = Songs.query.get(song_id)
    user_id = user_id

    if song:
        db.session.delete(song)
        db.session.commit()

    return redirect(f'/creator_details/{user_id}')

@app.route('/flag_playlist/<int:user_id>/<int:playlist_id>', methods=['POST'])
def flag_playlist(user_id, playlist_id):
    # Fetch the playlist to flag
    playlist = Playlist.query.get(playlist_id)
    user_id = user_id

    if playlist:
        playlist.is_flagged = True
        db.session.commit()

    return redirect(f'/creator_details/{user_id}')

@app.route('/unflag_playlist/<int:user_id>/<int:playlist_id>', methods=['POST'])
def unflag_playlist(user_id, playlist_id):
    # Fetch the playlist to unflag
    playlist = Playlist.query.get(playlist_id)
    user_id = user_id

    if playlist:
        playlist.is_flagged = False
        db.session.commit()

    return redirect(f'/creator_details/{user_id}')

@app.route('/delete_playlist/<int:user_id>/<int:playlist_id>', methods=['POST'])
def delete_playlist(user_id, playlist_id):
    # Fetch the playlist to delete
    playlist = Playlist.query.get(playlist_id)
    user_id = user_id

    if playlist:
        db.session.delete(playlist)
        db.session.commit()

    return redirect(f'/creator_details/{user_id}')

@app.route('/admin_stats')
def admin_stats():
    # Fetch the required statistics from the database
    users_most_ratings = (
        User.query
        .join(Songs)
        .group_by(User.UID)
        .all()
    )

    # Get users with most flagged songs
    users_most_flagged_songs = (
        User.query
        .join(Songs)
        .filter(Songs.is_flagged == True)
        .group_by(User.UID)
        .all()
    )

    # Calculate counts for the bar plots
    ratings_counts = [db.session.query(db.func.count(Songs.SID)).filter(Songs.user_ID == user.UID).scalar() for user in users_most_ratings]
    flagged_songs_counts = [db.session.query(db.func.count(Songs.SID)).filter(Songs.user_ID == user.UID, Songs.is_flagged == True).scalar() for user in users_most_flagged_songs]

    # Total number of flagged user, song, and playlist
    total_flagged_users = User.query.filter(User.is_flagged == True).count()
    total_flagged_songs = Songs.query.filter(Songs.is_flagged == True).count()
    # Assuming you have a Playlist model
    total_flagged_playlists = Playlist.query.filter(Playlist.is_flagged == True).count()

    # Top-performing songs among all users
    top_performing_songs = (
        Songs.query
        .order_by(Songs.Average_Rating.desc())
        .limit(10)
        .all()
    )

    # Create plots
    plt.figure(figsize=(12, 6))

    # Plot Users with Most Ratings
    plt.subplot(2, 3, 1)
    sns.barplot(x=[user.Full_name for user in users_most_ratings], y=ratings_counts)
    plt.title('Users with Most Ratings')
    plt.xlabel('User')
    plt.ylabel('Total Ratings')

    # Plot Users with Most Flagged Songs
    plt.subplot(2, 3, 2)
    sns.barplot(x=[user.Full_name for user in users_most_flagged_songs], y=flagged_songs_counts)
    plt.title('Users with Most Flagged Songs')
    plt.xlabel('User')
    plt.ylabel('Flagged Songs')

    # Plot Total Flagged Users, Songs, and Playlists
    plt.subplot(2, 3, 3)
    sns.barplot(x=['Users', 'Songs', 'Playlists'], y=[total_flagged_users, total_flagged_songs, total_flagged_playlists])
    plt.title('Total Flagged Users, Songs, and Playlists')
    plt.xlabel('Entity')
    plt.ylabel('Count')

    # Plot Top Performing Songs
    plt.subplot(2, 3, 4)
    sns.barplot(x=[song.S_name for song in top_performing_songs], y=[song.Average_Rating for song in top_performing_songs])
    plt.title('Top Performing Songs')
    plt.xlabel('Song')
    plt.ylabel('Average Rating')

    # Save the plot to a BytesIO object
    img_stream = io.BytesIO()
    plt.tight_layout()
    plt.savefig(img_stream, format='png')
    img_stream.seek(0)

    # Convert the plot to base64 for embedding in HTML
    plot_img = base64.b64encode(img_stream.getvalue()).decode('utf-8')
    img_stream.close()

    return render_template('stats.html', plot_img=plot_img, users_with_most_ratings=users_most_ratings,
                           users_with_most_flagged_songs=users_most_flagged_songs,
                           total_flagged_users=total_flagged_users,
                           total_flagged_songs=total_flagged_songs,
                           total_flagged_playlists=total_flagged_playlists,
                           top_performing_songs=top_performing_songs, ratings_counts=ratings_counts,
                           flagged_songs_counts=flagged_songs_counts)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
