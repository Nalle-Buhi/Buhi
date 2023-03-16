# This file has all the jobs and items in a python list so i can easily add them to the database

""" 
    The items table is the following:   
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    name VARCHAR(50),
    price FLOAT,
    description TEXT,
    image_url VARCHAR(255),
    enabled BIT
    
    And the jobs table is the following:
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    name TEXT,
    payout INTEGER,
    enabled INTEGER

    Job lists are in the following format where the first value being the job name, second being payout and the last value is enabled/disabled:
    jobs = [
        [1, "job1", 123, 1],
        [2, "job2", 321, 0]
    ]

    Item list goes like this manual id:n because autoincrementing may get scuffed:
    items = [
    [1, "item1", 123, "description", "image_url", 1/0,],
    [2, "item2", 321, "description", "image_url", 1/0,]

    ]
    """


jobs = [
    [1, "Kaivostyöntekijä", "Louhi mineraaleja buhistanin kaivoksilla", 3300, 1],
    [2, "Rekkakuski", "Vie norttia ja megistä kauppaan", 3415, 1],
]

items = [
    [
        1,
        "Nortti aski",
        10,
        "Maukkaan North State tupakan avulla saat vähennettyä työ stresi huolia",
        " ",
        1,
    ],
    [
        2,
        "MegaForce Energy Drink",
        1.10,
        "Raikas ja ravitseva. Tämä antaa sinulle vireyttä lisää",
        " ",
        1,
    ],
]
