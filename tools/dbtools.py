import sqlite3
import datetime
import db.itemjob

create_db_query = [
    """CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    discord_id VARCHAR(20) UNIQUE,
    wallet_balance FLOAT,
    bank_balance FLOAT,
    job_id INTEGER REFERENCES jobs(id)

);""",
    """CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    user_id INT,
    transaction_type VARCHAR(10),
    sign VARCHAR(1),
    amount FLOAT,
    timestamp DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(id)
);""",
    """CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    name VARCHAR(50),
    price FLOAT,
    description TEXT,
    image_url VARCHAR(255),
    enabled BIT
);""",
    """CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY NOT NULL,
    user_id INT,
    item_id INT,
    quantity INT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (item_id) REFERENCES items(id)
);""",
    """CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY NOT NULL,
    name TEXT,
    description TEXT,
    payout INTEGER,
    enabled INTEGER
);""",
]


class SQLite:
    def __init__(self, db_file):
        self.db_file = db_file
        self.connection = None

    def __enter__(self):
        self.connection = sqlite3.connect(self.db_file)
        return self.connection.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            self.connection.commit()
            self.connection.close()
            self.connection = None


# Startup stuff


async def create_tables():
    with SQLite("./db/economy.db") as cur:
        try:
            for query in create_db_query:
                cur.execute(query)
        except Exception as err:
            print(err)


async def startup_add_jobs():
    for i in db.itemjob.jobs:
        await add_job(i[0], i[1], i[2], i[3], i[4])


async def startup_add_items():
    for i in db.itemjob.items:
        try:
            await add_item(i[0], i[1], i[2], i[3], i[4], i[5])
        except Exception as err:
            print(err)


# Command related stuff


async def log_transaction(user_id, amount, transaction_type, sign):
    """Log transactions, currently known and utilized transaction types are, transfer, deposit, withdraw, cash, card and paycheck. Make sure to add + or - depending on the transaction type"""
    timestamp = datetime.datetime.now()
    with SQLite("./db/economy.db") as cur:
        cur.execute(
            "INSERT INTO transactions (user_id, amount, transaction_type, sign, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, transaction_type, sign, timestamp),
        )


async def balance(user_id):
    """Return the values for wallet_balance and bank_balance in this order"""
    with SQLite("./db/economy.db") as cursor:
        cursor.execute("SELECT * FROM users WHERE discord_id = ?", (user_id,))
        row = cursor.fetchone()
        if row is None:
            cursor.execute(
                "INSERT INTO users (discord_id, wallet_balance, bank_balance) VALUES (?, ?, ?)",
                (user_id, 50.0, 0.0),
            )
            print("User added to database")

        wallet_balance = row[2]
        bank_balance = row[3]
        return wallet_balance, bank_balance


async def deposit(user_id, amount_to_transfer):
    with SQLite("./db/economy.db") as cursor:
        cursor.execute(
            "SELECT wallet_balance, bank_balance FROM users WHERE discord_id = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        wallet_balance = row[0]
        bank_balance = row[1]

        # Check if the user has enough funds in their wallet
        if wallet_balance < amount_to_transfer or amount_to_transfer <= 0:
            wallet_balance, bank_balance = await balance(user_id)
            raise ValueError(
                f"Ei tarpeeksi käteistä, sinulla on {wallet_balance}€ käteistä."
            )

        # Update the user's wallet and bank balances
        new_wallet_balance = wallet_balance - amount_to_transfer
        new_bank_balance = bank_balance + amount_to_transfer

        await update_balance(user_id, new_wallet_balance, new_bank_balance)
        await log_transaction(user_id, amount_to_transfer, "deposit", "+")


async def withdraw(user_id, amount_to_transfer):
    with SQLite("./db/economy.db") as cursor:
        cursor.execute(
            "SELECT wallet_balance, bank_balance FROM users WHERE discord_id = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        wallet_balance = row[0]
        bank_balance = row[1]

        # Check if the user has enough funds in their wallet
        if bank_balance < amount_to_transfer or amount_to_transfer <= 0:
            # Roll back the transaction and raise an error
            wallet_balance, bank_balance = await balance(user_id)
            raise ValueError(
                f"Ei tarpeeksi rahaa pankissa, sinulla on {bank_balance}€."
            )

        # Update the user's wallet and bank balances and log the transaction
        new_wallet_balance = wallet_balance + amount_to_transfer
        new_bank_balance = bank_balance - amount_to_transfer

        await update_balance(user_id, new_wallet_balance, new_bank_balance)
        await log_transaction(user_id, amount_to_transfer, "withdraw", "-")


async def transfer(user_id, amount_to_transfer, payee_id):
    if user_id == payee_id:
        raise ValueError("Et voi siirtää itsellesi rahaa hölömö")
    with SQLite("./db/economy.db") as cursor:
        # Check if the payee has and account and get their balances
        try:
            cursor.execute(
                "SELECT wallet_balance, bank_balance FROM users WHERE discord_id = ?",
                (payee_id,),
            )
            row = cursor.fetchone()
            payee_wallet_balance = row[0]
            payee_bank_balance = row[1]
        except Exception as err:
            raise ValueError(
                "Käyttäjällä jolle yrität siirtää rahaa ei ole pankkitiliä, kehota heitä tekemään tili"
            )

        cursor.execute(
            "SELECT wallet_balance, bank_balance FROM users WHERE discord_id = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        wallet_balance = row[0]
        bank_balance = row[1]

        # Check if the user has enough funds in their wallet
        if bank_balance < amount_to_transfer or amount_to_transfer <= 0:
            # Roll back the transaction and raise an error
            raise ValueError(
                f"Ei tarpeeksi rahaa pankissa, sinulla on {bank_balance}€."
            )

        # Update the user's wallet and bank balances and log the transaction
        new_bank_balance = bank_balance - amount_to_transfer

        await update_balance(user_id, wallet_balance, new_bank_balance)
        await log_transaction(user_id, amount_to_transfer, "transfer", "-")

        payee_new_bank_balance = payee_bank_balance + amount_to_transfer
        await update_balance(payee_id, payee_wallet_balance, payee_new_bank_balance)
        await log_transaction(payee_id, amount_to_transfer, "transfer", "-")


async def update_balance(user_id, wallet_balance, bank_balance):
    with SQLite("./db/economy.db") as cursor:
        cursor.execute("BEGIN")

        cursor.execute(
            "UPDATE users SET wallet_balance = ?, bank_balance = ? WHERE discord_id = ?",
            (wallet_balance, bank_balance, user_id),
        )

        cursor.execute("COMMIT")


async def get_transactions(user_id, transaction_type):
    with SQLite("./db/economy.db") as cursor:
        try:
            if transaction_type == "all":
                cursor.execute(
                    """SELECT * FROM transactions
                    WHERE user_id = ?""",
                    (user_id,),
                )
            else:
                cursor.execute(
                    """SELECT * FROM transactions
                    WHERE user_id = ? AND transaction_type = ?""",
                    (user_id, transaction_type),
                )
            row = cursor.fetchall()
            return row
        except Exception as err:
            print(err)


async def get_user_job(user_id):
    with SQLite("./db/economy.db") as cursor:
        cursor.execute("SELECT job_id FROM users WHERE discord_id = ?", (user_id,))
        user_job = cursor.fetchone()
        return user_job


async def get_available_jobs():
    with SQLite("./db/economy.db") as cursor:
        try:
            cursor.execute("SELECT * FROM jobs WHERE enabled = ?", (1,))
            row = cursor.fetchall()
            return row
        except Exception as err:
            print(err)


async def update_user_job(user_id, job_id):
    with SQLite("./db/economy.db") as cursor:
        try:
            cursor.execute(
                "UPDATE users SET job_id = ? WHERE discord_id = ?", (job_id, user_id)
            )
        except Exception as err:
            print(err)

async def get_single_item(item_id):
    with SQLite("./db/economy.db") as cursor:
        cursor.execute("SELECT * FROM items WHERE enabled = ? AND id = ?;", (1, item_id))
        items = cursor.fetchone()
        return items

async def get_available_items():
    with SQLite("./db/economy.db") as cursor:
        cursor.execute("SELECT * FROM items WHERE enabled = ?;", (1,))
        items = cursor.fetchall()
        return items
    
async def update_user_inventory(user_id, item_id, quantity):
    with SQLite("./db/economy.db") as cursor:
        cursor.execute("SELECT quantity FROM inventory WHERE user_id = ? AND item_id = ?", (user_id, item_id))
        result = cursor.fetchone()
        if result is None:        
            cursor.execute("INSERT INTO inventory (user_id, item_id, quantity) VALUES (?, ?, ?)", (user_id, item_id, quantity))
        else:
            cursor.execute("UPDATE inventory SET quantity = ? WHERE user_id = ? AND item_id = ?", ((result[0] + quantity), user_id, item_id))

async def shop_transaction(user_id, item_id, quantity):
    try:
        item_data = await get_single_item(item_id)
        if item_data == None:
            raise ValueError("Itemiä ei ole olemassa")
        wallet_balance, bank_balance = await balance(user_id)
        total_price = (item_data[2]*quantity)
        if total_price > bank_balance or quantity <= 0:
            raise ValueError("Ei tarpeeksi rahaa ostaa kyseisiä tavaroita")  
        else:
            # Do the necessary transactions
            await update_balance(user_id, wallet_balance, (bank_balance - total_price))
            await log_transaction(user_id, total_price, "card", "-")
            await update_user_inventory(user_id, item_id, quantity)
            return total_price, item_data[1]
            
            

    except Exception as err:
        print(err)

async def add_job(id, name, description, payout, enabled):
    with SQLite("./db/economy.db") as cursor:
        cursor.execute(
            """INSERT OR REPLACE INTO jobs (id,name,description,payout,enabled) VALUES (?, ?, ?, ?, ?);""",
            (id, name, description, payout, enabled),
        )
        print(
            f"Added or Replaced a job into the database with the following values {id}, {name}, {payout}, {enabled} \n"
        )


async def add_item(id, name, price, description, image_url, enabled):
    with SQLite("./db/economy.db") as cursor:
        cursor.execute(
            """INSERT OR REPLACE INTO items (id, name, price, description, image_url, enabled) VALUES (?, ?, ?, ?, ?, ?)""",
            (id, name, price, description, image_url, enabled),
        )
        print(
            f"Added or Replaced an item into the database with the following values {id}, {name}, {price}, {description}, {image_url}, {enabled}, \n"
        )
