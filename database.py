import psycopg2

DB_NAME = "photon"
DB_USER = "holderUser"  
DB_PASSWORD = "holderPass"  
DB_HOST = "localhost" 
DB_PORT = "5432"  

# Connect to PostgreSQL database
def connect():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        return None

# Check if a player exists by ID
def check_for_player(player_id):
    conn = connect()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT codename FROM players WHERE id = %s;", (player_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        if result:
            return result[0]  # Return the codename if found
        else:
            return False  # Return False if not found
    except psycopg2.Error as e:
        print(f"Error querying the database: {e}")
        return False

# Add a new player to the database
def add_player(player_id, codename):
    conn = connect()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO players (id, codename) VALUES (%s, %s);", (player_id, codename))
        conn.commit()
        cursor.close()
        conn.close()
        return True  # Player added successfully
    except psycopg2.Error as e:
        print(f"Error inserting into the database: {e}")
        return False

# Remove a player from the database
def remove_player(player_id):
    conn = connect()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM players WHERE id = %s;", (player_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True  # Player removed successfully
    except psycopg2.Error as e:
        print(f"Error deleting from the database: {e}")
        return False