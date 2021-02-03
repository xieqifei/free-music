import requests
import youtube_dl
from qiniu import Auth

import subprocess
import os
# 移动ffmpeg到tmp目录，并且赋予权限,tmp是云函数的本地磁盘空间，可读可写
with open("/var/user/ffmpeg", "rb") as rf:
    with open("/tmp/ffmpeg", "wb") as wf:
        wf.write(rf.read())
subprocess.run('chmod 755 /tmp/ffmpeg', shell=True)

google_appkey = ""

#七牛对象储存
access_key = ''
secret_key = ''

def handler(environ, start_response):
    musicname =  environ['fc.request_uri'] .split("/")[-1]
    video_url = get_video_url_in_youtube(google_appkey,musicname)
    filename = dl_video(video_url)

    localpath = "/tmp"
    musicname = mp4tomp3(filename)
    dl_url = uploadfile(localpath,musicname)
    delete_local_file('/tmp/'+filename)
    delete_local_file('/tmp/'+musicname)
    html='<script language="javascript" type="text/javascript">window.location.href="'+dl_url+'";setTimeout("javascript:location.href=\''+dl_url+'\'", 5000); </script>'
    return html

def uploadfile(localpath,filename):
 
    q = Auth(access_key, secret_key)
    bucket_name = 'feibar'
    #上传后保存的文件名
    key = filename
    #生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, key, 3600)
    url = 'https://upload-z2.qiniup.com'
    files = {'file': open(localpath+"/"+filename, 'rb')}           
    data = {'token':token,'fileName':filename,'key':key}
    response = requests.post(url, files=files, data=data)
    print(response.text)
    url="https://qn.xieqifei.com/"+filename
    return url

def set_liftime():
    return 0

def dl_video(url):
    ydl_opts = {
    'format': 'best',
    'outtmpl': '/tmp/%(title)s.%(ext)s',
    }   

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        info = ydl.extract_info(url, download=False)
        filename = info['title']+'.'+info['ext']
        # filename = info['title']+".mp3"
    return filename

def get_video_url_in_youtube(appKey,music_name):
    url = "https://youtube.googleapis.com/youtube/v3/search?q="+music_name+"&key="+appKey
    resp = requests.get(url).json()
    return "https://www.youtube.com/watch?v="+resp['items'][0]['id']['videoId']

#删除本地文件
def delete_local_file(src):
    if os.path.isfile(src):
        try:
            os.remove(src)
        except:
            pass
    elif os.path.isdir(src):
        for item in os.listdir(src):
            itemsrc = os.path.join(src, item)
            delete_local_file(itemsrc)
        try:
            os.rmdir(src)
        except:
            pass

def mp4tomp3(filename):
    os.system("/tmp/ffmpeg -i /tmp/"+filename+" /tmp/"+filename.split('.')[0]+'.mp3')
    return filename.split('.')[0]+'.mp3'