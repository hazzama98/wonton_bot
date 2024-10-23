import base64
import json
import os
import random
import sys
import time
from urllib.parse import parse_qs, unquote
import requests
from datetime import datetime, timedelta
import string

class Wonton:

    def __init__(self, proxy_config):
        self.headers = {
            'authority': 'wonton.food',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://www.wonton.restaurant',
            'referer': 'https://www.wonton.restaurant/',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"iOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'
        }
        self.proxy_config = proxy_config
        if self.proxy_config['use_proxy']:
            self.proxies = self.load_proxies()
        else:
            self.proxies = {}

    def print_(self, word):
        print(f"[⚔] | {word}")

    def make_request(self, method, url, headers, json=None, data=None):
        retry_count = 0
        while True:
            time.sleep(2)
            try:
                response = requests.request(method, url, headers=headers, json=json, data=data, proxies=self.proxies)
                if response.status_code >= 500:
                    if retry_count >= 4:
                        self.print_(f"Status Code: {response.status_code} | {response.text}")
                        return None
                    retry_count += 1
                elif response.status_code >= 400:
                    self.print_(f"Status Code: {response.status_code} | {response.text}")
                    return None
                else:
                    return response
            except requests.RequestException as e:
                self.print_(f"Request failed: {e}")
                if retry_count >= 4:
                    return None
                retry_count += 1

    def checkin(self, token):
        url = 'https://wonton.food/api/v1/checkin'
        headers = {**self.headers, 
        'Authorization': f'bearer {token}'}

        try:
            response = self.make_request('get',url, headers)
            if response is not None:
                data_checkin = response.json()
                if data_checkin is not None:
                    self.print_('Checkin Done')
                    self.print_(f"Last check-in date: {data_checkin.get('lastCheckinDay')}")
                    if data_checkin.get('newCheckin',False):
                        reward = next((config for config in data_checkin['configs'] if config['day'] == data_checkin['lastCheckinDay']), None)
                        if reward:
                            self.print_(f"Daily reward {data_checkin['lastCheckinDay']}:")
                            self.print_(f"- {reward['tokenReward']} WTON")
                            self.print_(f"- {reward['ticketReward']} ticket")
                    else:
                        self.print_('You checked in today.')
                return data_checkin
            
        except Exception as error:
            self.print_(f'Error Check-in: {error}')
            return None

    def check_farm_status(self, token):
        url = 'https://wonton.food/api/v1/user/farming-status'
        headers = {**self.headers, 'Authorization': f'bearer {token}'}

        try:
            res = self.make_request('get',url, headers)
            if res.status_code == 200:
                data = res.json()
                
                if not data:
                    return 'start'
                finishAt = data.get('finishAt')
                dt_object = datetime.fromisoformat(finishAt.replace("Z", "+00:00"))
                unix_time = int(dt_object.timestamp())
                remaining = unix_time - time.time()
                if remaining <= 0:
                    return data
                else:
                    self.print_(f'Remaining Farming Time : {round(remaining)} Seconds')
                    return 'wait'
                    
            else:
                self.print_(f'Error check farm: {res.status_code}')
                return None
        except Exception as error:
            self.print_(f'Lỗi khi kiểm tra trạng thái farming: {error}')
            return None

    def claim_farming(self, token):
        url = 'https://wonton.food/api/v1/user/farming-claim'
        headers = {**self.headers, 'Authorization': f'bearer {token}'}

        try:
            res = self.make_request('post',url, headers, data={})
            if res is not None:
                data = res.json()
                self.print_('Farming Claimed...')
                return data
            
        except Exception as error:
            self.print_(f'Error Claim farming: {error}')
            return None

    def start_farming(self, token):
        url = 'https://wonton.food/api/v1/user/start-farming'
        headers = {**self.headers, 'Authorization': f'bearer {token}'}

        try:
            res = self.make_request('post',url, headers, data={})
            if res is not None:
                data = res.json()
                self.print_('Farming Start...')
                return data

        except Exception as error:
            self.print_(f'Error Farming: {error}')
            return None

    def start_game(self, token):
        url = 'https://wonton.food/api/v1/user/start-game'
        headers = {**self.headers, 'Authorization': f'bearer {token}'}

        try:
            res = self.make_request('post',url, headers, data={})
            if res is not None:
                data = res.json()
                data['bonusRound'] = True  # Set bonus round to always True
                self.print_('Start the game successfully')
                return data
        except Exception as error:
            self.print_(f'Error Start game: {error}')
            return None

    def finish_game(self, token, points, hasBonus):
        url = 'https://wonton.food/api/v1/user/finish-game'
        headers = {**self.headers, 'Authorization': f'bearer {token}'}
        data = {'points': points, 'hasBonus': hasBonus}

        try:
            res = self.make_request('post',url, headers, json=data)
            if res is not None:
                response = res.json()
                return response

        except Exception as error:
            self.print_(f'Error Finish Game: {error}')
            return None
        
    def get_task(self, token):
        url = 'https://wonton.food/api/v1/task/list'
        headers = {**self.headers, 'Authorization': f'bearer {token}'}
        try:
            res = self.make_request('get',url, headers)
            if res is not None:
                data = res.json()
                tasks = data['tasks']
                taskProgress = data['taskProgress']

                for task in tasks:
                    name = task.get('name')
                    if name in ['Join FunMe Channel', 'Join MasterChef Channel']:
                        self.print_(f"Task {name} Skip!!")
                        continue

                    rewardAmount = task.get('rewardAmount')
                    alls = f"Task : {name} | Reward : {rewardAmount}"
                    if task['status'] == 0:
                        payload = {'taskId': task['id']}
                        self.verify_task(token, payload, alls)
                    else:
                        self.print_(f"{alls} Done")

                if taskProgress >= 3:
                    self.get_task_progress(token)
            else:
                self.print_(f'Error Get Task: {res}')
        except Exception as error:
            self.print_(f'Error Get Task: {error}')

    def verify_task(self, token, payload, alls):
        url = 'https://wonton.food/api/v1/task/verify'
        headers = {**self.headers, 'Authorization': f'bearer {token}'}
        response = self.make_request('post',url, headers, json=payload)
        if response is not None:
            if response.status_code == 200:
                self.print_(f"Verification {alls}")
                time.sleep(1)
                self.claim_task(token, payload, alls)
            else:
                self.print_(f"Failed Verification {alls}")

    def claim_task(self, token, payload, alls):
        url = 'https://wonton.food/api/v1/task/claim'
        headers = {**self.headers, 'Authorization': f'bearer {token}'}
        response = self.make_request('post',url, headers, json=payload)
        if response is not None:
            if response.status_code == 200:
                self.print_(f"Claim {alls}")
            else:
                self.print_(f"Failed Claim {alls}")

    def get_task_progress(self, token):
        url = 'https://wonton.food/api/v1/task/claim-progress'
        headers = {**self.headers, 'Authorization': f'bearer {token}'}

        try:
            res = self.make_request('get',url, headers)
            if res.status_code == 200:
                data = res.json()
                items = data['items']

                self.print_('Claim WONTON successful, received')
                for item in items:
                    self.print_(f"Name: {item.get('name')} | Farming Power : {item.get('farmingPower')} | Token Value : {item.get('tokenValue')} WTON | {item.get('value')} TON")
            else:
                self.print_(f'Error Get: {res.status_code}')
        except Exception as error:
            self.print_(f'Error Get: {error}')

    def login(self, data):
        url = 'https://wonton.food/api/v1/user/auth'
        payload = {'initData': data, 'inviteCode': ''}

        try:
            response = self.make_request('post', url, self.headers, json=payload)
            if response is not None:
                data = response.json()
                return data

        except Exception as error:
            self.print_(f'Error Login: {error}')
            return None

    def get_user(self, token):
        url = 'https://wonton.food/api/v1/user'
        headers = {**self.headers, 'Authorization': f'bearer {token}'}

        try:
            response = self.make_request('get',url, headers)
            if response is not None:
                return response.json()

        except Exception as error:
            self.print_(f'Get user error : {error}')
            return None

    def clear_gift_task(self, token, types):
        url = f'https://wonton.food/api/v1/user/claim-task-gift?type={types}'
        headers = {**self.headers, 'Authorization': f'bearer {token}'}

        try:
            response = self.make_request('get',url, headers)
            if response is not None:
                jsons = response.json()
                self.print_(f"Claim gift Task {types} Done")
                items = jsons.get('items')
                for item in items:
                    self.print_(f"Name: {item.get('name')} | Farming Power : {item.get('farmingPower')} | Token Value : {item.get('tokenValue')} WTON | {item.get('value')} TON")
                return jsons

        except Exception as error:
            self.print_(f'Get user error : {error}')
            return None
    
    def get_list_wonton(self, token):
        url = 'https://wonton.food/api/v1/shop/list'
        headers = {**self.headers, 'Authorization': f'bearer {token}'}
        try:
            response = self.make_request('get',url, headers)
            if response is not None:
                jsons = response.json()
                shopItems = jsons.get('shopItems',[])
                in_used = 0
                list_wonton = []
                data_item = {}
                ton = 0.0
                wton = 0
                for item in shopItems:
                    inventory = item.get('inventory')
                    inUse = item.get('inUse')
                    if inUse:
                        in_used = int(item.get('farmingPower'))
                        data_item = item
                    if inventory > 0 :
                        farmingPower = int(item.get('farmingPower',0))
                        value = float(item.get('value',0))
                        wton += farmingPower*inventory
                        ton += value*inventory
                        list_wonton.append(item)
                
                sorted_data = sorted(list_wonton, key=lambda x: int(x['farmingPower']), reverse=True)
                for data in sorted_data:
                    power = int(data.get('farmingPower'))
                    if power > in_used:
                        self.set_wonton(token, data)
                        data_item = data
                        break
                return {'ton': ton, 'wton':wton, 'data':data_item}

        except Exception as error:
            self.print_(f'Get user error : {error}')
            return None
    
    def set_wonton(self, token, item):
        url = 'https://wonton.food/api/v1/shop/use-item'
        id = item.get('id')
        payload = {'itemId': id}
        headers = {**self.headers, 
                   'Authorization': f'bearer {token}'
                   }
        try:
            response = self.make_request('post', url, headers, json=payload)
            if response is not None:
                if response.status_code == 200:
                    name = item.get('name','')
                    farmingPower = item.get('farmingPower','0')
                    self.print_(f"Set Farming Done | Name : {name}, Farming Power : {farmingPower}")

        except Exception as error:
            self.print_(f'Get user error : {error}')
            return None
        
    def load_proxies(self):
        try:
            with open('proxy.txt', 'r') as file:
                proxy = file.read().strip()
                return {
                    'http': proxy,
                    'https': proxy
                }
        except FileNotFoundError:
            print("File proxy.txt not found.")
            return {}

def print_(word):
    print(f"[⚔] | {word}")

def gets(id):
    try:
        with open("tokens.json", "r") as file:
            tokens = json.load(file)
        return tokens.get(str(id))
    except FileNotFoundError:
        self.print_("File tokens.json not found.")
        return None
    except json.JSONDecodeError:
        self.print_("Error decoding JSON from tokens.json.")
        return None

def save(id, token):
    try:
        with open("tokens.json", "r") as file:
            tokens = json.load(file)
        tokens[str(id)] = token
        with open("tokens.json", "w") as file:
            json.dump(tokens, file, indent=4)
    except FileNotFoundError:
        self.print_("File tokens.json not found.")
    except json.JSONDecodeError:
        self.print_("Error decoding JSON from tokens.json.")

def delete_all():
    open("tokens.json", "w").write(json.dumps({}, indent=4))

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

                
def key_bot():
    api = base64.b64decode("aHR0cDovL2l0YmFhcnRzLmNvbS9hcGkuanNvbg==").decode('utf-8')
    try:
        response = requests.get(api)
        response.raise_for_status()
        try:
            data = response.json()
            header = data['header']
            print('\033[96m' + header + '\033[0m')
        except json.JSONDecodeError:
            print('\033[96m' + response.text + '\033[0m')
    except requests.RequestException as e:
        print_('\033[96m' + f"Failed to load header: {e}" + '\033[0m')

def load_query():
    try:
        with open('query.txt', 'r') as f:
            queries = [line.strip() for line in f.readlines()]
        return queries
    except FileNotFoundError:
        print("File query.txt not found.")
        return [  ]
    except Exception as e:
        print("Failed get Query :", str(e))
        return [  ]

def parse_query(query: str):
    parsed_query = parse_qs(query)
    parsed_query = {k: v[0] for k, v in parsed_query.items()}
    user_data = json.loads(unquote(parsed_query['user']))
    parsed_query['user'] = user_data
    return parsed_query

def print_delay(delay):
    print()
    while delay > 0:
        hours, remainder = divmod(delay, 3600)
        minutes, seconds = divmod(remainder, 60)
        sys.stdout.write(f"\r[⚔] | Waiting Time: {round(hours)} hours, {round(minutes)} minutes, and {round(seconds)} seconds")
        sys.stdout.flush()
        time.sleep(1)
        delay -= 1
    print_("Waiting Done, Starting....\n")
       
def main():
    def load_config():
        try:
            with open('config.json', 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print("File config.json not found.")
            return {}
        except json.JSONDecodeError:
            print("Error decoding JSON from config.json.")
            return {}

    config = load_config()
    selector_task = config.get('auto_clear_task', 'n')  
    selector_game = config.get('auto_play_game', 'n') 
    selector_max = config.get('score_range', '50-80') 

    while True:
        delete_all()
        start_time = time.time()
        delay = 3*3750
        clear_terminal()
        key_bot()
        queries = load_query()
        sum = len(queries)
        wonton = Wonton(config)
        tickets = []
        ton = 0.0
        wton = 0
        for index, query in enumerate(queries, start=1):
            users = parse_query(query).get('user')
            id = users.get('id')
            print_(f"Account {index}/{sum} [ {users.get('username')} ]")
            print_('generate token...')
            data_login = wonton.login(query)
            ticketCount = data_login.get('ticketCount')
            token = gets(id)
            if token is None:
                token = data_login.get('tokens').get('accessToken')
                save(id, token)
            data_user = data_login.get('user',{})
            tokenBalance = data_user.get('tokenBalance','0')
            withdrawableBalance = data_user.get('withdrawableBalance','0')
            if data_user is not None:
                print_(f"WTON Balance: {tokenBalance}")
                print_(f"TON Balance: {withdrawableBalance}")
                print_(f"Ticket Count: {(data_login['ticketCount'])}")
                wton += int(tokenBalance)
                ton += float(withdrawableBalance)
                wonton.checkin(token)
            
            hasClaimedOkx = data_user.get('hasClaimedOkx',False)
            hasClaimedBinance = data_user.get('hasClaimedBinance',False)
            hasClaimedHackerLeague = data_user.get('hasClaimedHackerLeague',False)

            if hasClaimedOkx == False:
                wonton.clear_gift_task(token, "OKX_WALLET")
            
            if hasClaimedBinance == False:
                wonton.clear_gift_task(token, "BINANCE_SIGN_UP")
            
            if hasClaimedHackerLeague == False:
                wonton.clear_gift_task(token, "HACKER_LEAGUE")

            data_farming = wonton.check_farm_status(token)
            if data_farming is not None:
                if data_farming == 'start':
                    wonton.start_farming(token)
                elif data_farming == 'wait':
                    print()
                else:
                    wonton.claim_farming(token)
                    wonton.start_farming(token)

            data_list = wonton.get_list_wonton(token)
            if data_list is not None:
                stats = data_list.get('data').get('stats')[2]
                ton += float(data_list.get('ton'))
                wton += int(data_list.get('wton'))

            tickets.append({'ticket': ticketCount, 'stats':int(stats)})
        

        for index, query in enumerate(queries):
            mid_time = time.time()
            remaining_time = delay - (mid_time-start_time)
            if remaining_time <= 0:
                break
            users = parse_query(query).get('user')
            id = users.get('id')
            print_(f"Account {index+1}/{sum} [ {users.get('username')} ]")
            data = tickets[index]
            token = gets(id)

            print_('generate token...')
            data_login = wonton.login(query)
            token = data_login.get('tokens').get('accessToken')
            save(id, token)
            
            if selector_task == 'y':
                print_('Staring Task...')
                wonton.get_task(token)
            if selector_game == 'y':
                print_('Staring Play Game...')
                ticket = data.get('ticket',0)
                if ticket == 0:
                    print_('No have Ticket To Play')
                else:
                    print_(f'Remaining ticket : {ticket}')
                    stats = data.get('stats')
                    while ticket > 0:
                        
                        game_data = wonton.start_game(token)
                        if game_data:
                            hasBonus = game_data.get('bonusRound',False)
                            print_(f'Bonus Round: {hasBonus}')
                            time.sleep(random.randint(20,25))
                            stats = data.get('stats')
                            rand = random.randint(90, 150)
                            points = rand*stats
                            if selector_max =='y':
                                rand = random.randint(130,200)
                                points = rand*stats
                            finish_data = wonton.finish_game(token, points, hasBonus)
                            if finish_data is not None:
                                ticket -= 1
                                print_(f'Playing game done reward : {points} points')
                                if hasBonus:
                                    print_("Bonus Reward !!")
                                    items = finish_data.get('items',[])
                                    for item in items:
                                        print_(f"Name: {item.get('name')} | Farming Power : {item.get('farmingPower')} | Token Value : {item.get('tokenValue')} WTON | {item.get('value')} TON")
        print()
        print_(f"Total Balance | Wton : {wton} | TON : {ton}")
        end_time = time.time()
        total = delay - (end_time-start_time)
        if total > 0:
            print_delay(total)

if __name__ == "__main__":
     main()

