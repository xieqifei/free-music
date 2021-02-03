# -*- encoding: utf-8 -*-
'''
@file_name    :lambda_function.py
@description  :用于谷歌云函数，下载并处理音频，再上传至七牛云储存
@time         :2021/02/02 22:20:14
@author       :Qifei
@version      :1.0
'''

import base64
import requests
import youtube_dl
from qiniu import Auth

#七牛云对象储存AK和SK，以及储存桶名
access_key = ''
secret_key = ''
bucket_name = ''

#谷歌api，用于获取youtube搜索结果
google_appKey=""

q = Auth(access_key, secret_key)

def handler(request):
    musicname =  request.url.split("/")[-1]
    video_url = get_video_url_in_youtube(google_appKey,musicname)
    filename = dl_mp3(musicname,video_url)
    localpath = "/tmp"
    dl_url = uploadfile(localpath,filename)
    #遵循同源cors协议，可跨域访问
    headers = {
        'Access-Control-Allow-Origin': '*'
    }
  
    return (dl_url, 200, headers)

#将文件上传到七牛
def uploadfile(localpath,filename):
    #上传后保存的文件名
    key = filename
    #生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, key, 3600)
    url = 'https://upload-z2.qiniup.com'
    files = {'file': open(localpath+"/"+filename, 'rb')}           
    data = {'token':token,'fileName':filename,'key':key}
    response = requests.post(url, files=files, data=data)
    resp_code = set_liftime(filename)
    url="https://qn.xieqifei.com/"+filename
    return url

#设置七牛云过期时间为一天
def set_liftime(musicname):
    entry = '{}:{}'.format(bucket_name,musicname)
    EncodedEntryURI=str(base64.urlsafe_b64encode(bytes(entry, encoding = "utf8")),encoding="utf-8")
    url='rs.qbox.me/deleteAfterDays/'+EncodedEntryURI+'/1'
    accessToken=q.token_of_request(url,content_type='application/x-www-form-urlencoded')
    header = {'Content-Type':'application/x-www-form-urlencoded','Authorization': "Qiniu "+accessToken}
    r=requests.post('https://'+url,header)
    return r.status_code

##下载mp3格式文件
def dl_mp3(musicname,url):
    ydl_opts = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'outtmpl': '/tmp/{}.mp3'.format(musicname),
    'quiet': False
    }   
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        # info = ydl.extract_info(url, download=False)
        filename = "{}.mp3".format(musicname)
    return filename

#调用谷歌api获取youtube搜索结果，返回匹配度最高的视频链接
def get_video_url_in_youtube(appKey,music_name):
    url = "https://youtube.googleapis.com/youtube/v3/search?q="+music_name+"&key="+appKey
    resp = requests.get(url).json()
    return "https://www.youtube.com/watch?v="+resp['items'][0]['id']['videoId']
