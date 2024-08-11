# https://drive.google.com/file/d/1ELWixTzBi7DuYxxBBNq7i50H0Cf2PqcC/view?usp=sharing


import requests

file_id = '1ELWixTzBi7DuYxxBBNq7i50H0Cf2PqcC'
url = f'https://drive.google.com/uc?export=download&id={file_id}'

response = requests.get(url)
if response.status_code == 200:
    content = response.text
    print(content)
    # You can now use 'content' in your project
else:
    print('Failed to download file')
