
prompt = """
You need to act as a policy model, that given a question and a modular set, determines the sequence of modules that can be executed sequentially can solve the question.

The modules are defined as follows:

- Query_Generator: This module generates a search engine query for the given question. Normally, we consider using "Query_Generator" when the question involves domain-specific knowledge.

- Bing_Search: This module searches the web for relevant information to the question. Normally, we consider using "Bing_Search" when the question involves domain-specific knowledge.

- Image_Captioner: This module generates a caption for the given image. Normally, we consider using "Image_Captioner" when the question involves the semantic understanding of the image, and the "has_image" field in the metadata is True.

- Text_Detector: This module detects the text in the given image. Normally, we consider using "Text_Detector" when the question involves the unfolding of the text in the image, e.g., diagram, chart, table, map, etc., and the "has_image" field in the metadata is True.

- Program_Generator: This module generats a python program that can solve the given question. It takes in the question and possible context and produces a program that can be executed by the "Program_Executor" module. Normally, we consider using "Program_Generator" when the questions and contexts involve complex computation, such as arithmetic operations over multiple numbers, or when the questions involve complex logical operations, such as "if-else" statements.

- Program_Verifier: This module verifies whether the generated program from "Program_Generator" is valid and error-free. It checks for syntax errors, logical errors, and other potential issues that may arise during program execution.

- Program_Executor: This module executes the generated program from "Program_Generator" and produces an output that can be further processed by other modules, such as "Question_Answering". 

- Row_Lookup: This module returns the simplified table that only remains the rows that are relevant to the question. It takes in the question and a table and returns the simplified table. If all rows are relevant or there are only three rows or less, return the original table. Normally, we only consider using "Row_Lookup" when the table involves more than three rows and the question only requires a small number of rows to answer the question.

- Column_Lookup: This module returns the simplified table that only remains the columns that are relevant to the question. It takes in the question and a table and returns the simplified table. If all columns are relevant or there are only two columns, return the original table. Normally, we consider using "Column_Lookup" when the table involves more than two columns and the question only requires a small number of columns to answer the question. 

- Table_Verbalizer: This module converts the table to a description that can be easily understood by the downstream modules, like "Program_Generator", "Solution_Generator", "Question_Answering". Normally, we consider using "Table_Verbalizer" when the table involves a small number of rows and columns and the table is domain-specific, such as steam-and-leaf plots, function tables, etc.

- Knowledge_Retrieval: This module retrieves background knowledge as the hint for the given question. Normally, we consider using "Knowledge_Retrieval" when the background knowledge is helpful to guide the solution.

- Solution_Generator: This module generates a detailed solution to the question based on the information provided. Normally, "Solution_Generator" will incorporate the information from "Query_Generator", "Bing_Search", "Image_Captioner", "Text_Detector", and "Knowledge_Retrieval".

- Answer_Generator: This module extracts final answer in a short form from the solution or execution result. This module normally is the last module in the prediction pipeline.

Below are some examples that map the problem to the modules.

Question: Compare the average kinetic energies of the particles in each sample. Which sample has the higher temperature?

Context: The diagrams below show two pure samples of gas in identical closed, rigid containers. Each colored ball represents one gas particle. Both samples have the same number of particles. 

Options: (A) neither; the samples have the same temperature (B) sample A (C) sample B

Metadata: {'pid': 19, 'has_image': True, 'grade': 8, 'subject': 'natural science', 'topic': 'physics', 'category': 'Particle motion and energy', 'skill': 'Identify how particle motion affects temperature and pressure'}

Modules: ["Text_Detector", "Knowledge_Retrieval", "Solution_Generator", "Answer_Generator"]

Question: Which property do these three objects have in common? 

Options: (A) hard (B) soft (C) yellow

Metadata: {'pid': 43, 'has_image': True, 'grade': 4, 'subject': 'natural science', 'topic': 'physics', 'category': 'Materials', 'skill': 'Compare properties of objects'} 

Modules: ["Text_Detector", "Knowledge_Retrieval", "Solution_Generator", "Answer_Generator"]

Question: Which better describes the Shenandoah National Park ecosystem?

Context: Figure: Shenandoah National Park.\nShenandoah National Park is a temperate deciduous forest ecosystem in northern Virginia.

Options: (A) It has warm, wet summers. It also has only a few types of trees. (B) It has cold, wet winters. It also has soil that is poor in nutrients.

Metadata: {'pid': 246, 'has_image': True, 'grade': 3, 'subject': 'natural science', 'topic': 'biology', 'category': 'Ecosystems', 'skill': 'Describe ecosystems'}

Modules: ["Query_Generator", "Bing_Search", "Solution_Generator", "Answer_Generator"]

Question: Think about the magnetic force between the magnets in each pair. Which of the following statements is true?

Context: The images below show two pairs of magnets. The magnets in different pairs do not affect each other. All the magnets shown are made of the same material, but some of them are different shapes.  

Metadata: {'has_image': True, 'grade': 6, 'subject': 'natural science', 'topic': 'physics', 'category': 'Velocity, acceleration, and forces', 'skill': 'Compare magnitudes of magnetic forces'} 

Options: (A) The magnitude of the magnetic force is greater in Pair 1. (B) The magnitude of the magnetic force is greater in Pair 2. (C) The magnitude of the magnetic force is the same in both pairs.

Modules: ["Text_Detector", "Knowledge_Retrieval", "Solution_Generator", "Answer_Generator"]

Question: Which is in row C?

Options: (A) the diner (B) the grocery store (C) the library (D) the school

Metadata: {'pid': 375, 'has_image': True, 'grade': 3, 'subject': 'social science', 'topic': 'geography', 'category': 'Geography', 'skill': 'Use a letter-number grid'} 

Modules: ["Text_Detector", ≈"Solution_Generator", "Answer_Generator"]

Question: Which material is this screw driver made of?

Options: (A) cardboard (B) plastic

Metadata: {'pid': 264, 'has_image': True, 'grade': 2, 'subject': 'natural science', 'topic': 'physics', 'category': 'Materials', 'skill': 'Identify multiple materials in objects'} 

Modules: ["Image_Captioner", "Solution_Generator", "Answer_Generator"]

Question: How long is a garden snail?

Context: Select the best estimate.

Options: (A) 27 meters (B) 27 millimeters (C) 27 kilometers (D) 27 centimeters

Metadata: {'pid': '1351', 'has_image': False, 'grade': 6, 'subject': 'natural science', 'topic': 'units-and-measurement', 'category': 'Units and measurement', 'skill': 'Choose metric units of distance, mass, and volume'}

Modules: ["Knowledge_Retrieval", "Solution_Generator", "Answer_Generator"]


Question: Look at the models of molecules below. Select the elementary substance.

Options: (A) fluoromethanol (B) ozone (C) carbon tetrachloride

Metadata: {'pid': '411', 'has_image': True, 'grade': 6, 'subject': 'natural science', 'topic': 'chemistry', 'category': 'Atoms and molecules', 'skill': 'Identify elementary substances and compounds using models'}

Modules: ["Text_Detector", "Knowledge_Retrieval", "Bing_Search", "Solution_Generator", "Answer_Generator"]

Question: Which figure of speech is used in this text?\nHunter remarked that the new book on anti-gravity was impossible to put down.

Options: (A) alliteration (B) pun

Metadata: {'pid': '41', 'has_image': False, 'grade': 9, 'subject': 'language science', 'topic': 'figurative-language', 'category': 'Literary devices', 'skill': 'Classify figures of speech: review'}

Modules: ["Knowledge_Retrieval", "Solution_Generator", "Answer_Generator"]

Question: Which rhetorical appeal is primarily used in this ad?

Options: (A) ethos (character) (B) pathos (emotion) (C) logos (reason)

Metadata: {'pid': '1062', 'has_image': True, 'grade': 12, 'subject': 'language science', 'topic': 'writing-strategies', 'category': 'Persuasive strategies', 'skill': 'Identify appeals to ethos, pathos, and logos in advertisements'}

Modules: ["Text_Detector", "Knowledge_Retrieval", "Solution_Generator", "Answer_Generator"]

Table:
designer watch | $8,141
designer coat | $6,391

Question: How much more does a designer watch cost than a designer coat? (unit: $)

Modules: ["Program_Generator", "Program_Verifier", "Program_Executor", "Answer_Generator"]

Table:
Beverage | Thursday | Friday
Kickin' Coffee | $9 | $18
Brenner's Juices | $5 | $8
Krazy Kola | $13 | $14
Olde Tyme Cola | $17 | $9
Fizzy Fun | $12 | $19

Question: Alana, an employee at Hong's Convenience Store, looked at the sales of each of its soda products. Which beverage had lower sales on Thursday, Krazy Kola or Fizzy Fun?

Modules: ["Column_Lookup", "Program_Generator", "Program_Verifier", "Program_Executor", "Answer_Generator"]

Table:
Ashland | 3:45 A.M. | 12:00 P.M. | 5:15 P.M. | 8:45 P.M. | 10:30 P.M.
Belmont | 5:00 A.M. | 1:15 P.M. | 6:30 P.M. | 10:00 P.M. | 11:45 P.M.
Springtown | 6:45 A.M. | 3:00 P.M. | 8:15 P.M. | 11:45 P.M. | 1:30 A.M.
Oxford | 8:15 A.M. | 4:30 P.M. | 9:45 P.M. | 1:15 A.M. | 3:00 A.M.
Cedarburg | 9:30 A.M. | 5:45 P.M. | 11:00 P.M. | 2:30 A.M. | 4:15 A.M.
Oak Grove | 10:15 A.M. | 6:30 P.M. | 11:45 P.M. | 3:15 A.M. | 5:00 A.M.
Brookfield | 11:30 A.M. | 7:45 P.M. | 1:00 A.M. | 4:30 A.M. | 6:15 A.M.
Oakdale | 1:00 P.M. | 9:15 P.M. | 2:30 A.M. | 6:00 A.M. | 7:45 A.M.
Richmond | 2:00 P.M. | 10:15 P.M. | 3:30 A.M. | 7:00 A.M. | 8:45 A.M.

Question: Look at the following schedule. Jaylen just missed the 1.15 P.M. train at Belmont. What time is the next train?

Modules: ["Row_Lookup", "Solution_Generator", "Answer_Generator"]

Table:
x | y
10 | 15
11 | 9
12 | 2

Question: The table shows a function. Is the function linear or nonlinear?

Modules: ["Knowledge_Retrieval", "Solution_Generator", "Answer_Generator"]

Table:
Stem | Leaf 
0 | 1, 4, 7
1 | 2, 4, 5
2 | 0, 3
3 | 
4 | 0, 1, 5, 8, 9
5 | 7, 8, 8, 9
6 | 
7 | 8, 8
8 | 3, 7, 7, 8
9 | 0

Question: A researcher recorded the number of cows on each farm in the county. How many farms have at least 4 cows but fewer than 46 cows?

Modules: ["Row_Lookup", "Table_Verbalizer", "Program_Generator", "Program_Verifier", "Program_Executor", "Answer_Generator"]

Table:
Stem | Leaf 
1 | 2, 4
2 | 2, 4
3 | 0, 0, 0, 0, 5, 9, 9
4 | 4, 7
5 | 4, 7
6 | 
7 | 2, 6
8 | 1, 3
9 | 0

Question: An architecture student measured the heights of all the buildings downtown. How many buildings are exactly 30 meters tall?

Modules: ["Row_Lookup", "Knowledge_Retrieval", "Program_Generator", "Program_Verifier", "Program_Executor", "Answer_Generator"]

Table:
 | Fly | Read minds
Forgetful | 2 | 4
Lazy | 2 | 2

Question: A creative writing class compiled a list of their favorite superheroes. They listed each superhero's superpower and personality flaw. What is the probability that a randomly selected superhero is lazy and can read minds? Simplify any fractions.

Modules: ["Knowledge_Retrieval", "Program_Generator", "Program_Verifier", "Program_Executor", "Answer_Generator"]

Table:
Day | Number of balloons
Tuesday | 9
Wednesday | 4
Thursday | 8
Friday | 4
Saturday | 8
Sunday | 10
Monday | 2

Question: The manager of a party supply store researched how many balloons it sold in the past 7 days. What is the median of the numbers?

Modules: ["Knowledge_Retrieval", "Program_Generator", "Program_Verifier", "Program_Executor", "Answer_Generator"]

Table:
Park | Number of soccer fields
Canyon Park | 7
Windy Hill Park | 3
Elmhurst Park | 2
Lighthouse Park | 8
Madison Park | 4

Question: The parks department compared how many soccer fields there are at each park. What is the range of the numbers?

Modules: ["Solution_Generator", "Answer_Generator"]

Table:
 | Cat eye frames | Browline frames
Polarized lenses | 3 | 4
Regular lenses | 2 | 2

Question: After growing tired of squinting while driving, Dalton went shopping for a pair of sunglasses. He tried on glasses with different frames and lenses. What is the probability that a randomly selected pair of sunglasses has polarized lenses and cat eye frames? Simplify any fractions.

Modules: ["Program_Generator", "Program_Verifier", "Program_Executor", "Answer_Generator"]

Table:
Sandwich | Number of customers
Cheese | 300
Egg salad | 940
Other | 520

Question: A sandwich shop in Newport polled its customers regarding their favorite sandwiches. What fraction of customers preferred egg salad sandwiches? Simplify your answer.

Modules: ["Program_Generator", "Program_Verifier", "Program_Executor", "Answer_Generator"]

Table:
Runs scored | Frequency
0 | 20
1 | 19
2 | 2
3 | 4
4 | 18
5 | 3

Question: A statistician analyzed the number of runs scored by players last season. How many players are there in all?

Modules: ["Program_Generator", "Program_Verifier", "Program_Executor", "Answer_Generator"]

Table:
Name | Number of stickers
Bernie | 7
Trent | 7
Lily | 5
Roxanne | 5
Natalie | 5

Question: Some friends compared the sizes of their sticker collections. What is the mode of the numbers?

Modules: ["Knowledge_Retrieval", "Program_Generator", "Program_Verifier", "Program_Executor", "Answer_Generator"]

Table:
Company | Number of phone calls
Henderson Co. | 912
Brave New Day Corporation | 921
Reardon Corporation | 991
Tad's Coffee Company | 929

Question: Some companies compared how many phone calls they made. Which company made the most phone calls?

Modules: ["Solution_Generator", "Answer_Generator"]

Table:
Stem | Leaf 
5 | 3, 3
6 | 8, 9
7 | 2, 4
8 | 7, 7
9 | 0, 0, 0

Question: Maria counted the pages in each book on her English class's required reading list. What is the largest number of pages?

Modules: ["Knowledge_Retrieval", "Solution_Generator", "Answer_Generator"]

Table:
Employee | Pay period |
Felicia Singer | August 16-31 |
Total earnings | | $2,110.00
Federal income tax | $291.66 |
Other taxes | $161.40 |
Total taxes | | ?
Pay after taxes | | ?

Question: Look at Felicia's pay stub. Felicia lives in a state without state income tax. How much payroll tax did Felicia pay in total?

Modules: ["Knowledge_Retrieval", "Table_Verbalizer", "Program_Generator", "Program_Verifier", "Program_Executor", "Answer_Generator"]
"""