import requests
import csv
import json
import re

API_URL = "http://localhost:3000"

def scrape_problems(limit=10, output_file="problems.csv"):
    response = requests.get(f"{API_URL}/problems?limit={limit}")
    problems = response.json()

    with open(output_file, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "title", "slug", "tags"])
        for problem in problems["problemsetQuestionList"]:
            writer.writerow([problem["questionFrontendId"], problem["title"], problem["titleSlug"], [tag["name"] for tag in problem["topicTags"]]])
            print(f"[{problem['questionFrontendId']}/{limit}] {problem['title']} written to {output_file}")

def scrape_problem_descriptions(input_csv="problems.csv" ):
    total_problems = sum(1 for line in open(input_csv)) - 1
    with open(input_csv, "r") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            problem_id = row[0]
            problem_slug = row[2]
            response = requests.get(f"{API_URL}/select?titleSlug={problem_slug}")
            problem = response.json()
            with open(f"problems/{problem_id}.json", "w") as f:
                json.dump(problem, f)
                print(f"[{problem_id}/{total_problems}] Problem {problem_id} description written to problem_descriptions/{problem_id}.json")

def parse_problems(input_csv="problems.csv", output_dir="parsed_problems"):
    """
    Parse the problems from the input CSV file to markdown files in the output directory
    Also cleans the question description, converting html to markdown
    """
    with open(input_csv, "r") as f:
        reader = csv.reader(f)
        total_problems = sum(1 for line in open(input_csv)) - 1
        next(reader)

        for row in reader:
            problem_id = row[0]
            with open(f"problems/{problem_id}.json", "r") as f:
                problem = json.load(f)
                with open(f"{output_dir}/{problem_id}.md", "w") as f:
                    # Clean question_description
                    # FIX: constraints not being cleaned properly
                    question_description = problem["question"]
                    question_description = question_description.replace("<p>", "").replace("</p>", "\n")
                    question_description = question_description.replace("<strong>", "**").replace("</strong>", "**")
                    question_description = question_description.replace("<em>", "*").replace("</em>", "*")
                    question_description = question_description.replace("<code>", "`").replace("</code>", "`")
                    question_description = question_description.replace("<ul>", "").replace("</ul>", "")
                    question_description = question_description.replace("<pre>", "```").replace("</pre>", "```")
                    question_description = question_description.replace("&nbsp;", " ")
                    question_description = question_description.replace("&lt;", "<").replace("&gt;", ">")
                    question_description = re.sub(r"\n+", "\n", question_description)
                    question_description = re.sub(r"<.*?>", "", question_description)

                    f.write(f"---\ntitle: {problem['questionTitle']}\ndescription: {question_description[:100]}\n---\n")
                    f.write(f"# {problem["questionTitle"]}\n")
                    f.write(f"## Description\n")
                    f.write(f"{question_description}\n")
                    print(f"[{problem_id}/{total_problems}] Problem {problem_id} parsed to {output_dir}/{problem_id}.md") 

# scrape_problems(100, "problems.csv")
# scrape_problem_descriptions("problems.csv")
parse_problems("problems.csv", "parsed_problems")
