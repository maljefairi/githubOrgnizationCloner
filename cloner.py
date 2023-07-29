import os
import time
from dotenv import load_dotenv
import requests
from git import Repo
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S',
                    level=logging.INFO)

# Load environment variables
load_dotenv()

ORG_NAME = os.getenv('ORG_NAME')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
DELAY = int(os.getenv('DELAY', 300))

rate_limit_reset_time = datetime.now()


def fetch_repository_information():
    global rate_limit_reset_time

    while True:
        if rate_limit_reset_time > datetime.now():
            sleep_time = (rate_limit_reset_time - datetime.now()).total_seconds()
            time.sleep(sleep_time)
        try:
            request_url = f'https://api.github.com/orgs/{ORG_NAME}/repos?per_page=100'
            headers = {'Authorization': f'token {GITHUB_TOKEN}'}
            response = requests.get(request_url, headers=headers)
            response.raise_for_status()

            if 'X-RateLimit-Reset' in response.headers:
                rate_limit_reset_time = datetime.fromtimestamp(int(response.headers['X-RateLimit-Reset']))
            return response.json()

        except requests.RequestException as request_exception:
            logging.error('Failed to fetch repository information.',
                          exc_info=request_exception)
            time.sleep(DELAY)


def clone_and_pull_repositories(repository_information):
    repository_url = repository_information.get('ssh_url')
    repository_name = repository_information.get('name')

    try:
        if repository_name not in os.listdir('.'):
            Repo.clone_from(repository_url, repository_name)
            logging.info(f'Cloned repository: {repository_name}.')
        else:
            repository = Repo(repository_name)
            origin = repository.remotes.origin
            origin.pull()
            logging.info(f'Updated repository: {repository_name}.')

    except Exception as exception:
        logging.error(f'Error in cloning/pulling repository: {repository_name}.',
                      exc_info=exception)


def main():
    while True:
        repositories_info = fetch_repository_information()
        for repository_info in repositories_info:
            clone_and_pull_repositories(repository_info)
        time.sleep(DELAY)


if __name__ == '__main__':
    main()