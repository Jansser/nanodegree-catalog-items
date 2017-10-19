# Catalog Items Project
A project to Full Stack Web Developer Nanodegree program. A web application that provides a list of items within a variety of categories and integrate third party user registration and authentication. Authenticated users should have the ability to post, edit, and delete their own items.

### Installation

The project requires [Python](https://www.python.org/downloads/) 3, flask, sqlalchemy, flask_uploads and the libaries below.

```pip install flask```

```pip install sql-alchemy```

```pip install httplib2```

```pip install requests```

```pip install flask-sqlalchemy```

```pip install oauth2client```

```pip install flask_uploads```

### How to run

* Download the repository or clone ```git clone https://github.com/Jansser/nanodegree-catalog-items.git```
* Change to the app directory by typing **cd nanodegree-catalog-items**.
* Now type **python database.py** to initialize the database.
* Type **python load_data.py** to populate the database with categories and items.
* Type **python app.py** to run the Flask web server. In your browser visit **http://localhost:8000** to view the catalog app.