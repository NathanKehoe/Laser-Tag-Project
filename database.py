import psycopg2

class PlayerDatabase:
    def __init__(self, db_name="photon", db_user="grparish@uark.edu", db_password="password", db_host="localhost", db_port="5432"):
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.db_port = db_port

    # Connect to PostgreSQL database
    def connect(self):
        try:
            return psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port
            )
        except psycopg2.Error as e:
            print(f"Error connecting to database: {e}")
            return None

    # Check if a player exists by ID
    def check_for_player(self, player_id):
        conn = self.connect()
        if conn is None:
            return False
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT codename FROM players WHERE id = %s;", (player_id,))
                result = cursor.fetchone()
                return result[0] if result else False  # Return the codename if found
        except psycopg2.Error as e:
            print(f"Error querying the database: {e}")
            return False
        finally:
            conn.close()

    # Add a new player to the database
    def add_player(self, player_id, codename):
        conn = self.connect()
        if conn is None:
            return False
        try:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO players (id, codename) VALUES (%s, %s);", (player_id, codename))
            conn.commit()
            return True  # Player added successfully
        except psycopg2.Error as e:
            print(f"Error inserting into the database: {e}")
            return False
        finally:
            conn.close()

    # Remove a player from the database
    def remove_player(self, player_id):
        conn = self.connect()
        if conn is None:
            return False
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM players WHERE id = %s;", (player_id,))
            conn.commit()
            return True  # Player removed successfully
        except psycopg2.Error as e:
            print(f"Error deleting from the database: {e}")
            return False
        finally:
            conn.close()
