from collections import OrderedDict
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import xmltodict
import urllib3
import itertools
import datatype
import json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_player_list(team: str, league=None) -> dict:
    '''
    取得球員名單。球隊代碼請見說明文件

    參數：
    `team`:     `str`，球隊代碼。
    `league`:   `str`，一二軍代碼，一軍為`'A'`，二軍為`'D'`，若留空則取得所有的名單
    '''
    if(not team in datatype.team_code.keys()):
        raise ValueError('Team code incorrect.')
    if(league):
        if(not league in ['A', 'D']):
            raise ValueError('League code incorrect.')
    ses = HTMLSession()
    leagueList = []
    if(league):
        leagueList.append(league)
    else:
        leagueList = ['A', 'D']
    player_list = {}
    for l in leagueList:
        player_list[l] = []
        res = ses.post(datatype.root + '/team', data={
            'ClubNo': team,
            'KindCode': l
        }, verify=False)
        data: OrderedDict = xmltodict.parse('<html>' + res.text + '</html>')
        raw_player_list = list(itertools.chain(*[l['div'] for l in data['html']['div'] if l['@class'] == 'TeamPlayersList'][1:]))
        for raw_pl in raw_player_list:
            player_id = raw_pl['div']['div'][1]['div'][1]['a']['@href'].split('=')[1]
            player_name = raw_pl['div']['div'][1]['div'][1]['a']['#text']
            player_number = raw_pl['div']['div'][1]['div'][2]['#text']
            player_list[l].append({
                'name': player_name,
                'id': player_id,
                'number': player_number
            })
    return player_list


def get_player_info(player_id, get_batting_score=False, get_pitching_score=False, get_fielding_score=False) -> dict:
    '''
    取得球員的詳細資料，預設只會取得最基本的資料，將對應參數傳入`True`可以取得對應的詳細資料

    參數：
    `player_id`:            `str`或是`list[str]`，可由`get_player_list()`取得
    `get_batting_score`:    `bool`，取得打擊成績，預設為`False`
    `get_pitching_score`:   `bool`，取得投球成績，預設為`False`
    `get_fielding_score`:   `bool`，取得守備成績，預設為`False`
    '''
    if(not type(player_id) in [str, list]):
        raise ValueError('Player ID should be string or list of string')
    player_id_list = []
    if(type(player_id) == str):
        player_id_list.append(player_id)
    else:
        player_id_list = player_id
    ses = HTMLSession()
    player_info = {}
    for i in player_id_list:
        player_info[i] = {}
        res = ses.get(datatype.root+'/team/person?Acnt=' + i, verify=False)
        raw_data = BeautifulSoup(res.text, 'lxml')
        key_data = raw_data.find('div', {'class': 'PlayerBrief'})
        keywords = ['pos', 'b_t', 'ht_wt', 'born', 'debut', 'nationality', 'original_name', 'draft']
        info_data = {
            'team': key_data.find('div', {'class': 'team'}).text,
        }
        for k in keywords:
            info_data[k] = {
                'label': key_data.find('dd', {'class': k}).find('div', {'class': 'label'}).text,
                'desc': key_data.find('dd', {'class': k}).find('div', {'class': 'desc'}).text
            }
        player_info[i]['info'] = info_data
        findTarget = [f for f in range(0, 4) if ([False, get_batting_score, get_pitching_score, get_fielding_score])[f]]
        if len(findTarget) > 0:
            keys = [l.split("'")[1] for l in res.text.split('\n') if 'RequestVerificationToken' in l]
        else:
            continue
        targs = {
            'getfighteryearopts': 'FighterYearOpts',
            'getbattingscore': 'BattingScore',
            'getpitchscore': 'PitchScore',
            'getdefencescore': 'DefenceScore',
            'getfighterscore': 'fighterscore'
        }
        for ft in findTarget:
            url = datatype.root + '/team/' + list(targs.keys())[ft]
            targ = datatype.league_code
            for tag in targ.keys():
                res = ses.post(url, params={'acnt': i, 'kindCode': tag}, headers={
                    "requestverificationtoken": keys[ft],
                    "x-requested-with": "XMLHttpRequest"
                })
                if(list(targs.values())[ft] not in player_info[i]):
                    player_info[i][list(targs.values())[ft]] = {}
                player_info[i][list(targs.values())[ft]][tag] = json.loads(res.json()[list(targs.values())[ft]])
        if(get_fighter_score):
            player_info[i]['FighterScore'] = _get_fighter_score(ses, i, [keys[0], keys[4]], info_data['pos']['desc'])
    return player_info


def get_fighter_score(player_id, years: list = []) -> dict:
    '''
    取得對戰成績。預設搜尋生涯成績，欲搜尋逐年成績請見參數

    參數：
    `player_id`:    `str`或是`list[str]`，可由`get_player_list()`取得
    `years`:        取得資料年份，必須為list[str]，預設為空。
    '''
    if(not type(player_id) in [str, list]):
        raise ValueError('Player ID should be string or list of string')
    player_id_list = []
    if(type(player_id) == str):
        player_id_list.append(player_id)
    else:
        player_id_list = player_id
    ses = HTMLSession()
    fighter_score = {}
    for i in player_id_list:
        res = ses.get(datatype.root+'/team/person?Acnt=' + i, verify=False)
        keys = [l.split("'")[1] for l in res.text.split('\n') if 'RequestVerificationToken' in l]
        fighter_score[i] = _get_fighter_score(ses, i, [keys[0], keys[4]], years)
    return fighter_score


def _get_fighter_score(ses, player_id, keys, years):
    data = {}
    res = ses.post(datatype.root + '/team/getfighteryearopts', params={'acnt': player_id}, headers={
        "requestverificationtoken": keys[0],
        "x-requested-with": "XMLHttpRequest"
    })
    fighter_ops = json.loads(res.json()['FighterYearOpts'])
    for y in fighter_ops:
        if y not in years:
            continue
        res = ses.post(datatype.root + '/team/getfighterscore', params={'acnt': player_id, 'year': y['Year']}, headers={
            "requestverificationtoken": keys[1],
            "x-requested-with": "XMLHttpRequest"
        })
        data[y['Year']] = json.loads(res.json()['FighterScore'])
    res = ses.post(datatype.root + '/team/getfighterscore', params={'acnt': player_id, 'year': ''}, headers={
        "requestverificationtoken": keys[1],
        "x-requested-with": "XMLHttpRequest"
    })
    data['career'] = json.loads(res.json()['FighterScore'])
    return data


def get_homerun_detail(player_id) -> dict:
    '''
    取得全壘打明細

    參數：
    `player_id`:    `str`或是`list[str]`，可由`get_player_list()`取得
    `years`:        list[str]，取得資料年份，預設為空。
    '''
    if(not type(player_id) in [str, list]):
        raise ValueError('Player ID should be string or list of string')
    player_id_list = []
    if(type(player_id) == str):
        player_id_list.append(player_id)
    else:
        player_id_list = player_id
    ses = HTMLSession()
    homerun_detail = {}
    for i in player_id_list:
        res = ses.get(datatype.root+'/team/hr?Acnt=' + i, verify=False)
        data = []
        raw_data = BeautifulSoup(res.text)
        key_data = raw_data.find('div', {"class": 'RecordTable'})
        for rw in key_data.find_all('tr')[1:]:
            vals = [val.text for val in rw.find_all('td')]
            data.append({
                'num': vals[0],
                'year': vals[1],
                'gameNo': vals[2],
                'inning': vals[3],
                'date': vals[4],
                'park': vals[5],
                'pitcher': vals[6],
                'rbi': vals[7],
                'comment': vals[8]
            })
        homerun_detail[i] = data
    return homerun_detail


def get_apart_score(player_id, leagues: list = ['A'], years: list = ['9999']) -> dict:
    '''
    取得分項成績

    參數：
    `player_id`:    `str`或是`list[str]`，可由`get_player_list()`取得
    `years`:        list[str]，取得資料年份，`'9999'`為生涯累積，預設為`['9999']`
    `leagues`:      list[str]，比賽類型代碼，預設為`['A']`
    '''
    if(not type(player_id) in [str, list]):
        raise ValueError('Player ID should be string or list of string')
    player_id_list = []
    if(type(player_id) == str):
        player_id_list.append(player_id)
    else:
        player_id_list = player_id
    if(len(leagues) == 0 or len(years) == 0):
        raise ValueError('Length of leagues and years should not be zero.')
    ses = HTMLSession()
    apart_score = {}
    res = ses.get(datatype.root + '/team/apart?Acnt=' + player_id, verify=False)
    keys = [l.split("'")[1] for l in res.text.split('\n') if 'RequestVerificationToken:' in l]
    for i in player_id_list:
        apart_score[i] = {}
        for kc in leagues:
            apart_score[i][kc] = {}
            res = ses.post(datatype.root + '/team/getapartoptsaction', params={
                'acnt': i,
                'kindCode': kc,
            }, headers={
                "requestverificationtoken": keys[0],
                "x-requested-with": "XMLHttpRequest"
            })
            apart_opt_saction = res.json()
            year_ops = [row['Value'] for row in json.loads(apart_opt_saction['GameYearOpts'])]
            pos_ops = [row['Value'] for row in json.loads(apart_opt_saction['PositionOpts'])]
            for pos in pos_ops:
                apart_score[i][kc]['batting' if pos == '01' else 'pitching'] = {}
                res = ses.post(datatype.root + '/team/getapartoptsaction', params={
                    'acnt': i,
                    'kindCode': kc,
                    'position': pos
                }, headers={
                    "requestverificationtoken": keys[0],
                    "x-requested-with": "XMLHttpRequest"
                })
                for year in year_ops:
                    if year not in years:
                        continue
                    res = ses.post(datatype.root + '/team/getapartscore', params={
                        'acnt': i,
                        'kindCode': kc,
                        'position': pos,
                        'year': year
                    }, headers={
                        "requestverificationtoken": keys[1],
                        "x-requested-with": "XMLHttpRequest"
                    })
                    apart_score[i][kc]['batting' if pos == '01' else 'pitching'][year] = json.loads(res.json()['ApartScore'])
    return apart_score


def get_fighting_detail(player_id, oppo_teams: list = [], leagues: list = ['A'], years: list = ['9999']) -> dict:
    '''
    取得投打對戰成績。球隊代碼請見說明文件

    參數：
    `player_id`:    `str`或是`list[str]`，可由`get_player_list()`取得
    `oppo_teams`:   `list[str]`，對戰球隊代碼之陣列，留空位全部搜尋，預設為空
    `years`:        list[str]，取得資料年份，`'9999'`為生涯累積，預設為`['9999']`
    `leagues`:      list[str]，比賽類型代碼，預設為`['A']`
    '''
    oppo_teams = [s+'011' for s in oppo_teams]
    if(not type(player_id) in [str, list]):
        raise ValueError('Player ID should be string or list of string')
    player_id_list = []
    if(type(player_id) == str):
        player_id_list.append(player_id)
    else:
        player_id_list = player_id
    if(len(leagues) == 0 or len(years) == 0):
        raise ValueError('Length of leagues and years should not be zero.')
    ses = HTMLSession()
    fighting_score = {}
    for i in player_id_list:
        fighting_score[i] = {}
        res = ses.get(datatype.root + '/team/fighting?Acnt=' + i, verify=False)
        keys = [l.split("'")[1] for l in res.text.split('\n') if 'RequestVerificationToken' in l]
        for kc in leagues:
            fighting_score[i][kc] = {}
            res = ses.post(datatype.root + '/team/getfightingoptsaction', params={
                'acnt': i,
                'kindCode': kc,
            }, headers={
                "requestverificationtoken": keys[0],
                "x-requested-with": "XMLHttpRequest"
            })
            game_year_ops = [key['Value'] for key in json.loads(res.json()['GameYearOpts'])]
            for yea in game_year_ops:
                if yea not in years:
                    continue
                fighting_score[i][kc][yea] = {}
                res = ses.post(datatype.root + '/team/getfightingoptsaction', params={
                    'acnt': i,
                    'kindCode': kc,
                    'year': yea
                }, headers={
                    "requestverificationtoken": keys[0],
                    "x-requested-with": "XMLHttpRequest"
                })
                fighting_team_opts = [key['Value'] for key in json.loads(res.json()['FightingTeamOpts'])[1:]]
                for figt in fighting_team_opts:
                    if figt not in oppo_teams and not len(oppo_teams) == 0:
                        continue
                    res = ses.post(datatype.root + '/team/getfightingscore', params={
                        'acnt': i,
                        'kindCode': kc,
                        'year': yea,
                        'fightingTeamNo': figt
                    }, headers={
                        "requestverificationtoken": keys[1],
                        "x-requested-with": "XMLHttpRequest"
                    })
                    fighting_score[i][kc][yea][figt] = json.loads(res.json()['FightingScore'])
    return fighting_score


def get_follow_score(player_id, leagues: list = ['A'], years: list = []):
    '''
    取得分項成績

    參數：
    `player_id`:    `str`或是`list[str]`，可由`get_player_list()`取得
    `years`:        list[str]，取得資料年份，留空為取得全部，預設為空`
    `leagues`:      list[str]，比賽類型代碼，預設為`['A']`
    '''
    if(not type(player_id) in [str, list]):
        raise ValueError('Player ID should be string or list of string')
    player_id_list = []
    if(type(player_id) == str):
        player_id_list.append(player_id)
    else:
        player_id_list = player_id
    if(len(leagues) == 0):
        raise ValueError('Length of leagues and years should not be zero.')
    ses = HTMLSession()
    follow_score = {}
    for i in player_id_list:
        follow_score[i] = {}
        res = ses.get(datatype.root + '/team/follow?Acnt=' + i, verify=False)
        keys = [l.split("'")[1] for l in res.text.split('\n') if 'RequestVerificationToken' in l]
        for kc in leagues:
            follow_score[i][kc] = {}
            res = ses.post(datatype.root + '/team/getfollowoptsaction', params={
                'acnt': i,
                'kindCode': kc,
            }, headers={
                "requestverificationtoken": keys[0],
                "x-requested-with": "XMLHttpRequest"
            })
            year_opts = [row['Value'] for row in json.loads(res.json()['YearOpts'])]
            for year in year_opts:
                if year not in years and not len(years) == 0:
                    continue
                res = ses.post(datatype.root + '/team/getfollowscore', params={
                    'acnt': i,
                    'kindCode': kc,
                    'year': year
                }, headers={
                    "requestverificationtoken": keys[1],
                    "x-requested-with": "XMLHttpRequest"
                })
                follow_score[i][kc][year] = json.loads(res.json()['FollowScore'])
    return follow_score
