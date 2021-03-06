# CPBL Crawler

中華職棒官方網站的爬蟲工具，使用 Python 撰寫

## 取得

使用 `git clone` 或是直接下載 zip 壓縮檔，解壓縮即可使用

### 安裝

需具備 python 3.9.7 或相容版本，  
接著安裝必要套件

```bash
pip install -r requirements.txt
```

## 使用範例

### 取得球員名單

引入套件

```python
import CPBL
```

使用球隊代碼取得中信兄弟之球員名單

```python
CPBL.get_player_list('ACN')
```

球隊代碼說明見文件下方

取得之資料如下：

```js
{
    ...{
        'name': '官大元',
        'id': '0000003078',
        'number': '18'
    }
    ...
}
```

其中id可以用來搜尋球員的詳細資料：

```python
CPBL.get_player_info('0000003078')
```

得資料如下：

```js
{
    '0000003078': {
        'info': {
            'team': '中信兄弟',
            'pos': {
                'label': '位置',
                'desc': '投手'
            },
            'b_t': {
                'label': '投打習慣',
                'desc': '右投右打'
            },
            'ht_wt': {
                'label': '身高/體重',
                'desc': '174(CM) / 68(KG)'
            },
            'born': {
                'label': '生日',
                'desc': '1983/09/09'
            },
            'debut': {
                'label': '初出場',
                'desc': '2011/03/20'
            },
            'nationality': {
                'label': '國籍/出生地',
                'desc': '中華民國'
            },
            'original_name': {
                'label': '原名',
                'desc': ''
            },
            'draft': {
                'label': '選秀順位',
                'desc': '兄弟象2010年第四輪'
            }
        }
    }
}
```

還有其他沒有寫在這份文件裡的功能，完整使用文件待更新

## 球隊、球員及比賽代碼

本工具使用之球隊、球員及比賽代碼來自中華職棒官網。

### 球隊代碼

```python
{
    'ACN': '中信兄弟',
    'ADD': '統一7-ELEVEn獅',
    'AJL': '樂天桃猿',
    'AEO': '富邦悍將',
    'AAA': '味全龍'
}
```

另有其他已轉賣、解散之球隊代碼未紀錄於此文件

### 球員代碼

每個球員都有一個長度為10的代碼，可以使用 `CPBL.get_player_list()` 取得

### 比賽類型代碼

中華職棒官網根據比賽類型將比賽分為7種類型，代號如下：

```python
{
    'A': '一軍例行賽',
    'B': '一軍明星賽',
    'C': '一軍總冠軍賽',
    'D': '二軍例行賽',
    'E': '一軍季後挑戰賽',
    'F': '軍總冠軍賽',
    'G': '一軍熱身賽'
}
```

## 注意事項

1. 大量爬取資料可能觸發反爬蟲機制，使用者自負使用責任。
2. 資料版權屬於中華職棒大聯盟，本工具僅供取得公開於網路上之資料。
