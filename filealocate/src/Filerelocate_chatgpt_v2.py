import shutil
import subprocess
import os
import json
from datetime import datetime
from openai import OpenAI
import tiktoken # type: ignore

def get_folder_structure(tidy_path):
    try:
        result = subprocess.run(['tree', '-L', '1', tidy_path], capture_output=True, text=True)
        if result.returncode != 0:
            print("Error running tree command.")
            return None
        return result.stdout
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def prompting(tree_result):
    prompt = f"""
    I have a list of directories, and I need you to categorize each one into predefined categories. The categories are: "Images", "Documents", "Music", "Videos", "Code", "Art", "Miscellaneous". 

    Please provide the output strictly in the exact same format as the following,
    ```
      /directory/one/path : Category
      /directory/two/path : Category
      ...
    ```
    Here is the list of directories:
    {tree_result}

    Please categorize the above directories.
    """
    return prompt 

def categorize_directories(prompt):
    client = OpenAI()
    completion = client.chat.completions.create(
      model="gpt-3.5-turbo",
      messages=[
        {"role": "system", "content": "you are an assistant that categorizes directories."},
        {"role": "user", "content": prompt}
      ]
    )
    return completion.choices[0].message.content.replace("\\n", "\n")


def move_files(categorized_list, path_map):
    logbox = {}

    for item in categorized_list:
        split_point = item.split(":")
        if len(split_point) <= 1 or item.strip() == '':
            continue

        box_item_path = split_point[0].strip()
        box_item_category = split_point[1].strip()
        box_destination = path_map.get(box_item_category)

        if not box_destination:
            print(f"Unknown category: {box_item_category} for item: {box_item_path}")
            continue

        try:
            shutil.move(box_item_path, box_destination)
            logbox[box_item_path] = box_destination
        except shutil.Error as e:
            print(f"Error moving {box_item_path} to {box_destination}: {e}")
        except IOError as e:
            print(f"IOError for {box_item_path} to {box_destination}: {e}")
        except Exception as e:
            print(f"Unexpected error moving {box_item_path} to {box_destination}: {e}")

    return logbox

'''
def token_convert(prompt, categorized_list):
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    input_token_count = encoding.encode(prompt)
    output_token_count = encoding.encode(categorized_list)
'''    
def token_convert(prompt: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    input_num_tokens = len(encoding.encode(prompt))
    return input_num_tokens


def token_to_dollar(x):
    dollars = (x / 1000000) * 0.50
    result = f"{dollars} dollars"

    return result
def main():
    #get tidy path
    tidy_path = input("Enter the path of the folder which you'd like to tidy: ")

    if not os.path.isdir(tidy_path):
        print("The provided path is not a valid directory.")
        return
    #run path with tree command to get result
    tree_result = get_folder_structure(tidy_path)
    if not tree_result:
        return
    
    #slot tree result into predefined prompt template
    prompt = prompting(tree_result)
    #convert prompt to token
    input_token = token_convert(prompt)
    #convert input_token to dolalr
    input_dollar = token_to_dollar(input_token)

    proceed = input("The cost of input is around " + str(input_dollar) + ", do you wish to proceed? (y/n)")
    #proceed condition divider
    if proceed == 'y':
        print("sending prompt to gpt...")
        #run the prompt through gpt and retrieve
        categorized_list = categorize_directories(prompt)
        spliced_list = categorized_list.splitlines()
        path_map = {
            "Images": "/Users/arthuryeh/Desktop/testfolder/Images",
            "Documents": "/Users/arthuryeh/Desktop/testfolder/Documents",
            "Music": "/Users/arthuryeh/Desktop/testfolder/Music",
            "Videos": "/Users/arthuryeh/Desktop/testfolder/Videos",
            "Code": "/Users/arthuryeh/Desktop/testfolder/Code",
            "Art": "/Users/arthuryeh/Desktop/testfolder/Art",
            "Miscellaneous": "/Users/arthuryeh/Desktop/testfolder/Miscellaneous"
        }
        """Some error handling"""
        if not categorized_list:
            print("Failed to categorize directories.")
            return
        if not spliced_list:
            print("Failed to split list")
        print('successfully retrieved categorized list and shown below:', categorized_list)
        input('do you wish to proceed with the following categorization?')
        

        logbox = move_files(spliced_list, path_map)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"move_log_{timestamp}.json"
        with open(log_filename, "w", encoding='utf-8') as log_file:
            json.dump(logbox, log_file, indent=4, ensure_ascii=False)

        print(f"Tidying complete. Log saved to {log_filename}")

    elif proceed =='n':
        return

if __name__ == "__main__":
    main()
