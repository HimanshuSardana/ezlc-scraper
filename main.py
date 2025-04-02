import requests
import csv
import html
from bs4 import BeautifulSoup
import os
import json
import re

API_URL = "http://localhost:3000"

def scrape_problems(limit=10, output_file="problems.csv"):
    """
    Scrape problems from the API and write them to a CSV file
    """
    response = requests.get(f"{API_URL}/problems?limit={limit}")
    problems = response.json()

    with open(output_file, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "title", "slug", "tags"])
        for problem in problems["problemsetQuestionList"]:
            writer.writerow([problem["questionFrontendId"], problem["title"], problem["titleSlug"], [tag["name"] for tag in problem["topicTags"]]])
            print(f"[{problem['questionFrontendId']}/{limit}] {problem['title']} written to {output_file}")

def scrape_problem_descriptions(input_csv="problems.csv" ):
    """
    Scrape the problem descriptions from the API and write them to JSON files
    """
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
                    try:
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
                    except:
                        print(f"Error parsing problem {problem_id}")
                        continue

                    f.write(f"---\ntitle: {problem['questionTitle']}\ndescription: {question_description[:100]}\n---\n")
                    f.write(f"# {problem["questionTitle"]}\n")
                    f.write(f"## Description\n")
                    f.write(f"{question_description}\n")
                    print(f"[{problem_id}/{total_problems}] Problem {problem_id} parsed to {output_dir}/{problem_id}.md") 

def clean_html(text):
    """
    Cleans HTML content, decodes escape sequences, and normalizes whitespace.
    """
    if not text:
        return ""

    # Decode HTML entities (&lt;, &gt;, etc.)
    text = html.unescape(text)

    # Remove HTML tags
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text(separator="\n")  # Convert <p> and <br> to newlines

    # Replace multiple newlines and spaces with a single newline
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()

    return text

def process_question_description(questionDescription):
    try:
        if not questionDescription:
            return ""  # Return an empty string if None or empty
        
        # Ensure it's a string before applying replace operations
        questionDescription = str(questionDescription)

        questionDescription = questionDescription.replace("<p>", "").replace("</p>", "\n")
        questionDescription = questionDescription.replace("<strong>", "").replace("</strong>", "")
        questionDescription = questionDescription.replace("<em>", "").replace("</em>", "")
        questionDescription = questionDescription.replace("<code>", "").replace("</code>", "")
        questionDescription = questionDescription.replace("<ul>", "").replace("</ul>", "")
        questionDescription = questionDescription.replace("<pre>", "").replace("</pre>", "")
        questionDescription = questionDescription.replace("&nbsp;", " ")
        questionDescription = questionDescription.replace("&lt;", "<").replace("&gt;", ">")
        questionDescription = re.sub(r"<.*?>", "", questionDescription)

        # Remove all text from description after the string "Example"
        questionDescription = questionDescription.split("Example")[0]
        questionDescription = questionDescription.replace("\n", "")

        return questionDescription
    except Exception as e:
        print(f"Error processing question description: {e}")
        return ""

def generate_training_data(input_csv="problems.csv", output_csv="training_data.csv"):
    """
    Generate training data from JSON files, clean descriptions, and write to a structured CSV.
    """
    if not os.path.exists(input_csv):
        print(f"Error: {input_csv} not found.")
        return

    training_data = []

    try:
        with open(input_csv, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header if present

            for row in reader:
                try:
                    if not row:
                        continue  # Skip empty rows
                    
                    id = row[0].strip()
                    json_path = f"problems/{id}.json"
                    
                    if not os.path.exists(json_path):
                        print(f"Warning: {json_path} not found.")
                        continue  # Skip if file doesn't exist
                    
                    with open(json_path, "r", encoding="utf-8") as json_file:
                        problem = json.load(json_file)

                        questionTitle = problem.get("questionTitle", "").strip()
                        questionDescription = process_question_description(problem.get("question", ""))
                        questionDifficulty = problem.get("difficulty", "").strip()
                        questionTags = [tag["name"].strip() for tag in problem.get("topicTags", []) if "name" in tag]

                        training_data.append([id, questionTitle, questionDescription, questionDifficulty, ", ".join(questionTags)])
                except Exception as e:
                    print(f"Error processing problem {id}: {e}")
                    continue

        if training_data:
            with open(output_csv, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "title", "description", "difficulty", "tags"])
                writer.writerows(training_data)
                print(f"Problems with Descriptions written to {output_csv}")
        else:
            print("No valid training data to write.")
    except Exception as e:
        print(f"Error processing input CSV: {e}")

# scrape_problems(3450, "problems.csv")
# scrape_problem_descriptions("problems.csv")
# parse_problems("problems.csv", "parsed_problems")
generate_training_data("problems.csv", "problems_with_descriptions.csv")
